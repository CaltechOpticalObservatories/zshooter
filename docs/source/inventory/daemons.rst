Daemon inventory
================

How the inventory was derived
-----------------------------

Two things shape it.

**The instrument is four assemblies.** The front-end, the imager, the VIS
spectrograph, and the NIR spectrograph are separately supported, separately
alignable, and separately removable for servicing. The ICS follows that
division, so that a subsystem can be worked on, tested, and brought up on the
bench without the rest of the instrument.

**Daemons are drawn at hardware ownership boundaries**: one daemon per
controller or fieldbus, owning every mechanism attached to it. Mechanisms
sharing an EtherCAT bus or a Lakeshore chassis cannot be owned by separate
processes without a bus arbiter, which is a daemon by another name and one
that separates safety logic from hardware access. Recorded as ADR-0001 in
:doc:`../decisions/index`.

The instrument has **33 controlled motion axes** and **11 detector systems**.
Grouping by ownership gives 18 daemons.

Naming
------

Peer identity is ``<group>_<scope>``; keyword address is
``<group>.<scope>.<name>``; source lives in ``daemons/<group>/<scope>/``.

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Group
     - Domain
   * - ``zsfe``
     - Front-end: beam routing and calibration sources
   * - ``zsimg``
     - Imager mechanisms
   * - ``zsvis``
     - VIS spectrograph mechanisms
   * - ``zsnir``
     - NIR spectrograph mechanisms
   * - ``zscam``
     - Detector readout services
   * - ``zshouse``
     - Housekeeping and infrastructure
   * - ``zskeck``
     - Gateways to WMKO domains
   * - ``zsseq``
     - Sequencing and coordination

Front-end
---------

.. list-table::
   :header-rows: 1
   :widths: 18 24 34 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsfe_selector``
     - Front-end selector bus
     - Mirror selector mechanisms: full field to the imager, apertured
       fold-flat passing the central 30" to the spectrographs, and 60 degree
       routing to platform neighbours
     - ``coo-ethercat``
   * - ``zsfe_cal``
     - Calibration sources
     - Integrating sphere, emission-line lamps, continuum sources, and any
       mechanism that deploys them
     - ``pdu``, vendor lamp control

The front-end decides what light goes where, which makes ``zsfe_selector``
the most operationally significant mechanism daemon in the instrument. Its
state determines whether the spectrographs are receiving light at all, so the
sequencer and both GUIs gate on it and every calibration interlock is
conditioned on it.

Calibration belongs to the front-end rather than to a separate assembly
because the integrating sphere feeds the same beam path the selector
controls. That adjacency is what lets the imager and the spectrographs be
co-calibrated against one common source.

Imager
------

.. list-table::
   :header-rows: 1
   :widths: 18 24 34 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsimg_motion``
     - Imager motion bus
     - Common refractive ADC, selectable filter in the middle channel, three
       rotating detector assemblies
     - ``coo-ethercat``

The ``u`` and ``z`` channels carry fixed broadband filters and have no filter
mechanism. Only the middle channel is selectable.

The three detector rotators are separate axes but are commanded together: the
channels are co-aligned, and a differential rotation between them is a fault
rather than a configuration.

Spectrographs
-------------

The two spectrographs are optically and mechanically parallel. Each has the
same five mechanism types in its pre-optics, and the arms downstream are
fixed-format with no moving parts at all.

.. list-table::
   :header-rows: 1
   :widths: 18 24 34 24

   * - Peer
     - Owns
     - Mechanisms
     - Driver
   * - ``zsvis_motion``
     - VIS pre-optics bus
     - Slit, tip/tilt, focus, ADC, K-mirror
     - ``coo-ethercat``
   * - ``zsnir_motion``
     - NIR pre-optics bus
     - Slit, tip/tilt, focus, ADC, K-mirror, all cryogenic
     - ``coo-ethercat``

These should share one daemon implementation parameterised by configuration.

.. list-table::
   :header-rows: 1
   :widths: 16 84

   * - Mechanism
     - Notes
   * - Slit
     - 10" long, discrete selectable widths spanning roughly 0.3" to 1.0".
       Discrete rather than continuous, so it is a selector with named
       positions rather than a positioner with a range.
   * - Tip/tilt
     - Slit-plane alignment. Two axes.
   * - Focus
     - Pre-optics focus.
   * - ADC
     - A pair of counter-rotating Amici prisms. Two axes driven as a
       coordinated pair from a dispersion solution rather than positioned
       independently. Needs airmass and parallactic angle from
       ``zskeck.tcs``.
   * - K-mirror
     - Field de-rotation, counter-rotating the diurnal sky motion to hold the
       target fixed on the slit. Needs telescope state from ``zskeck.tcs``
       and runs continuously during an exposure rather than being positioned
       once.

