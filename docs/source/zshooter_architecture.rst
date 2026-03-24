Zshooter System Architecture
============================

Overview
--------

The major architectural domains are:

- ZImager
- ZSpec nIR
- ZSpec Blue
- ZSpec Red
- Housekeeping and infrastructure services
- Calibration and lightpath control
- Observer-facing interfaces
- Readout and downstream data reduction systems

Within this architecture, the reusable software library lives under
``src/zshooter``, while deployable runtime daemons live under ``daemons/``.
The shared library contains reusable device control logic, procedures,
algorithms, models, telemetry interfaces, and configuration handling.
Daemons expose runtime control interfaces and should remain thin unless they are
explicitly responsible for orchestration.

Architectural intent
--------------------

The Zshooter architecture separates the following concerns:

- mechanism control
- subsystem organization
- orchestration procedures
- detector readout
- housekeeping and infrastructure monitoring
- observer-facing control surfaces
- downstream reduction and archival processing

A key architectural rule is that device daemons should primarily expose control
capabilities and device state, while reusable operational behavior should live
in the shared library. Multi-step workflows should preferentially be
implemented as reusable procedures rather than embedded directly into daemon
entrypoints.

Repository layout
-----------------

The repository is organized so that the reusable Zshooter software library lives
under ``src/zshooter`` and deployable runtime daemons live beside ``src`` in
the repository hierarchy.

Example::

   project/
   ├── src/
   │   └── zshooter/
   │       ├── devices/
   │       ├── drivers/
   │       ├── procedures/
   │       ├── algorithms/
   │       ├── models/
   │       ├── config/
   │       └── telemetry/
   ├── daemons/
   │   ├── zimager/
   │   ├── zspec_nir/
   │   ├── zspec_blue/
   │   ├── zspec_red/
   │   ├── housekeeping/
   │   └── sequencing/
   ├── configs/
   ├── tests/
   └── docs/

Overall architecture
--------------------

.. mermaid::

   flowchart LR

       subgraph DA["daemons/"]
           subgraph ZI["ZImager daemons"]
               ZI_ROT_U["u rotator"]
               ZI_ROT_V["variable rotator"]
               ZI_ROT_Z["z rotator"]
               ZI_ADC_U["u ADC"]
               ZI_SLIT["slit"]
               ZI_FOCUS["focus"]
               ZI_FILTER["filter"]
           end

           subgraph ZN["ZSpec nIR daemons"]
               ZN_NOD["nod"]
               ZN_ROT["rotator"]
               ZN_FIELD["field stop"]
               ZN_SLIT["slit"]
               ZN_FOCUS["focus"]
               ZN_TEMP["temp control"]
               ZN_CRYO["cryomech"]
           end

           subgraph ZB["ZSpec Blue daemons"]
               ZB_ADC["ADC"]
               ZB_ROT["rotator"]
               ZB_SLIT["slit"]
               ZB_FOCUS["focus"]
               ZB_CRYO["cryotel"]
           end

           subgraph ZR["ZSpec Red daemons"]
               ZR_ADC["ADC"]
               ZR_ROT["rotator"]
               ZR_SLIT["slit"]
               ZR_FOCUS["focus"]
               ZR_CRYO["cryotel"]
           end

           subgraph HK["Housekeeping daemons"]
               HK_TEMP["temp logger"]
               HK_VAC["vacuum logger"]
               HK_MQTT["MQTT relay"]
               HK_WATCH["ICS watchdog"]
               HK_SYS["systemd interface"]
               HK_UPS["networked UPS"]
           end

           CAL["lamp daemon"]
           LP["lightpath selector"]
           SEQ["optional sequencing / coordination peer"]
       end

       subgraph LIB["src/zshooter"]
           DEV["devices"]
           PROC["procedures"]
           ALG["algorithms"]
           DRV["drivers"]
           MOD["models"]
           CFG["config"]
           TEL["telemetry"]
       end

       subgraph EXT["external systems"]
           GUI["observer GUI / user apps"]
           RDO["readout services"]
           DRP["DRP / quicklook / archive"]
           OUT["external procedure outputs"]
       end

       ZI --> DEV
       ZN --> DEV
       ZB --> DEV
       ZR --> DEV
       HK --> DEV
       CAL --> DEV
       LP --> DEV
       SEQ --> PROC

       PROC --> DEV
       PROC --> ALG

       DEV --> DRV
       DEV --> MOD
       PROC --> MOD
       ALG --> MOD

       DEV --> CFG
       DEV --> TEL

       GUI <--> ZI
       GUI <--> ZN
       GUI <--> ZB
       GUI <--> ZR
       GUI <--> HK
       GUI <--> CAL
       GUI <--> LP
       GUI <--> SEQ

       ZI <--> ZN
       ZN <--> ZB
       ZB <--> ZR
       ZR <--> HK

       DEV --> RDO
       RDO --> DRP
       PROC --> OUT

