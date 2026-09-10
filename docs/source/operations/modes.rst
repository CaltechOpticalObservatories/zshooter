Instrument modes
================

A mode is a named operating context. It determines which daemons must be
ready, which limits apply, which commands are permitted, and which interlocks
are active.

Modes are configuration, not code.

.. list-table::
   :header-rows: 1
   :widths: 16 34 50

   * - Mode
     - Purpose
     - Characteristics
   * - ``science``
     - Nominal observing
     - Observing limits. The sequencer drives. Lamps interlocked off.
       All daemons required for the selected channels must be ``ready``.
   * - ``acquisition``
     - Target acquisition and centring
     - Observing limits. Telescope offsets permitted. Short exposures.
       Transitions to ``science`` on acquisition.
   * - ``calibration``
     - Arcs, flats, darks
     - Front-end selector in a calibration position. Lamps permitted.
       Telescope motion not required. Runs during the day as well as at
       night.
   * - ``engineering``
     - Hard hat operation
     - Engineering limits. Direct device addressing. Announced to observers.
       Refused while a sequence is running.
   * - ``maintenance``
     - Servicing, warm-up, pump-down
     - Motion may be inhibited entirely. Thermal and vacuum operations
       permitted that no other mode allows. Detector power-down permitted.
   * - ``safe``
     - Commanded safe state
     - All daemons in their safe states. Only ``recover`` and reads accepted.

Selecting a mode
----------------

Mode is instrument-wide and held by ``zsseq_obs``, with two qualifications:

- ``engineering`` is held **per subsystem**. One arm can be under engineering
  control while the rest of the instrument remains in ``science``: but the
  observer GUI announces it, and the sequencer will not include that subsystem
  in a science sequence.
- ``safe`` is reachable from any mode and is never refused.

Transitions
-----------

.. mermaid::

   stateDiagram-v2
       [*] --> safe: boot
       safe --> calibration: recover + configure
       safe --> acquisition
       calibration --> acquisition
       acquisition --> science: target acquired
       science --> acquisition: next target
       science --> calibration: calibration set
       acquisition --> engineering: sequence stopped
       calibration --> engineering
       science --> engineering: sequence stopped
       engineering --> calibration: exit hard hat
       engineering --> maintenance
       maintenance --> engineering
       science --> safe: fault / commanded
       acquisition --> safe
       calibration --> safe
       engineering --> safe
       maintenance --> safe

Entering ``engineering`` from ``science`` requires the running sequence to be
stopped first; the sequencer does not silently yield the instrument.

Leaving ``engineering`` does not return the instrument to ``ready``. Readiness
is re-established and re-observed, because the mechanism state after an
engineering session is not assumed.

Required daemons per mode
-------------------------

Each mode declares in configuration which daemons must be ``ready``. This is
what allows partial operation: a NIR spectrograph that is warm does not
prevent a VIS-only programme, and neither prevents imaging.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Mode
     - Required
   * - ``science``
     - ``zsseq_obs``, ``zskeck_tcs``, ``zsfe_selector``, and the motion and
       detector daemons of every selected assembly, plus ``zshouse_cryo``,
       ``zshouse_thermal``, and ``zshouse_vacuum`` when the NIR
       spectrograph is in use.
   * - ``acquisition``
     - As ``science``, plus ``zskeck_acq``. Acquisition itself is performed
       by MAGIQ, which ZShooter waits on rather than drives.
   * - ``calibration``
     - ``zsseq_obs``, ``zsfe_cal``, ``zsfe_selector``, and the motion and
       detector daemons of every selected assembly. Not ``zskeck_tcs``.
   * - ``engineering``
     - Only the daemons being worked on.
   * - ``maintenance``
     - ``zshouse_vacuum``, ``zshouse_thermal``, ``zshouse_cryo``,
       ``zshouse_glycol``, and ``zshouse_power``.

.. note:: **TBC: observing modes**

   The instrument's *scientific* observing modes (which channel combinations,
   slit widths, and readout modes are supported, and which are simultaneous)
   come from the L1/L2 requirements and are not yet captured here. They will
   determine the observing-configuration vocabulary the observer GUI presents
   and the required-daemon sets above.
