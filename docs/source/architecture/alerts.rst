Alerts and errors
=================

An instrument generates a great deal of information about things that are not
right. Most of it does not need anyone to do anything. A small amount needs
someone to act now.

An alert system exists to keep those two categories apart. When it fails, it
fails in one of two ways: operators are flooded and learn to ignore the
message pane, or something important is reported in a way nobody notices. Both
are worse than no alert system, because both create false confidence.

Errors and alerts are different things
--------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 12 44 44

   * -
     - Error
     - Alert
   * - **Is**
     - The outcome of one operation.
     - A condition the instrument is in.
   * - **Scope**
     - One command, one transaction.
     - The instrument or a subsystem.
   * - **Lifetime**
     - Instantaneous. It happened.
     - Persists until it is resolved or acknowledged.
   * - **Audience**
     - The client that issued the command.
     - Everyone operating the instrument.
   * - **Example**
     - "Move rejected: 11.0 exceeds softmax 10.0."
     - "Blue cryostat pressure above interlock threshold."
   * - **Carried by**
     - Command response, correlated by ``transid``.
     - Retained alert topic.

A rejected command is an error. It is returned to whoever asked, logged, and
finished. It does not raise an alert, because nothing is wrong with the
instrument: a client asked for something invalid and was told so.

A cryostat warming up is an alert. No command failed. Nobody asked for
anything. The condition exists whether or not anyone is currently issuing
commands, and it persists until someone deals with it.

Confusing the two produces the classic failure: a hundred rejected commands
from a GUI with a stuck spinbox raise a hundred alerts, and the real alert
underneath is lost.

Errors
------

Every error is structured. An error that is only a string cannot be handled,
counted, or filtered.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Meaning
   * - ``transid``
     - The command this error belongs to.
   * - ``category``
     - What kind of failure. See below.
   * - ``code``
     - Stable, specific identifier. Never renumbered.
   * - ``message``
     - Human-readable, specific, and safe to show an observer verbatim.
   * - ``detail``
     - Structured context: the value, the limit, the blocking condition, the
       driver's own error code.
   * - ``recoverable``
     - Whether retrying could succeed, or whether something must change first.

Categories
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 22 46 32

   * - Category
     - Meaning
     - Who fixes it
   * - ``invalid``
     - Malformed or out of range request.
     - The client.
   * - ``limit``
     - Valid request outside the active envelope.
     - The client, or configuration.
   * - ``state``
     - Not permitted in the daemon's current state.
     - Wait, or change mode.
   * - ``authority``
     - Requester lacks the required role.
     - Acquire authority.
   * - ``ownership``
     - Device held by another client or sequence.
     - Wait, or take ownership.
   * - ``interlock``
     - Blocked by a cross-device condition.
     - Resolve the named condition.
   * - ``device``
     - The hardware failed or refused.
     - Engineering.
   * - ``communication``
     - The device or external domain is unreachable.
     - Engineering.
   * - ``timeout``
     - Accepted, started, did not complete in time.
     - Engineering.
   * - ``internal``
     - A defect in the ICS.
     - The software team.

Categories exist so that a client can respond without parsing prose. A GUI
offers "retry" for ``timeout`` and not for ``limit``; the sequencer stops on
``device`` and waits on ``ownership``.

Message quality
~~~~~~~~~~~~~~~

Error messages are read at three in the morning by someone who did not write
the software.

.. code-block:: text

   Bad:   Command failed
   Bad:   Error -17 in move()
   Bad:   Invalid parameter

   Good:  Slit width 11.0 arcsec exceeds the observing limit of 10.0 arcsec.
   Good:  Lamp enable refused: calibration lightpath is disengaged.
   Good:  Focus move timed out after 45 s at 3.2 mm, target 8.0 mm.

A good message says what was refused, why, and what the constraint was. GUIs
display the daemon's message rather than substituting their own, because the
daemon knows the specifics and the GUI does not.

Alerts
------

An alert has an identity, a severity, a lifecycle, and an owner.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Meaning
   * - ``key``
     - Stable identifier for the *condition*, not the occurrence. The same
       condition recurring reuses the same key.
   * - ``severity``
     - ``info``, ``warning``, ``error``, ``critical``.
   * - ``source``
     - The daemon that raised it.
   * - ``summary``
     - One line, specific.
   * - ``detail``
     - Values, thresholds, and the state that produced it.
   * - ``raised`` / ``updated`` / ``cleared``
     - Lifecycle timestamps.
   * - ``count``
     - How many times this condition has recurred.
   * - ``acknowledged``
     - Whether an operator has taken responsibility for it.
   * - ``action``
     - What the operator is expected to do.