The K-mirror and the ADC are the only mechanisms that track during an
observation. Everything else is positioned during configuration and then
held.

Detectors
---------

.. list-table::
   :header-rows: 1
   :widths: 18 20 30 32

   * - Peer
     - Owns
     - Detectors
     - Notes
   * - ``zscam_vis``
     - VIS Archon controller
     - B, G, R qCCDs, 4096x2048, 15 micron
     - Read out through an Archon, so it uses ``camera-interface``.
       Multi-Video Processor electronics give 256 readout channels per
       device. Frame store, so a new exposure starts while the previous
       reads out. Readout about 2 minutes.
   * - ``zscam_nir``
     - NIR readout electronics
     - YJ, H, K HgCdTe LmAPD, 2048x2048
     - Nondestructive readout, 16 parallel channels, up-the-ramp sampling.
   * - ``zscam_img``
     - Imager cameras
     - Three Hamamatsu ORCA-Quest 2 qCMOS, 4096x2304, 4.6 micron
     - Millisecond frame times, full-frame and sub-array modes. The three
       must be synchronised.

``zscam_img`` is grouped for a different reason: simultaneous tri-band
millisecond imaging is the imager's whole purpose, and synchronising three
cameras across three processes would make the one thing it exists to do the
hardest thing to guarantee.

The frame store on the qCCDs changes the exposure model. Because near-zero
read noise makes subdivision free, a long integration is normally taken as a
series of shorter ones and the observer watches signal-to-noise accumulate.
The detector daemon therefore manages a series rather than a single
exposure, and publishes progress across it.

Housekeeping
------------

.. list-table::
   :header-rows: 1
   :widths: 18 22 36 24

   * - Peer
     - Owns
     - Responsibilities
     - Driver
   * - ``zshouse_cryo``
     - Cryocoolers
     - NIR cryostat and detector dewar cooling: state, power, fault
       reporting
     - ``cryomech`` / ``sunpower``, TBC
   * - ``zshouse_thermal``
     - Lakeshore chassis
     - Detector and bench temperature control loops, heaters, and the
       structure temperatures that feed flexure and focus models
     - ``lakeshore``
   * - ``zshouse_vacuum``
     - Gauges and pumps
     - NIR cryostat and detector dewar pressures, ion pump state
     - ``inficon``, ``gammavac``
   * - ``zshouse_glycol``
     - Facility cooling interface
     - Glycol supply and return temperatures, flow, leak detection
     - TBC
   * - ``zshouse_power``
     - PDUs and UPS
     - Outlet control, power state, UPS status and battery
     - ``pdu``, ``ups`` (new)
   * - ``zshouse_env``
     - 1-Wire bus
     - Ambient temperature, humidity, dew point, pressure
     - ``onewire``
   * - ``zshouse_watchdog``
     - The host service manager
     - Daemon liveness supervision and systemd control
     - systemd

**On the keyword side** it subscribes to every daemon's heartbeat and status,
detects silence, and publishes ``offline`` on behalf of daemons that cannot
report it themselves. A dead daemon cannot announce that it is dead, so
something else has to.

**On the system side** it owns the host service manager. Starting, stopping,
and restarting a daemon are systemd operations, and the watchdog exposes them
as keywords like any other capability:

.. code-block:: text

   zshouse.watchdog.daemonstates   compound: all daemons, state + heartbeat age
   zshouse.watchdog.restart        trigger, takes a peer id
   zshouse.watchdog.stop           trigger, takes a peer id
   zshouse.watchdog.start          trigger, takes a peer id
   zshouse.watchdog.servicestate   systemd unit state for one peer

This makes daemon lifecycle reachable from the hard hat GUI and the CLI
without anyone opening an ssh session to run ``systemctl``. Restarting a
faulted daemon becomes an ordinary keyword write, logged like every other
command. Restart policy is configuration, per daemon, and is described in
:doc:`deployment`; the watchdog applies it and does not invent it.

