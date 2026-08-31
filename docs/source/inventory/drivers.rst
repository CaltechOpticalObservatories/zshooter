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
     - all ``*_motion`` daemons, ``zscal_lightpath``
   * - ``lakeshore``
     - Lakeshore 224 / 336 temperature controllers
     - Ethernet, ASCII
     - ``zsnir_thermal``, ``zshk_temp``
   * - ``sunpower``
     - Sunpower CryoTel cryocoolers
     - Serial
     - ``zsblue_cryo``, ``zsred_cryo``
   * - ``inficon``
     - Inficon vacuum gauges
     - Serial / terminal server
     - ``zshk_vacuum``
   * - ``gammavac``
     - Gamma Vacuum SPCe ion pump controllers
     - Serial over terminal server
     - ``zshk_vacuum``
   * - ``pdu``
     - Eaton EMAT-08 / EMAT-10 power distribution units
     - TCP ASCII, CRLF framed
     - ``zshk_power``, ``zscal_lamps``
   * - ``onewire``
     - EDS OW-SERVER environmental sensors
     - HTTP, async
     - ``zshk_env``
   * - ``newport``
     - Newport motion controllers
     - Ethernet / serial
     - ``zsimg_adc`` (if not EtherCAT)
   * - ``pi``
     - Physik Instrumente stages and piezo controllers
     - Ethernet / serial (PIPython)
     - fine positioning, if required
   * - ``thorlabs``
     - Thorlabs stages, flippers, filter wheels
     - USB / serial
     - ``zscal_lightpath`` covers and flippers
   * - ``srs``
     - Stanford Research Systems instruments
     - Serial / GPIB
     - ``zscal_lamps`` modulation, if required
   * - ``camera-interface``
     - Archon and ARC/Leach detector controllers
     - Vendor API (C++, with ARC PCIe driver)
     - all ``zscam_*`` daemons

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
  :doc:`../operations/simulation`.
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
