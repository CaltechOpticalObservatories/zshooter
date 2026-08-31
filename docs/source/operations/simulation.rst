Simulation and test
===================

Every daemon runs without hardware. This is a requirement rather than a
convenience: the GUIs, the sequencer, and the workflows all need to be built
and regression-tested long before the instrument exists, and they cannot be if
running them requires the instrument.

What simulation must reproduce
------------------------------

A simulated daemon is indistinguishable from a real one to every client:

- the same keywords, types, units, and metadata;
- the same daemon and command state machines;
- the same validation, limits, and interlocks;
- realistic timing: a stage that takes 30 seconds takes 30 seconds, because a
  GUI tested against instant motion has never exercised its progress display,
  its timeout handling, or its cancel path;
- **failures**: timeouts, connection loss, out-of-limit refusals, faults, and
  recovery. A simulator that only succeeds tests only the happy path, which is
  the path least likely to go wrong at 3 a.m.

Where simulation lives
----------------------

At the **driver** boundary. Each driver ships a simulated implementation of the
same API; the daemon selects between them by configuration.

.. mermaid::

   flowchart LR
       D["Device daemon<br/>(identical in both cases)"] --> I{"driver.simulate"}
       I -- false --> R["Real driver"] --> H["Hardware"]
       I -- true --> S["Simulated driver"] --> M["Device model"]

This places the seam as low as possible, so that everything above it (command
validation, state machines, limits, interlocks, keyword serving, publication,
and logging) is the same code in both cases. A simulation seam higher in the
stack would leave the most safety-critical logic untested.

Test levels
-----------

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Level
     - Scope
     - Runs
   * - Unit
     - Library logic in ``src/zshooter``: validation, algorithms, models,
       configuration loading
     - Every commit
   * - Daemon
     - One daemon against its simulated driver: keyword surface, state
       machine, limit enforcement, fault and recovery
     - Every commit
   * - Integration
     - Several daemons plus the sequencer, all simulated: workflows,
       interlocks, ownership, abort paths
     - Every commit
   * - Interface
     - GUIs and CLI against a fully simulated instrument
     - Every commit
   * - Hardware
     - Real drivers against real devices, subsystem by subsystem
     - On the bench, manually

The first four constitute the ``sim`` environment in
:doc:`../inventory/deployment` and run in CI. A change that breaks a workflow
should fail before anyone takes it to the bench.

Fault injection
---------------

Simulated drivers accept injected failures, so that failure paths are tested
deliberately rather than encountered accidentally:

- connection loss and reconnection
- command timeout
- motion stall and unexpected position
- limit switch trip
- controller-reported error codes
- detector readout failure
- temperature or pressure excursion beyond an interlock threshold

Each of these should have an integration test asserting that the instrument
responds correctly: that the fault is published with a specific reason, that
the sequence stops at a safe boundary, that recovery requires an explicit
action, and that nothing silently continues.

First vertical slice
--------------------

Before generating scaffolding for the full inventory, the architecture should
be validated on one thin slice end to end:

.. code-block:: text

   CLI + minimal GUI
     -> Libby transport
     -> one motion daemon (simulated coo-ethercat driver)
     -> keyword surface with limits and validation
     -> published status and telemetry
     -> command log

This exercises the envelope, the keyword conventions, the daemon base class,
the configuration schema, the state machines, and the logging contract, every
architectural decision in these documents, at a scale where getting one wrong
is cheap to fix.

Following the COO ICS specification's recommendation, the second slice should
be a **detector** daemon, because detector daemons stress the parts a
mechanism daemon does not: long-running commands, progress reporting, large
data products, and abort.