Subsystem-oriented view
-----------------------

Zshooter is described as a set of instrument subsystems, each containing
one or more mechanism-control daemons.

ZImager
~~~~~~~

The ZImager domain contains mechanisms associated with the imaging path,
including rotators, ADC control, slit control, focus control, and filter
control.

Representative daemon responsibilities include:

- rotator positioning
- ADC positioning
- slit configuration
- focus adjustment
- filter selection
- status and health reporting for imaging mechanisms

ZSpec nIR
~~~~~~~~~

The ZSpec nIR domain contains mechanisms and support services associated with
the near-infrared spectroscopic path.

Representative daemon responsibilities include:

- nod control
- rotator control
- field stop control
- slit control
- focus adjustment
- temperature control
- cryogenic subsystem reporting or control

ZSpec Blue
~~~~~~~~~~

The ZSpec Blue domain contains the mechanisms associated with the blue arm of
the spectrograph.

Representative daemon responsibilities include:

- ADC control
- rotator control
- slit control
- focus adjustment
- cryogenic telemetry or support interfaces

ZSpec Red
~~~~~~~~~

The ZSpec Red domain contains the mechanisms associated with the red arm of the
spectrograph.

Representative daemon responsibilities include:

- ADC control
- rotator control
- slit control
- focus adjustment
- cryogenic telemetry or support interfaces

Housekeeping and infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Housekeeping daemons support operational awareness and infrastructure health
rather than direct science mechanism control.

Representative responsibilities include:

- temperature logging
- vacuum logging
- relay or messaging integration
- watchdog supervision
- system service integration
- UPS monitoring

Calibration and lightpath services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calibration and lightpath services are part of operational control when they
are executed by the instrument system.

Representative responsibilities include:

- lamp control
- lightpath selection
- configuration of operational calibration states
- participation in calibration or setup procedures

Shared library role
-------------------

The reusable software under ``src/zshooter`` is the primary home for shared
implementation logic.

This library contains:

- device-domain control surfaces
- driver integrations
- procedures and orchestration logic
- algorithms and decision logic
- state and result models
- telemetry publication interfaces
- configuration loading and validation

The goal is to avoid embedding substantial reusable logic directly inside daemon
entrypoints.

Daemon taxonomy
---------------

The Zshooter architecture includes several classes of runtime services.

Mechanism daemons
~~~~~~~~~~~~~~~~~

Mechanism daemons control one mechanism or tightly related group of mechanisms.

This includes:

- rotator daemons
- slit daemons
- focus daemons
- ADC daemons
- filter daemons
- field stop daemons
- nod daemons
- cryogenic support daemons

These daemons should remain thin and delegate most functional logic to the
shared Zshooter library.

Meta daemons
~~~~~~~~~~~~~~~~~~~~~

Meta daemons coordinate multi-step procedures or multi-subsystem
activities.

This includes:

- API host
- sequencer
- future observing or setup coordinators

These services may call reusable procedures that configure multiple subsystems
for a common operational objective.

Housekeeping daemons
~~~~~~~~~~~~~~~~~~~~

Housekeeping daemons provide infrastructure and operational support services.

Examples include:

- watchdog
- system service integration
- telemetry relays
- facility logging services
- power monitoring services

Readout services
~~~~~~~~~~~~~~~~

Readout services are adjacent to, but distinct from, mechanism control daemons.
They are responsible for detector acquisition and detector-facing readout logic.

These services should be modeled separately from the mechanism control layer
because their operational behavior, data products, and fault modes differ from
those of ordinary mechanism daemons.

External interfaces and downstream systems
------------------------------------------

The Zshooter architecture interacts with several external or adjacent systems.

Observer-facing systems
~~~~~~~~~~~~~~~~~~~~~~~

Observer-facing systems include GUIs or operational consoles used to monitor
and command the instrument through approved control interfaces.

Readout systems
~~~~~~~~~~~~~~~

Readout systems are responsible for detector data acquisition and handoff to
downstream consumers.

Downstream reduction systems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Downstream data reduction systems, quicklook services, and archive-oriented
pipelines are operationally adjacent to the instrument but should not be
confused with the low-level mechanism control architecture.

Procedure outputs
~~~~~~~~~~~~~~~~~

Some procedures may generate outputs intended for operator, engineering, or
science use. These may include reports, calibration exposures, fitted
coefficients, alignment offsets, or other reference products.

Such outputs are not assumed to live inside this repository unless explicitly
stated. The control architecture is responsible for defining what procedures
produce, how status and metadata are reported, and how output locations are
communicated to users or downstream systems.

