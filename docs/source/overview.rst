Overview
========

What ZShooter is
----------------

ZShooter is a multi-channel imaging spectrograph. Light entering the instrument
is divided between an imaging channel and three spectroscopic channels:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Domain
     - Role
   * - ZImager
     - Imaging channel: rotators, atmospheric dispersion correction, slit,
       focus, and filter selection.
   * - ZSpec nIR
     - Near-infrared spectroscopic channel, including nod control, field stop,
       and a cryogenic detector environment.
   * - ZSpec Blue
     - Blue spectroscopic arm.
   * - ZSpec Red
     - Red spectroscopic arm.

Each channel is supported by shared calibration, lightpath, thermal, vacuum,
power, and environmental infrastructure, and by a telescope interface to the
Keck 1 telescope control system.

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
engineering path described in :doc:`architecture/authority`. It bypasses the
sequencer, but it does **not** bypass daemon-level safety validation.

Reading order
-------------

- :doc:`architecture/index`: the rules the system is built on: layering,
  messaging, gateways to Keck domains, broadcast, alerts, keywords, state,
  authority, and safety.
- :doc:`inventory/index`: the concrete list of daemons and drivers.
- :doc:`interfaces/index`: the observer and hard hat interfaces.
- :doc:`operations/index`: instrument modes, workflows, and simulation.
- :doc:`development/index`: testing, AIT, continuous integration, and
  releases.
- :doc:`decisions/index`: architectural decisions and the open questions
  that remain.