Severity
~~~~~~~~

Severity describes required response, not how alarming the condition sounds.

.. list-table::
   :header-rows: 1
   :widths: 16 40 44

   * - Severity
     - Meaning
     - Response
   * - ``info``
     - Notable, no action.
     - Recorded. Not displayed prominently.
   * - ``warning``
     - Degraded or trending wrong. Observing continues.
     - Visible. Look at it when convenient.
   * - ``error``
     - Something is not working. Observing is affected.
     - Visible and persistent. Act this hour.
   * - ``critical``
     - Hardware is at risk, or the instrument is unsafe.
     - Unmissable. Act now.

``critical`` is reserved for conditions that risk damage: vacuum loss with a
cold detector, a cryocooler failure, a thermal runaway, a mechanism driving
into a hard limit. If ``critical`` is used for anything that can wait until
morning, it stops meaning "now".

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

Two properties matter, and both follow from alerts being keyed on the
condition:

**Self-clearing.** An alert clears when its condition resolves, without an
operator dismissing it. A cryostat that comes back into range clears its own
alert. Alerts that must be manually dismissed accumulate, and an operator
clicking through a backlog is not reading them.

**Acknowledgement is not resolution.** Acknowledging says a human has seen it
and taken responsibility. The condition is still true and the alert is still
active. This distinction is what lets an operator work through a known problem
without the display pretending it is fixed.

Deduplication
~~~~~~~~~~~~~

A condition that recurs updates its existing alert and increments ``count``. It
does not create a new one. A flapping sensor produces one alert with a high
count, which is both accurate and readable, rather than four hundred alerts.

Rate limiting is a consequence of keying, not a separate mechanism bolted on
afterwards.

Ownership and delivery
----------------------

**The daemon that detects the condition raises the alert.** Alerts are not
inferred by a GUI from displayed values, because then they exist only while
that GUI is open.

Alerts are broadcast on retained topics, per :doc:`broadcast`. Retention is
what makes an alert survive a client restart: a GUI that starts at midnight
sees every active alert immediately, not just those raised after it connected.

The aggregated active alert set is published by the sequencer alongside
instrument state, so that "is anything wrong" has a single answer rather than
requiring a poll of every daemon.

Presentation
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Surface
     - Shows
   * - Observer GUI
     - Active ``warning`` and above, in operator terms, with the action.
       ``critical`` is unmissable and cannot be dismissed while active.
   * - Hard hat GUI
     - Every alert at every severity, with full detail, source daemon, and the
       telemetry that produced it.
   * - CLI
     - Active alerts as a keyword query, so scripts and the night log can read
       them.
   * - Night log
     - Every alert transition, permanently.

Escalation
~~~~~~~~~~

Some conditions cannot wait for someone to be looking at a screen: a cryostat
warming with the instrument unattended during the day, or a vacuum excursion
overnight between runs.

.. note:: **TBC: out-of-band escalation**

   Whether ``critical`` alerts escalate beyond the GUIs, and how, is not
   settled. The options range from an on-call notification path to integration
   with WMKO's own operations alerting. It depends on who is responsible for
   the instrument outside observing hours, which is an operations question
   rather than a software one.

Design rules
------------

**Every alert has an action.** If there is nothing anyone can do, it is
telemetry or an event, not an alert. An alert whose action is "be aware of
this" trains people to skip alerts.

**Alerts are conditions, errors are outcomes.** A failed command does not raise
an alert. A pattern of failed commands might, raised deliberately by the daemon
that noticed the pattern.

**Alerts describe the instrument, not the software.** "Blue cryostat pressure
above threshold" is an alert. "Exception in publish loop" is a log entry with a
bug behind it.

**Severity is about response, not tone.**

**Never alert on something you can fix.** A daemon that can reconnect should
reconnect and, at most, log it. Alert when the automatic response has been
exhausted.

**Test alerts like any other behaviour.** Every interlock and every fault path
asserts the alert it raises, its severity, and that it clears when the
condition resolves. Fault injection covers this, per
:doc:`../development/testing`.
