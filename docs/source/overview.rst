Overview
========

What ZShooter is
----------------

ZShooter is a cross-dispersed echelle spectrograph with a co-aligned
three-channel millisecond imager, under development for the Keck I right
Nasmyth platform. It records 3,100 to 24,500 |ang| in a single exposure at
R >= 18,000 with a 0.7" slit, rising to R ~ 42,000 with a 0.3" slit under
seeing enhancement.

.. |ang| unicode:: U+00C5

Mechanically it is **four separately supported assemblies** on the
gravity-invariant Nasmyth platform, each independently alignable and partly
removable for servicing. That division drives the ICS structure.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Assembly
     - Role
   * - Front-end
     - Routes the K1DM3 beam. Mirror selector mechanisms send the full field
       to the imager, the central 30" to the spectrographs with the remainder
       to the imager, or the whole field onward at 60 degrees to neighbouring
       platform positions. Carries the integrating sphere, emission-line
       lamps, and continuum sources used to calibrate the spectrographs and
       to co-calibrate them against the imager.
   * - Imager
     - Three channels, ``u`` / selectable / ``z``, over a 2' field on
       qCMOS detectors with millisecond frame times. A common ADC feeds a
       two-element dichroic tree; the middle channel carries a selectable
       filter mechanism; each channel re-images onto a rotating detector
       assembly. Provides photometric context and acquisition support.
   * - VIS spectrograph
     - Three arms, **B** / **G** / **R**, covering 310 to 980 nm on qCCD
       detectors. Warm.
   * - NIR spectrograph
     - Three arms, **YJ** / **H** / **K**, covering 960 to 2,450 nm on
       HgCdTe LmAPD detectors. Everything downstream of the entrance doublet
       sits in an evacuated cryogenic volume at ~100 K.

Both spectrographs are **fixed-format**: echelle gratings, dichroics,
cross-dispersers, and cameras are not exchanged during observing. This
removes a whole class of mechanism from the instrument and is why the motion
inventory is smaller than the channel count suggests.

Spectrograph arms
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 12 16 22 22 28

   * - Arm
     - Spectrograph
     - Passband
     - Orders
     - Detector
   * - ``B``
     - VIS
     - 310-430 nm
     - 85-118 (34)
     - qCCD, 4096x2048, 15 |mu| m
   * - ``G``
     - VIS
     - 430-650 nm
     - 56-85 (30)
     - qCCD, 4096x2048, 15 |mu| m
   * - ``R``
     - VIS
     - 650-980 nm
     - 37-56 (20)
     - qCCD, 4096x2048, 15 |mu| m
   * - ``YJ``
     - NIR
     - 960-1340 nm
     - 57-80 (24)
     - LmAPD, 2048x2048
   * - ``H``
     - NIR
     - 1470-1830 nm
     - 41-51 (11)
     - LmAPD, 2048x2048
   * - ``K``
     - NIR
     - 1990-2450 nm
     - 31-38 (8)
     - LmAPD, 2048x2048

.. |mu| unicode:: U+03BC

The instrument carries **33 controlled motion axes** and **11 detector
systems**, together with calibration sources, detector readout electronics,
cryocoolers, vacuum equipment, temperature control, and facility power,
network, and glycol interfaces.

Context at Keck
~~~~~~~~~~~~~~~

ZShooter takes the K1 Nasmyth port currently occupied by HIRES, arriving in
2029. The deployable tertiary **K1DM3** feeds it, which is what allows the
instrument to stay online for rapid target-of-opportunity response. Upstream
of the front-end, the **STRATA** K1AO wavefront sensing and guider concept
picks off part of the beam through a Na D dichroic.

None of these are ZShooter's to control. They are external systems the ICS
must interface with; see :doc:`architecture/gateways`.

What the ICS is responsible for
-------------------------------

The ICS owns everything between the observer's intent and the instrument's
hardware:

- Commanding and monitoring every mechanism, detector, lamp, and support device.
- Enforcing safety at the point closest to the hardware.
- Publishing instrument state continuously so that operators, engineers, and
  automated clients see the same truth.
- Sequencing multi-step operations such as instrument configuration,
  acquisition, exposure, and calibration.
- Recording a traceable history of every command and state transition.
- Presenting the instrument through an observer interface and a separate
  engineering ("hard hat") interface.

The ICS is **not** responsible for science data reduction, quicklook analysis,
or archiving. Those systems are downstream consumers; the ICS defines the
handoff to them but does not implement them.

.. _overview-shape:

The shape of the system
-----------------------

The ICS is a set of cooperating processes rather than one program. Every
process that owns hardware is a **daemon**; every daemon speaks the same
message envelope to every other daemon; and all hardware-specific protocol
detail is confined to **drivers**, which are libraries linked into daemons
rather than processes of their own.

.. mermaid::

   flowchart TB
       subgraph P["Presentation"]
           OBS["Observer GUI"]
           HH["Hard hat GUI"]
           CLI["libby CLI / scripts"]
       end

       subgraph C["Coordination"]
           SEQ["Sequencer"]
           TCS["TCS interface"]
       end

       subgraph D["Device daemons"]
           MOT["motion daemons"]
           CAM["detector daemons"]
           CAL["calibration daemons"]
           HK["housekeeping daemons"]
       end

       subgraph DR["Drivers (libraries, not processes)"]
           DRV["coo-ethercat, lakeshore, inficon,<br/>gammavac, pdu, onewire, ..."]
       end

       HW["Instrument hardware"]

       OBS --> SEQ
       HH  --> SEQ
       HH  -.hard hat mode.-> D
       CLI --> D

       SEQ --> D
       SEQ --> TCS
       D   --> DRV
       TCS --> DRV
       DRV --> HW

       D   -.status / telemetry.-> P
       D   -.status / telemetry.-> C

The dotted line from the hard hat GUI directly to device daemons is the
engineering path described in :doc:`operations/modes`. It bypasses the
sequencer, but it does **not** bypass daemon-level safety validation.

Reading order
-------------

- :doc:`architecture/index`: the rules the system is built on: layering,
  messaging, keywords, state, safety, gateways to Keck domains,
  configuration, and reporting.
- :doc:`inventory/index`: the concrete list of daemons and drivers.
- :doc:`interfaces/index`: the observer and hard hat interfaces.
- :doc:`operations/index`: instrument modes and workflows.
- :doc:`development/index`: testing, AIT, continuous integration, and
  releases.
- :doc:`decisions/index`: architectural decisions and the open questions
  that remain.
