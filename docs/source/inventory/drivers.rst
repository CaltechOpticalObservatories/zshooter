Driver inventory
================

A driver is a library that speaks one vendor's protocol. It is imported by the
daemon that owns the hardware, has no message-bus presence, and makes no
instrument-level safety decisions.

Most of what ZShooter needs already exists as COO packages, shared with HISPEC
and other instruments. Reusing them is the default; writing a new one is the
exception that needs justifying.

Base class
----------

All ZShooter drivers derive from
`hardware_device_base <https://github.com/COO-Utilities/hardware_device_base>`_,
which fixes the shape every driver presents to its daemon:

- ``connect(host, port)`` / ``disconnect()`` / ``is_connected()``
- ``_send_command()`` / ``_read_reply()``
- ``get_atomic_value(item)``
- console and optional file logging

A daemon can therefore handle connection, reconnection, and connection-loss
detection identically whatever it is talking to.

Existing drivers
----------------

.. list-table::
   :header-rows: 1
   :widths: 18 26 26 30

   * - Driver
     - Hardware
     - Device protocol
     - Used by
   * - ``coo-ethercat``
     - Maxon EPOS4 motion controllers on an EtherCAT bus
     - EtherCAT (``pysoem`` soft master, dedicated NIC)
     - all ``*_motion`` daemons, ``zsfe_selector``
   * - ``lakeshore``
     - Lakeshore 224 / 336 temperature controllers
     - Ethernet, ASCII
     - ``zshouse_thermal``
   * - ``sunpower``
     - Sunpower CryoTel cryocoolers
     - Serial
     - ``zshouse_cryo`` (detector dewars)
   * - ``inficon``
     - Inficon vacuum gauges
     - Serial / terminal server
     - ``zshouse_vacuum``
   * - ``gammavac``
     - Gamma Vacuum SPCe ion pump controllers
     - Serial over terminal server
     - ``zshouse_vacuum``
   * - ``pdu``
     - Eaton EMAT-08 / EMAT-10 power distribution units
     - TCP ASCII, CRLF framed
     - ``zshouse_power``, ``zsfe_cal``
   * - ``onewire``
     - EDS OW-SERVER environmental sensors
     - HTTP, async
     - ``zshouse_env``
   * - ``newport``
     - Newport motion controllers
     - Ethernet / serial
     - any mechanism not on EtherCAT
   * - ``pi``
     - Physik Instrumente stages and piezo controllers
     - Ethernet / serial (PIPython)
     - fine positioning, if required
   * - ``thorlabs``
     - Thorlabs stages, flippers, filter wheels
     - USB / serial
     - ``zsfe_selector`` and ``zsimg_motion``, if any axis is Thorlabs
   * - ``srs``
     - Stanford Research Systems instruments
     - Serial / GPIB
     - ``zsfe_cal`` modulation, if required
   * - ``camera-interface``
     - Archon and ARC/Leach detector controllers, including the VIS qCCDs
     - Vendor API (C++, with ARC PCIe driver)
     - ``zscam_vis``. qCCD support is being added to ``camera-interface``
       because the qCCD is read out through an Archon controller.

Also available from the COO driver set and not currently mapped to a ZShooter
need: ``standa``, ``xeryon``, ``ozoptics``, ``hispec-fiber-switcher``.

Drivers to be written
---------------------

.. list-table::
   :header-rows: 1
   :widths: 18 34 48

   * - Driver
     - Hardware
     - Notes
   * - ``cryomech``
     - Cryomech pulse-tube compressor
     - Serial or Ethernet SMDP protocol. Read state, power, pressures, and
       fault codes; command on and off. No COO driver exists.
   * - ``ups``
     - Networked UPS
     - Almost certainly SNMP. Model not yet selected; the driver is thin and
       can wait for the hardware decision.
   * - ``lmapd``
     - Leonardo HgCdTe LmAPD arrays (Ike Pono / IBEX)
     - Nondestructive readout over 16 parallel channels, up-the-ramp
       sampling. Larger 2048 arrays announced for 2027, so the specific
       device is not yet fixed.
   * - ``qcmos``
     - Hamamatsu ORCA-Quest 2 qCMOS imager cameras
     - Vendor SDK. Needs full-frame and millisecond sub-array modes and
       hardware synchronisation across three cameras. A successor device is
       expected during the design phase and final selection follows its
       characterisation.
   * - ``glycol``
     - Facility glycol cooling interface
     - Protocol unknown; depends on what WMKO exposes at the platform.
   * - ``epics``
     - Keck 1 TCS and other WMKO EPICS services
     - EPICS Channel Access client. The Keck 1 TCS is owned and operated by
       WMKO and lives in an EPICS domain, so this driver is a client of
       observatory services rather than an interface to hardware COO controls.
       See the gateway note below.

Selection rules
---------------

- **Reuse before writing.** A driver that already exists and is in service on
  another COO instrument has been debugged at 3 a.m. by someone. A new one has
  not.
- **One driver per protocol, not per instrument.** If ZShooter needs a device
  another instrument already drives, extend the shared driver rather than
  forking it.
- **Drivers stay dumb.** No instrument state, no limit checking beyond what the
  device itself imposes, no message bus. A driver that knows it is part of
  ZShooter has a design error.
- **Every driver simulates.** A simulation implementation of the same API is
  part of the driver, not an afterthought in the daemon. See
  :doc:`../development/testing`.
- **Drivers are submodules.** Shared drivers are consumed as git submodules
  under ``src/zshooter/driver/``, pinned to a reviewed revision, following
  HISPEC's arrangement.

.. note:: **TBC: motion controller selection**

   The mapping of mechanisms to controllers assumes EtherCAT/EPOS4 throughout,
   following COO's current practice. Any mechanism using a different controller
   changes both its driver and, because daemons are drawn at ownership
   boundaries, potentially the daemon inventory in :doc:`daemons`. This should
   be settled against the electronics design before scaffolding is generated.

.. note:: **TBC: Keck EPICS interface**

   The specific EPICS process variables ZShooter needs from the Keck 1 TCS,
   and the commands it is permitted to write, must be agreed with WMKO. So must
   the Channel Access client library (``pyepics`` and ``caproto`` are the
   usual choices) and whether ZShooter connects to Channel Access directly or
   through a WMKO-provided access layer.

   Until that is settled, ``zskeck_tcs`` is specified by its role rather than its
   implementation: own the EPICS connection, translate telescope state into
   ZShooter keywords, and forward permitted commands the other way. That role
   is stable regardless of how the link is made. See
   :doc:`../architecture/gateways`.
