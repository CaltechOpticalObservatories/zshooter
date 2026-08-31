Traceability matrix
===================

.. note:: **Not yet populated**: pending ingestion of the L1/L2/L3
   requirements baseline. See :doc:`index`.

Format
------

Each row traces one requirement to the ICS artefacts that satisfy it and to the
method by which that is verified.

.. list-table::
   :header-rows: 1
   :widths: 10 8 30 24 16 12

   * - ID
     - Level
     - Requirement (abridged)
     - Satisfied by
     - Verification
     - Status
   * - ``L2-xxx``
     - L2
     - *requirement text*
     - ``zsblue_motion``, ``zsblue.motion.slitwidth``
     - Test (sim)
     - Open

``Satisfied by`` names concrete artefacts (a daemon peer, a keyword, a
workflow, an interlock, a configuration item), not prose. A trace to "the ICS"
is not a trace.

Illustrative entries
--------------------

These show the intended shape. The IDs are placeholders; the requirement text
is not quoted from the baseline.

.. list-table::
   :header-rows: 1
   :widths: 12 34 30 24

   * - Kind
     - Requirement shape
     - Satisfied by
     - Verification
   * - Mechanism
     - "The instrument shall provide a selectable slit width over *range*."
     - ``zsblue_motion``; keyword ``zsblue.motion.slitwidth`` with configured
       soft limits and named positions
     - Test (sim) for range and limit enforcement; Test (hardware) for
       accuracy
   * - Measurement
     - "Detector temperature shall be recorded throughout operation."
     - ``zsnir_thermal``; keyword ``zsnir.thermal.detectortemperature``;
       telemetry at 0.1 Hz; FITS header entry
     - Inspection of telemetry configuration; Test (sim) for publication
   * - Safety
     - "Calibration lamps shall not illuminate the telescope beam."
     - Lamp interlock in ``zscal_lamps`` conditioned on
       ``zscal.lightpath.state``, failing closed on stale state
     - Test (sim) with fault injection on the lightpath dependency
   * - Operation
     - "The instrument shall be configurable for a target without operator
       intervention."
     - ``zsseq_obs`` configure-for-target workflow
     - Test (sim) end to end; Demonstration on sky
   * - Performance
     - "Instrument reconfiguration shall complete within *t*."
     - Parallel mechanism commanding in the configure workflow; per-mechanism
       ``timeout_s``
     - Analysis of the timing budget; Test (hardware)
   * - Interface
     - "The instrument shall record telescope pointing with each exposure."
     - ``zskeck_tcs`` publication; header assembly in ``zscam_*``
     - Test (sim); Inspection of written headers

Maintenance
-----------

The matrix is generated from a single source of requirement records held in the
repository, not maintained by hand in this document. A hand-maintained matrix
is out of date within a month of being written, and a matrix that is out of
date is worse than none, because it is trusted.

Coverage (requirements with no satisfying artefact, and artefacts tracing to no
requirement) should be reported by the same tooling that generates the
matrix, so that both gaps surface automatically rather than at review.
