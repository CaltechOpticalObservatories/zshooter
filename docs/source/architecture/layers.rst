Layer model
===========

The ICS is organised into four layers plus the hardware itself. Each layer may
call the layer below it and publish upward. No layer may reach past its
neighbour.

.. mermaid::

   flowchart TB
       L1["<b>Presentation</b><br/>Observer GUI · Hard hat GUI · CLI · scripts"]
       L2["<b>Coordination</b><br/>Sequencer · TCS interface · watchdog"]
       L3["<b>Device daemons</b><br/>own hardware · hold state · enforce safety"]
       L4["<b>Drivers</b><br/>vendor protocol, in-process libraries"]
       L5["<b>Hardware</b>"]

       L1 -- "instrument message protocol" --> L2
       L2 -- "instrument message protocol" --> L3
       L1 -. "hard hat mode only" .-> L3
       L3 -- "Python API" --> L4
       L4 -- "device-native protocol" --> L5

       L3 -. "PUB: status, telemetry, events" .-> L1
       L3 -. "PUB: status, telemetry, events" .-> L2

Presentation layer
------------------

User-facing surfaces. These hold no authoritative state; they render published
state and issue commands.

- **Observer GUI**: the nominal observing interface. Commands the sequencer,
  not individual daemons. See :doc:`../interfaces/observer-gui`.
- **Hard hat GUI**: the engineering interface used by support astronomers,
  observing assistants, and instrument engineers. May address device daemons
  directly, with the subsystem in an explicit and visible engineering mode.
  See :doc:`../interfaces/hardhat-gui`.
- **CLI and scripts**: the ``libby`` command-line client and ad-hoc
  engineering scripts, using the same keyword interface as everything else.
  See :doc:`../interfaces/cli`.

Coordination layer
------------------

Daemons whose job is to talk to other daemons rather than to hardware. They
have no drivers and own no devices.

- **Sequencer**: executes multi-step instrument workflows: configure for a
  target, acquire, expose, read out, run a calibration set, abort safely.
- **TCS interface**: the one exception that touches something external: it
  owns the link to the Keck 1 telescope control system and republishes telescope
  state onto the instrument bus so that no other daemon needs a TCS connection.
- **Watchdog**: supervises daemon liveness and escalates when a daemon stops
  publishing heartbeats.

Coordination daemons are ordinary peers on the message bus. They are
distinguished only by what they command, not by any special privilege.

Device daemon layer
-------------------

The daemons that own hardware. Each one:

- owns exactly one hardware ownership boundary (see :doc:`principles`);
- holds the authoritative state of that hardware;
- validates every command against configured limits and current state;
- executes accepted commands and reports acceptance, progress, and completion;
- publishes status, telemetry, and fault events continuously;
- defines and can enter a safe state for its hardware.

Device daemons are deliberately thin on *policy*. Multi-step behaviour that
spans devices belongs in the coordination layer; reusable per-device behaviour
belongs in the shared library that the daemon imports.

Driver layer
------------

Libraries that speak a vendor's protocol and nothing else. A driver:

- exposes a small, synchronous or async Python API in engineering units where
  it can, and raw device units where it must;
- performs no instrument-level safety reasoning, which is the daemon's job;
- has no knowledge of the message bus, of keywords, or of instrument state;
- is independently testable against a device simulator or a real device.

Most ZShooter drivers already exist as COO packages shared with HISPEC and
other instruments. See :doc:`../inventory/drivers`.

Where code lives
----------------

::

   zshooter/
   ├── src/zshooter/
   │   ├── daemon/          # LibbyDaemon subclass conventions, mixins
   │   ├── devices/         # per-device-class control logic + state models
   │   ├── driver/          # vendor drivers (mostly git submodules)
   │   ├── procedures/      # reusable multi-step operations
   │   ├── algorithms/      # focus fitting, ADC solutions, flexure models
   │   ├── models/          # shared state, command, and result types
   │   ├── config/          # configuration loading and validation
   │   └── telemetry/       # telemetry publication helpers
   ├── daemons/
   │   ├── zsfe/            # one directory per group
   │   │   ├── selector/    # one directory per daemon scope
   │   │   └── cal/
   │   ├── zsimg/
   │   ├── zsvis/
   │   ├── zsnir/
   │   ├── zscam/
   │   ├── zshouse/
   │   ├── zskeck/
   │   └── zsseq/
   ├── configs/             # per-daemon configuration, versioned
   ├── gui/                 # observer and hard hat interfaces
   ├── init.d/              # systemd units
   ├── tests/
   └── docs/

The ``daemons/<group>/<scope>/`` layout mirrors the peer addressing scheme in
:doc:`keywords`: a daemon's directory path is its address.

Daemon entrypoints stay thin. A daemon module wires configuration to a driver,
registers keywords, and serves. Behaviour that is worth testing belongs in
``src/zshooter`` where it can be tested without starting a process.
