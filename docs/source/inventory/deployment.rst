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
     - ``*_motion``, ``zsimg_adc``, ``zscal_lightpath``
     - Needs a dedicated NIC per EtherCAT bus. EtherCAT traffic cannot share
       an interface with normal networking.
   * - Detector host
     - ``zscam_*``
     - Needs the detector controller interface hardware (PCIe for ARC, a
       dedicated high-throughput link for Archon) and local fast storage for
       frames.
   * - Housekeeping host
     - ``zshk_*``, ``zsnir_thermal``, ``*_cryo``, ``zscal_lamps``
     - Must keep running when observing stops. Thermal and vacuum monitoring
       are daytime and maintenance functions as much as night ones.
   * - Control host
     - ``zsseq_obs``, ``zskeck_tcs``, GUIs, VNC
     - Needs the observatory network and the TCS.

.. note:: **TBC: host allocation**

   This grouping is by constraint, not by a decided machine count. The actual
   allocation depends on the EtherCAT bus topology and the detector controller
   choice.

Startup
-------

All daemons start automatically at boot under systemd, with units in
``init.d/``. Ordering is by dependency, not by convenience:

1. **Infrastructure**: message transport (broker, if RabbitMQ is chosen).
2. **Housekeeping**: ``zshk_power`` first, since other daemons may need their
   hardware powered; then ``zshk_vacuum``, ``zshk_temp``, ``zshk_env``.
3. **Thermal and cryogenic**: cooling should be under control before anything
   else is attempted, and long before a detector is expected to be cold.
4. **Device daemons**: motion, calibration, detectors.
5. **Coordination**: ``zskeck_tcs``, then ``zsseq_obs``.
6. **Watchdog**: ``zshk_watchdog`` last, so it does not report expected
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
