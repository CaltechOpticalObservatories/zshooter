Daemon inventory
================

How the inventory was derived
-----------------------------

Daemons are drawn at **hardware ownership boundaries**: one daemon per
controller or fieldbus, owning every mechanism attached to it.

The reason is arbitration. Mechanisms sharing an EtherCAT bus, a Newport
controller, or a Lakeshore chassis cannot be owned by separate processes
without inventing a bus-arbiter to sit between them, which is a daemon by
another name, with the additional drawback that the safety logic and the bus
access then live in different processes. Grouping by ownership keeps each
daemon's safety reasoning and its hardware access in the same place.

This yields roughly twenty daemons rather than one per mechanism (~30) or one
per subsystem (~7). Recorded as ADR-0001 in :doc:`../decisions/index`.

.. warning:: **Provisional mapping**

   The grouping below assumes a controller topology that has not yet been
   confirmed. Where several mechanisms are shown under one daemon, that is a
   claim that they share a controller. **Each of these groupings must be
   checked against the as-built electronics design**, and daemons split or
   merged accordingly. The *rule* is settled; this *application* of it is not.

   The inventory has also not yet been reconciled against the L1/L2/L3
   requirements baseline.

Naming
------

Peer identity is ``<group>_<scope>``; keyword address is
``<group>.<scope>.<name>``; source lives in ``daemons/<group>/<scope>/``.

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Group
     - Domain
   * - ``zsimg``
     - ZImager channel
   * - ``zsnir``
     - ZSpec nIR channel
   * - ``zsblue``
     - ZSpec Blue arm
   * - ``zsred``
     - ZSpec Red arm
   * - ``zscam``
     - Detector controllers
   * - ``zscal``
     - Calibration and lightpath
   * - ``zshk``
     - Housekeeping and infrastructure
   * - ``zskeck``
     - Gateways to WMKO messaging domains
   * - ``zsseq``
     - Sequencing and coordination

Device daemons
--------------

ZImager
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsimg_motion``
     - ZImager motion bus
     - u rotator, variable rotator, z rotator, slit, focus, filter
     - ``coo-ethercat``
   * - ``zsimg_adc``
     - u-channel ADC controller
     - ADC prism pair (counter-rotating)
     - ``coo-ethercat`` or ``newport``: TBC

The ADC is shown separately because ADC prism pairs are commonly driven as a
coordinated pair with their own controller and their own dispersion solution.
If it shares the ZImager bus, merge it into ``zsimg_motion``.

ZSpec nIR
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsnir_motion``
     - nIR motion bus
     - nod, rotator, field stop, slit, focus
     - ``coo-ethercat``
   * - ``zsnir_thermal``
     - nIR Lakeshore chassis
     - Detector and bench temperature control loops, heaters
     - ``lakeshore``
   * - ``zsnir_cryo``
     - Cryomech compressor
     - Pulse-tube cooler: state, power, fault reporting
     - ``cryomech`` (new)

The nod mechanism is on the motion bus but is operationally distinct: it is
commanded inside the exposure loop rather than during configuration, so its
command timing and its interaction with detector readout need separate
treatment in the sequencer. See :doc:`../operations/workflows`.

ZSpec Blue
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsblue_motion``
     - Blue motion bus
     - ADC, rotator, slit, focus
     - ``coo-ethercat``
   * - ``zsblue_cryo``
     - Blue CryoTel cooler
     - Sunpower CryoTel: setpoint, power, state
     - ``sunpower``

ZSpec Red
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsred_motion``
     - Red motion bus
     - ADC, rotator, slit, focus
     - ``coo-ethercat``
   * - ``zsred_cryo``
     - Red CryoTel cooler
     - Sunpower CryoTel: setpoint, power, state
     - ``sunpower``

Blue and Red are structurally identical. They should share one daemon
implementation parameterised by configuration, not two near-duplicate
codebases.

Detectors
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Responsibilities
     - Driver
   * - ``zscam_blue``
     - Blue detector controller
     - Configure, expose, abort, read out, write FITS, report temperature
     - ``camera-interface``
   * - ``zscam_red``
     - Red detector controller
     - As above
     - ``camera-interface``
   * - ``zscam_nir``
     - nIR detector controller
     - As above, plus up-the-ramp / correlated-double-sampling readout modes
     - ``camera-interface``: TBC

Detector daemons are modelled separately from mechanism daemons throughout this
architecture. Their command durations, data products, failure modes, and
recovery behaviour differ enough that treating them as "just another daemon"
would distort both.

.. note:: **TBC: detector controllers**

   The controller type per channel (Archon, ARC/Leach, or a SIDECAR ASIC for
   the nIR H2RG-class device) is not fixed here. Whether one daemon can serve
   several controllers, rather than one daemon per controller, depends on that
   choice.

Calibration and lightpath
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zscal_lamps``
     - Lamp power and modulation
     - Arc and flat lamps, modulators, lamp interlocks
     - ``pdu``, ``srs``: TBC
   * - ``zscal_lightpath``
     - Lightpath selection mechanism
     - Calibration pickoff/fold, dust covers, shutters
     - ``coo-ethercat`` or ``thorlabs``: TBC

``zscal_lightpath`` holds the interlock that makes lamp operation safe: lamps
may only be enabled with the calibration path engaged. Because that couples two
daemons, ``zscal_lamps`` subscribes to lightpath state and fails closed if it
is stale or missing.

