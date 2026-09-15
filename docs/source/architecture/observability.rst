Errors, alerts, and logging
===========================

Everything the ICS reports about itself falls into four streams. They differ in
what they answer and in what a consumer is expected to do about them.

.. list-table::
   :header-rows: 1
   :widths: 16 40 22 22

   * - Stream
     - Answers
     - Delivered by
     - Retention
   * - **Error**
     - Did this command work, and if not, why?
     - Command response
     - Command log
   * - **Alert**
     - Is something wrong with the instrument right now?
     - Retained topic
     - Until cleared
   * - **Telemetry**
     - What were the physical conditions over time?
     - Periodic publication
     - Time series
   * - **Event**
     - What notable things happened, and when?
     - Topic
     - Log

Everything carries the ``transid`` of the originating command where one
exists, so a fault can be traced back to the command that provoked it.

Errors
------

An error is the outcome of one command. It is returned to whoever issued it,
recorded, and finished.

Every error is structured. An error that is only a string cannot be handled,
counted, or filtered.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Meaning
   * - ``category``
     - What kind of failure. See below.
   * - ``message``
     - Human-readable, specific, safe to show verbatim.
   * - ``detail``
     - Structured context: the value, the limit, the blocking condition, the
       driver's own error code.

.. list-table::
   :header-rows: 1
   :widths: 20 44 36

   * - Category
     - Meaning
     - Fixed by
   * - ``invalid``
     - Malformed request.
     - The client.
   * - ``limit``
     - Valid request outside the active envelope.
     - The client, or configuration.
   * - ``state``
     - Not permitted in the daemon's current state, including while it is
       busy.
     - Wait, or change mode.
   * - ``interlock``
     - Blocked by a cross-device condition.
     - Resolve the named condition.
   * - ``device``
     - The hardware failed or refused.
     - Engineering.
   * - ``timeout``
     - Started and did not complete in time.
     - Engineering.
   * - ``internal``
     - A defect in the ICS.
     - The software team.

Categories exist so a client can respond without parsing prose. A GUI offers
"retry" for ``timeout`` and not for ``limit``; the sequencer stops on
``device`` and waits on ``state``.

Message quality
~~~~~~~~~~~~~~~

Error messages are read at three in the morning by someone who did not write
the software.

.. code-block:: text

   Bad:   Command failed
   Bad:   Error -17 in move()

   Good:  Slit width 11.0 arcsec exceeds the observing limit of 10.0 arcsec.
   Good:  Lamp enable refused: front-end selector is not set to calibration.
   Good:  Focus move timed out after 45 s at 3.2 mm, target 8.0 mm.

A good message says what was refused, why, and what the constraint was. GUIs
display the daemon's message rather than substituting their own, because the
daemon knows the specifics and the GUI does not.

Alerts
------

An alert is a condition the instrument is **in**, not the outcome of a
command. It persists until it is resolved.

.. code-block:: text

   Error:  "Slit move rejected: 11.0 exceeds softmax 10.0."
           A client asked for something invalid and was told so.
           Nothing is wrong with the instrument.

   Alert:  "NIR cryostat pressure above interlock threshold."
           No command failed. Nobody asked for anything.
           The condition exists until someone deals with it.

Keeping these apart is the whole point of the alert system. If failed commands
raised alerts, a GUI with a stuck spinbox would bury the real alert underneath
a hundred false ones, and operators would learn to ignore the pane.

Fields
~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Meaning
   * - ``key``
     - Stable identifier for the *condition*, not the occurrence. A condition
       that recurs reuses its key.
   * - ``severity``
     - ``info``, ``warning``, ``error``, ``critical``.
   * - ``source``
     - The daemon that raised it.
   * - ``summary``
     - One line, specific.
   * - ``action``
     - What the operator is expected to do.
   * - ``raised`` / ``cleared``
     - Lifecycle timestamps.
   * - ``count``
     - How many times the condition has recurred.
   * - ``acknowledged``
     - Whether an operator has taken responsibility for it.

Severity
~~~~~~~~

Severity describes the required response, not how alarming the condition
sounds.

.. list-table::
   :header-rows: 1
   :widths: 16 40 44

   * - Severity
     - Meaning
     - Response
   * - ``info``
     - Notable, no action.
     - Recorded, not displayed prominently.
   * - ``warning``
     - Degraded or trending wrong. Observing continues.
     - Look at it when convenient.
   * - ``error``
     - Something is not working. Observing is affected.
     - Act this hour.
   * - ``critical``
     - Hardware is at risk, or the instrument is unsafe.
     - Act now.

``critical`` is reserved for conditions that risk damage: vacuum loss with a
cold detector, a cryocooler failure, a thermal runaway, a mechanism driving
into a hard limit. If it is used for anything that can wait until morning, it
stops meaning "now".

Lifecycle
~~~~~~~~~

.. mermaid::

   stateDiagram-v2
       [*] --> raised: condition detected
       raised --> acknowledged: operator takes responsibility
       raised --> cleared: condition resolved
       acknowledged --> cleared: condition resolved
       cleared --> raised: recurs (same key, count++)
       cleared --> [*]

Two properties follow from alerts being keyed on the condition rather than the
occurrence:

**They clear themselves.** A cryostat that comes back into range clears its own
alert; no operator dismisses it. Alerts that must be manually dismissed
accumulate, and an operator clicking through a backlog is not reading it.

**Acknowledgement is not resolution.** Acknowledging records that a human has
seen it and taken responsibility. The condition is still true and the alert is
still active. This is what lets an operator work through a known problem
without the display pretending it is fixed.

Recurrence updates the existing alert and increments ``count`` rather than
creating a new one, so a flapping sensor produces one alert with a high count
instead of four hundred alerts. Rate limiting falls out of keying rather than
being a separate mechanism.

Where alerts appear
~~~~~~~~~~~~~~~~~~~

The daemon that detects the condition raises the alert. Alerts are never
inferred by a GUI from displayed values, because then they would exist only
while that GUI is open.

Alerts are broadcast on retained topics, so a GUI starting at midnight sees
every active alert immediately rather than only those raised after it
connected. The sequencer publishes the aggregated active set alongside
instrument state, so "is anything wrong" has one answer.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Surface
     - Shows
   * - Observer GUI
     - Active ``warning`` and above, in operator terms, with the action.
       ``critical`` cannot be dismissed while active.
   * - Hard hat GUI
     - Every alert at every severity, with full detail and the telemetry that
       produced it.
   * - CLI
     - Active alerts as a keyword query, for scripts and the night log.
   * - Night log
     - Every alert transition, permanently.

Rules
~~~~~

**Every alert has an action.** If there is nothing anyone can do, it is
telemetry or an event. An alert whose action is "be aware of this" trains
people to skip alerts.

**Alerts describe the instrument, not the software.** "Blue cryostat pressure
above threshold" is an alert. "Exception in publish loop" is a log entry with
a bug behind it.

**Never alert on something you can fix.** A daemon that can reconnect should
reconnect and log it. Alert when the automatic response has been exhausted.

.. note:: **TBC: out-of-band escalation**

   Whether ``critical`` alerts escalate beyond the GUIs, and how, is not
   settled. It depends on who is responsible for the instrument outside
   observing hours, which is an operations question rather than a software
   one.

Command log
-----------

Every command produces one log record, whatever its outcome, including
rejections, which are frequently the most diagnostic records of all.

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Field
     - Notes
   * - ``transid``
     - Correlates with every message and event for this command.
   * - ``timestamp``
     - Request time, UTC.
   * - ``requester``
     - Peer identity, and the human operator where known.
   * - ``target`` / ``key``
     - Target daemon and keyword commanded.
   * - ``payload``
     - Parameters as sent.
   * - ``start`` / ``end`` / ``duration``
     - Execution timing.
   * - ``final_status``
     - ``completed``, ``rejected``, ``failed``, or ``cancelled``.
   * - ``error``
     - The error structure above, on failure.
   * - ``sequence_id`` / ``observation_id``
     - Where the command belongs to a sequence or observation.
   * - ``mode``
     - Instrument mode at the time, including whether the subsystem was in
       engineering mode.

The test of this log is a specific one: given a report that "the slit moved to
the wrong place last Tuesday", it must be possible to determine what was
commanded, by which client, against which configured limits, and what the
mechanism actually reported.

Telemetry
---------

Every daemon publishes telemetry on a fixed cadence, independent of commands
and of whether anyone is listening. Cadence is configured per keyword class:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Class
     - Cadence
     - Examples
   * - Heartbeat and daemon state
     - 1 Hz
     - ``heartbeat``, ``daemonstate``, ``isready``
   * - Mechanism position
     - 1 Hz idle, 10 Hz moving
     - stage and rotator positions
   * - Thermal and vacuum
     - 0.1 Hz
     - detector and cryostat temperatures, dewar pressure
   * - Environment and power
     - 1 min
     - ambient conditions, PDU state, UPS status
   * - Detector state
     - On change, plus 1 Hz during exposure
     - exposure progress, readout state

Telemetry is written to a time-series store for trending. Cryostat temperature
and vacuum histories in particular are the primary diagnostic when a detector
underperforms, and they are only useful if they were being recorded before
anyone suspected a problem.

Events
------

Events mark notable discrete occurrences: fault raised and cleared, mode
change, engineering mode entry and exit, sequence start and end, daemon start
and stop, configuration change, interlock trip. Each carries a severity, the
originating peer, and the correlating ``transid`` where one applies.

The observer GUI's message pane and the night log are both views onto this
stream, not separate mechanisms with their own state.

FITS headers
------------

Detector daemons assemble FITS headers from published keyword state at the
moment of exposure, not from values cached at configuration time. Header
content is driven by keyword metadata, with ``description`` supplying the
comment and ``units`` supplying the unit, so that a keyword and its header
entry cannot drift apart.

Every mechanism position, temperature, and instrument mode that could affect
data interpretation belongs in the header. A value that is expensive to
reconstruct later is cheap to record now.

.. note:: **TBC: header keyword mapping**

   The mapping from instrument keywords to FITS header cards, and the required
   header content for each channel, must be agreed with the data reduction
   pipeline team. This is an interface between the ICS and downstream systems
   and should be specified as one.
