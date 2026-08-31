Logging, telemetry, and events
==============================

Three distinct streams
----------------------

.. list-table::
   :header-rows: 1
   :widths: 18 30 52

   * - Stream
     - Answers
     - Retention
   * - **Command log**
     - What was commanded, by whom, and what happened?
     - Permanent. This is the audit record.
   * - **Telemetry**
     - What were the instrument's physical conditions over time?
     - Long-term, downsampled. Feeds trending and diagnosis.
   * - **Events**
     - What notable things happened, and when?
     - Permanent. Faults, mode changes, state transitions.

All three carry the ``transid`` of the originating command where one exists, so
a fault can be traced back to the command that provoked it.

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
     - Peer identity, resolved role, and the human operator where known.
   * - ``target``
     - Target daemon.
   * - ``key``
     - Keyword commanded.
   * - ``payload``
     - Parameters as sent.
   * - ``accepted``
     - Accepted or rejected.
   * - ``reason``
     - Rejection reason, or empty.
   * - ``start`` / ``end`` / ``duration``
     - Execution timing.
   * - ``final_status``
     - ``completed``, ``failed``, or ``cancelled``.
   * - ``result``
     - Result payload.
   * - ``error_code`` / ``error_message``
     - On failure.
   * - ``sequence_id`` / ``observation_id``
     - Where the command belongs to a sequence or an observation.
   * - ``mode``
     - Instrument mode at the time, including whether hard hat mode was
       active.

The test of this log is a specific one: given a report that "the slit moved to
the wrong place last Tuesday", it must be possible to determine what was
commanded, by which client, under which authority, against which configured
limits, and what the mechanism actually reported.

Telemetry
---------

Every daemon publishes telemetry on a fixed cadence, independent of commands
and independent of whether anyone is listening. Cadence is configured per
keyword class:

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
     - 0.017 Hz (1 min)
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

Events mark notable discrete occurrences: fault raised, fault cleared, mode
change, hard hat entry and exit, sequence start and end, daemon start and stop,
configuration change, interlock trip. Each carries a severity
(``info`` / ``warning`` / ``error`` / ``critical``), the originating peer, and
the correlating ``transid`` where one applies.

The observer GUI's message pane and the night log are both views onto this
stream. They are not separate mechanisms with their own state.

FITS headers
------------

Detector daemons assemble FITS headers from published keyword state at the
moment of exposure, not from values cached at configuration time. Header
content is driven by keyword metadata (``description`` supplies the comment and
``units`` supplies the unit), so that a keyword and its header entry cannot
drift apart.

Every mechanism position, temperature, and instrument mode that could affect
data interpretation belongs in the header. A value that is expensive to
reconstruct later is cheap to record now.

.. note:: **TBC: header keyword mapping**

   The mapping from instrument keywords to FITS header cards, and the required
   header content for each channel, must be agreed with the data reduction
   pipeline team. This is an interface between the ICS and downstream systems
   and should be specified as one.