Housekeeping
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 18 28 30 24

   * - Peer
     - Owns
     - Responsibilities
     - Driver
   * - ``zshk_vacuum``
     - Gauges and ion pumps
     - Cryostat pressures, ion pump state and current
     - ``inficon``, ``gammavac``
   * - ``zshk_temp``
     - Monitor-only Lakeshore channels
     - Structure and bench temperatures for flexure and focus models
     - ``lakeshore``
   * - ``zshk_env``
     - OW-SERVER 1-Wire bus
     - Ambient temperature, humidity, dew point, pressure
     - ``onewire``
   * - ``zshk_power``
     - PDUs and UPS
     - Outlet control, power state, UPS status and battery
     - ``pdu``, ``ups`` (new)
   * - ``zshk_watchdog``
     - Nothing
     - Daemon liveness supervision, systemd interface, escalation
     - none

``zshk_watchdog`` owns no hardware. It subscribes to every daemon's heartbeat,
detects silence, publishes ``offline`` on behalf of daemons that cannot report
it themselves, and drives systemd restarts under a configured policy.

Because it must keep working when the rest of the system does not, it has the
fewest dependencies of any daemon: no drivers, no configuration beyond the
daemon list and the restart policy.

Coordination and gateway daemons
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Peer
     - Responsibilities
   * - ``zsseq_obs``
     - The observation sequencer. Executes instrument workflows, holds
       instrument-level ownership during a sequence, aggregates daemon state
       into instrument state, and manages the target list. Owns no hardware.
   * - ``zskeck_tcs``
     - Gateway to the Keck 1 telescope control system. The TCS is owned and
       operated by WMKO and lives in an EPICS domain, so this daemon is a
       translator: it holds the EPICS Channel Access connection on one side and
       is an ordinary ZShooter peer on the other. Republishes telescope
       pointing, rotator angle, airmass, parallactic angle, and hour angle;
       forwards permitted offsets.
   * - ``zskeck_magiq``
     - Gateway to MAGIQ, the WMKO acquisition and guiding system. Republishes
       acquisition and guide state so the sequencer and the GUIs can see it,
       and requests the acquisition operations ZShooter is permitted to
       request. Scope pending the functional split below.

``zskeck_tcs`` is where the ADC and rotator solutions get their inputs. Every
daemon that needs airmass, parallactic angle, or hour angle subscribes to
``zskeck.tcs.*`` rather than opening its own EPICS connection. See
:doc:`../architecture/gateways` for why translation is concentrated in one
place.

Acquisition and guiding
~~~~~~~~~~~~~~~~~~~~~~~

**Telescope acquisition and guiding is owned by Keck, under MAGIQ.** ZShooter
does not implement astrometric acquisition, offset computation, or guiding, and
no daemon in this inventory does so.

What ZShooter needs is an interface to MAGIQ, not a replacement for it:
knowing whether a target is acquired and whether guiding is locked, so the
sequencer can gate an exposure on it; surfacing that state to the observer; and
requesting whatever acquisition operations an instrument is permitted to
request.

.. note:: **TBC: MAGIQ functional split**

   The division of responsibility between ZShooter and MAGIQ must be mapped
   explicitly and agreed with WMKO. The questions to answer, each of which
   changes what ``zskeck_magiq`` does:

   - Which acquisition steps does MAGIQ perform, and which (if any) does the
     instrument initiate?
   - What acquisition and guide state does MAGIQ publish, in what domain, and
     how does ZShooter subscribe to it?
   - Can the instrument request an offset, and if so within what limits and
     under whose authority?
   - Does ZShooter contribute anything to acquisition, such as a slit-viewing
     or through-slit image, and if so what does MAGIQ expect of it?
   - What does MAGIQ provide that must reach the FITS headers?
   - What happens to a running sequence when guiding is lost?

   Until this is mapped, the acquisition workflow in
   :doc:`../operations/workflows` cannot be specified and the required-daemon
   set for ``acquisition`` mode is incomplete.

Summary
-------

.. list-table::
   :header-rows: 1
   :widths: 24 20 56

   * - Class
     - Count
     - Peers
   * - Motion
     - 5
     - ``zsimg_motion``, ``zsimg_adc``, ``zsnir_motion``,
       ``zsblue_motion``, ``zsred_motion``
   * - Thermal / cryogenic
     - 4
     - ``zsnir_thermal``, ``zsnir_cryo``, ``zsblue_cryo``, ``zsred_cryo``
   * - Detector
     - 3
     - ``zscam_blue``, ``zscam_red``, ``zscam_nir``
   * - Calibration
     - 2
     - ``zscal_lamps``, ``zscal_lightpath``
   * - Housekeeping
     - 5
     - ``zshk_vacuum``, ``zshk_temp``, ``zshk_env``, ``zshk_power``,
       ``zshk_watchdog``
   * - Coordination
     - 1
     - ``zsseq_obs``
   * - Gateway
     - 2
     - ``zskeck_tcs``, ``zskeck_magiq``
   * - **Total**
     - **22**
     -

Distinct daemon *implementations* are fewer: Blue and Red motion share one,
the two CryoTel daemons share one, and the three detector daemons share one or
two depending on the nIR controller choice. Roughly a dozen implementations
cover twenty-two deployed daemons.