Because it must keep working when the rest of the system does not, it has the
fewest dependencies of any daemon: no instrument drivers, and no
configuration beyond the daemon list and the restart policy.

Coordination and gateway daemons
--------------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Peer
     - Responsibilities
   * - ``zsseq_obs``
     - The observation sequencer. Executes instrument workflows, aggregates
       daemon state into instrument state, and manages the target list. Owns
       no hardware.
   * - ``zskeck_tcs``
     - Gateway to the Keck 1 telescope control system, which WMKO owns and
       which lives in an EPICS domain. Republishes telescope pointing,
       rotator angle, airmass, parallactic angle, and hour angle; forwards
       permitted offsets.
   * - ``zskeck_acq``
     - Gateway to WMKO acquisition and guiding. Republishes acquisition and
       guide state so the sequencer and the GUIs can gate on it. Scope
       pending the split below.

``zskeck_tcs`` feeds the ADC dispersion solution and the K-mirror
de-rotation. Both track continuously during an exposure, so this gateway is
not a configuration-time convenience: an interruption to telescope state is
an interruption to two live control loops, and the daemons consuming it must
treat stale telescope state as a fault rather than coast on the last value.

.. note:: **TBC: K1DM3**

   ZShooter is fed by the deployable tertiary K1DM3, and whether the
   instrument receives light at all depends on its position. The ICS needs to
   know that state, and possibly to request it, since staying online for
   target-of-opportunity response is a design driver. Whether that arrives
   through ``zskeck_tcs`` or warrants its own gateway depends on how WMKO
   exposes it.

Acquisition and guiding
~~~~~~~~~~~~~~~~~~~~~~~

Telescope acquisition and guiding is owned by Keck, not by ZShooter. No
daemon in this inventory performs astrometric acquisition, offset
computation, or guiding.

Two things complicate the interface, and both need resolving with WMKO.

**Which Keck system.** MAGIQ is the current Keck acquisition and guiding
system. The design manuscript instead shows the **STRATA** K1AO wavefront
sensing and guider concept upstream of the ZShooter front-end, picking off
part of the beam through a Na D dichroic.

**ZShooter's own imager sees the field.** The imager provides acquisition
support and photometric anchoring over a 2' field, and the front-end can pass
the central 30" to the spectrographs while the remainder continues to the
imager. The instrument can therefore watch the field around the slit during
an observation.

.. note:: **TBC: acquisition functional split**

   To be mapped explicitly and agreed with WMKO:

   - Which acquisition steps does the Keck system perform, and which does the
     instrument initiate?
   - What acquisition and guide state is published, in what domain, and how
     does ZShooter subscribe to it?
   - Does ZShooter's imager contribute to acquisition or guiding, and if so
     what is expected of it and at what cadence?
   - Can the instrument request an offset, and within what limits?
   - What does the Keck system provide that must reach the FITS headers?
   - What happens to a running exposure when guiding is lost?

   Until this is mapped, the acquisition workflow in
   :doc:`../operations/workflows` is a shape rather than a specification.

Summary
-------

.. list-table::
   :header-rows: 1
   :widths: 24 12 64

   * - Class
     - Count
     - Peers
   * - Front-end
     - 2
     - ``zsfe_selector``, ``zsfe_cal``
   * - Mechanism
     - 3
     - ``zsimg_motion``, ``zsvis_motion``, ``zsnir_motion``
   * - Detector
     - 3
     - ``zscam_vis``, ``zscam_nir``, ``zscam_img``
   * - Housekeeping
     - 7
     - ``zshouse_cryo``, ``zshouse_thermal``, ``zshouse_vacuum``,
       ``zshouse_glycol``, ``zshouse_power``, ``zshouse_env``,
       ``zshouse_watchdog``
   * - Coordination
     - 1
     - ``zsseq_obs``
   * - Gateway
     - 2
     - ``zskeck_tcs``, ``zskeck_acq``
   * - **Total**
     - **18**
     -

Distinct daemon *implementations* are fewer still. The two spectrograph
motion daemons share one, and ``zscam_vis`` and ``zscam_nir`` may share one
depending on how far the qCCD and LmAPD readout models diverge. Roughly a
dozen implementations cover eighteen deployed daemons.

Being fixed-format is what keeps this number down. An instrument that
exchanged gratings, cross-dispersers, or cameras during observing would carry
a mechanism, a daemon, and a calibration dependency for each.
