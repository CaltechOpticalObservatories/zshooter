Testing
=======

The architecture is built so that almost everything can be tested without the
instrument. Simulation lives at the driver boundary (ADR-0006), so every layer
above it (command validation, state machines, limits, interlocks, keyword
serving, publication, and logging) is the *same code* in a test as at the
telescope.

That is what makes the test suite worth trusting: it is not exercising a
parallel implementation.

Where simulation lives
----------------------

At the **driver** boundary. Each driver ships a simulated implementation of
the same API; the daemon selects between them by configuration.

.. mermaid::

   flowchart LR
       D["Device daemon<br/>(identical in both cases)"] --> I{"driver.simulate"}
       I -- false --> R["Real driver"] --> H["Hardware"]
       I -- true --> S["Simulated driver"] --> M["Device model"]

This places the seam as low as possible, so that everything above it (command
validation, state machines, limits, interlocks, keyword serving, publication,
and logging) is the same code in both cases. A simulation seam higher in the
stack would leave the most safety-critical logic untested. Recorded as
ADR-0006 in :doc:`../decisions/index`.

A simulated daemon is indistinguishable from a real one to every client: the
same keywords, the same state machines, the same validation and interlocks,
realistic timing, and realistic failures.

Test levels
-----------

Levels are selected with pytest markers. Unit tests carry no marker.

.. list-table::
   :header-rows: 1
   :widths: 16 34 26 24

   * - Level
     - Scope
     - Marker
     - Runs in CI
   * - Unit
     - Library logic in ``src/zshooter``: validation, algorithms, models,
       configuration loading and schema checks
     - *(none)*
     - Yes
   * - Daemon
     - One daemon against its simulated driver: keyword surface, state
       machine, limit enforcement, fault and recovery
     - ``daemon``
     - Yes
   * - Integration
     - Several daemons plus the sequencer, all simulated: workflows,
       interlocks, cancellation, abort paths
     - ``integration``
     - Yes
   * - Interface
     - GUIs and CLI against a fully simulated instrument
     - ``interface``
     - Yes
   * - Hardware
     - Real drivers against real devices, subsystem by subsystem
     - ``hardware``
     - **No**

Running the tests
-----------------

.. code-block:: console

   $ pip install -e ".[dev]"

   $ pytest                          # everything except hardware
   $ pytest -m daemon                # one level
   $ pytest -m "daemon or integration"
   $ pytest --cov                    # with coverage
   $ pytest tests/daemons/test_zsvis_motion.py -v

Hardware tests are **deselected by default** through ``addopts`` in
``pyproject.toml``. Running them requires asking:

.. code-block:: console

   $ pytest -m hardware

This is deliberate. A hardware test that runs by accident on a developer's
laptop fails confusingly; one that runs by accident on the summit moves a
mechanism nobody asked to move.

``--strict-markers`` is enabled, so a typo in a marker name is an error rather
than a silently empty selection.

What a daemon test looks like
-----------------------------

A daemon test starts the daemon with a simulated driver and a test
configuration, then drives it through its keyword interface, the same interface
a GUI uses. It does not reach into daemon internals, because a test that
bypasses the keyword interface is not testing the thing clients depend on.

.. code-block:: python

   @pytest.mark.daemon
   def test_rejects_move_outside_soft_limits(zsvis_motion):
       result = zsvis_motion.modify("slitwidth", 11.0)   # softmax is 10.0

       assert not result.ok
       assert result.state == "rejected"          # not "failed"
       assert "limit" in result.reason.lower()
       assert zsvis_motion.show("slitwidth") == pytest.approx(1.0)  # unmoved

Three things that assertion set is checking, all of which matter operationally:

- the command was **rejected**, not **failed**: the distinction tells an
  operator whether the hardware was touched (see
  :doc:`../architecture/state-models`);
- the reason is **specific**, because ``"command failed"`` on a GUI at 3 a.m.
  is worthless;
- the mechanism **did not move**.

Failure paths are the point
---------------------------

A simulator that only succeeds tests only the happy path, the path least likely
to go wrong at night. Simulated drivers therefore accept injected failures, and
each has a test asserting the instrument responds correctly:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Injected failure
     - Must assert
   * - Connection loss
     - Daemon publishes ``fault`` with a specific reason; does not exit;
       reconnects on ``recover``.
   * - Command timeout
     - Command reaches ``failed``, not ``completed``; device released.
   * - Motion stall / unexpected position
     - Fault raised; position published as unknown rather than as the target.
   * - Limit switch trip
     - Motion stops; fault raised; ``halt`` still accepted.
   * - Controller error code
     - Surfaced verbatim in ``faultreason``, not swallowed.
   * - Detector readout failure
     - Partial frame preserved where possible; sequence stopped at a safe
       boundary.
   * - Interlock threshold excursion
     - Dependent commands rejected; the interlock names the unmet condition.
   * - Stale interlock dependency
     - Fails **closed**. A daemon that stops hearing about the front-end selector
       not enable lamps.

The last one is the most important test in the suite and the easiest to forget:
it verifies behaviour when a dependency goes *silent*, which is not the same as
that dependency reporting a bad value.

Timing
------

Simulated devices take realistic time. A stage that takes 30 seconds takes 30
seconds under simulation, because a GUI tested against instant motion has never
exercised its progress display, its ``timeout_s`` handling, or its cancel path.

Where a test does not need real duration, it advances a clock rather than
shortening the device model, so the daemon under test still sees the timing it
will see in the field.

Hardware tests
--------------

Hardware tests use the same test bodies as daemon tests where possible, run
against a real driver. They are the gate for summit deployment, not CI.

They are run on the bench, per subsystem, and their results are recorded
against the release being qualified. See :doc:`releases`. A subsystem whose
hardware tests have not been run against a given version has not been
qualified for that version, regardless of what CI says.

Coverage
--------

Coverage is measured on ``src/zshooter`` and reported per run. It is a
diagnostic, not a target: a coverage number cannot distinguish a test that
asserts correct rejection behaviour from one that merely calls a function.

The meaningful coverage question for this system is not "what fraction of lines
ran" but "does every safety rule in :doc:`../architecture/safety` have a test
that asserts it is enforced". That is tracked by requirement traceability,
not by the coverage tool.

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
the configuration schema and its defaults, the state machines, and the logging
contract: every architectural decision in these documents, at a scale where
getting one wrong is cheap to fix.

Following the COO ICS specification's recommendation, the second slice should
be a **detector** daemon, because detector daemons stress the parts a
mechanism daemon does not: long-running commands, progress reporting, large
data products, and cancellation.
