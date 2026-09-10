Deployment
==========

Hosts
-----

Daemons are distributed across hosts by what they must be physically near and
by what they must survive.

.. list-table::
   :header-rows: 1
   :widths: 22 34 44

   * - Host class
     - Runs
     - Constraint
   * - Motion host
     - ``zsfe_selector``, ``zsimg_motion``, ``zsvis_motion``,
       ``zsnir_motion``
     - Needs a dedicated NIC per EtherCAT bus. EtherCAT traffic cannot share
       an interface with normal networking.
   * - Detector host
     - ``zscam_vis``, ``zscam_nir``, ``zscam_img``
     - Needs the readout interface hardware and local fast storage. The
       heaviest constraint in the instrument: 256-channel qCCD readout and
       millisecond full-frame qCMOS imaging are both high-bandwidth, and may
       not share a host.
   * - Housekeeping host
     - ``zshouse_*``, ``zsfe_cal``
     - Must keep running when observing stops. Thermal, vacuum, and glycol
       monitoring are daytime and maintenance functions as much as night
       ones.
   * - Control host
     - ``zsseq_obs``, ``zskeck_tcs``, ``zskeck_acq``, GUIs, VNC
     - Needs the observatory network and the WMKO EPICS domain.

.. note:: **TBC: host allocation**

   This grouping is by constraint, not by a decided machine count. The actual
   allocation depends on the EtherCAT bus topology and on the detector
   readout electronics, neither of which is designed yet.

   Detector data rates are the thing most likely to force more hosts. Three
   qCMOS cameras at millisecond cadence and three qCCDs reading 256 channels
   apiece are unlikely to share one machine comfortably, and the imager and
   the spectrographs can run independently of each other in any case.

Startup
-------

All daemons start automatically at boot under systemd, with units in
``init.d/``:

1. **Infrastructure**: message transport (broker, if RabbitMQ is chosen).
2. **Housekeeping**: ``zshouse_power`` first, since other daemons may need
   their hardware powered; then ``zshouse_vacuum``, ``zshouse_thermal``,
   ``zshouse_glycol``, and ``zshouse_env``.
3. **Thermal and cryogenic**: cooling should be under control before anything
   else is attempted, and long before a detector is expected to be cold.
4. **Device daemons**: motion, calibration, detectors.
5. **Coordination**: ``zskeck_tcs``, then ``zsseq_obs``.
6. **Watchdog**: ``zshouse_watchdog`` last, so it does not report expected
   absences during a normal boot.
7. **Interfaces**: VNC sessions and GUIs.

A daemon that cannot reach its hardware still starts and publishes
``fault`` with a reason. It does not exit. A daemon that exits is invisible;
a daemon that reports why it is unhappy is diagnosable, and the distinction
matters most during a power-up when several things are wrong at once.

Restart policy
--------------

Restart behaviour is configured per daemon, because the right answer differs:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Daemon class
     - Policy
   * - Housekeeping, thermal, cryogenic
     - Always restart. Monitoring gaps are worse than restart churn, and these
       daemons hold no motion state to lose.
   * - Motion
     - Restart, then re-read hardware state before claiming readiness. Never
       auto-home on restart: homing an unknown configuration is how mechanisms
       get damaged.
   * - Detector
     - Restart, but never during an exposure. An in-progress readout is lost
       data, and the restart must wait for the readout to finish or fail.
   * - Sequencer
     - Restart, resuming into a stopped state. Never auto-resume a sequence:
       the instrument's condition after a sequencer crash is unknown, and the
       decision to continue belongs to the operator.

Environments
------------

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Environment
     - Purpose
   * - ``sim``
     - Every daemon in simulation, no hardware, single host. Runs in CI. This
       is where GUI and sequencer development happens.
   * - ``lab``
     - Real hardware on the bench, subsystem by subsystem. Mixed real and
       simulated daemons; the mix is a deployment-layer configuration choice,
       not a code change.
   * - ``summit``
     - Full instrument at the telescope.

The three differ only in the deployment configuration layer described in
:doc:`../architecture/configuration`. The same daemon code runs in all of them.
If ``sim`` and ``summit`` need different code, the simulation is not testing
the thing that will run.
