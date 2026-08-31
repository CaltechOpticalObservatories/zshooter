Assembly, Integration and Test
==============================

AIT is the phase in which the instrument stops being a design and becomes
hardware that works. Subsystems are assembled, connected to their controllers,
brought under software control for the first time, characterised, and then
integrated with each other.

It is also where most of the ICS gets exercised for the first time against real
devices, and where the software team learns what the simulated drivers got
wrong.

What AIT means here
-------------------

The three activities are distinct, and conflating them is how AIT campaigns
lose track of what has actually been demonstrated.

.. list-table::
   :header-rows: 1
   :widths: 16 34 50

   * - Activity
     - Question it answers
     - Software's role
   * - **Assembly**
     - Is it built correctly?
     - Little. Software may read sensors to confirm connections.
   * - **Integration**
     - Does it work under software control?
     - Bring up a daemon against real hardware for the first time. Confirm
       addressing, limits, direction sense, and units.
   * - **Test**
     - Does it meet its requirement?
     - Run a defined procedure, record the result, trace it to a requirement.

"It moved when I pressed the button" is integration. "It positions to within
the required accuracy over the full range, measured, recorded, and repeatable"
is test. Only the second discharges a requirement.

Definition of done
------------------

A subsystem is **AIT complete** when all of the following are true. Anything
less is reported as partial, with the specific gaps named.

.. list-table::
   :header-rows: 1
   :widths: 8 92

   * - ✓
     - Criterion
   * - ☐
     - Every mechanism is under daemon control, with no manual or vendor-tool
       steps in the path.
   * - ☐
     - Hard and soft limits are **measured**, not assumed, and are in reviewed
       configuration.
   * - ☐
     - Direction sense and units are confirmed against physical reality, not
       against the controller's opinion.
   * - ☐
     - Homing and referencing are repeatable from arbitrary starting
       positions.
   * - ☐
     - Every keyword the daemon serves reads correctly and writes correctly.
   * - ☐
     - Every interlock the subsystem participates in has been demonstrated to
       block, including when its dependency goes silent.
   * - ☐
     - The safe state has been demonstrated from the fault state, not only from
       idle.
   * - ☐
     - Fault and recovery have been exercised against the real device, with the
       real error codes recorded.
   * - ☐
     - Hardware tests pass and are recorded against a specific software
       version.
   * - ☐
     - The simulated driver has been corrected wherever the real device
       disagreed with it.

The last one is the one most often skipped and the most costly to skip. A
simulator that no longer matches the hardware silently invalidates every
integration test that depends on it, and nothing will say so.

Foundation of tests
-------------------

AIT tests are the ``hardware`` level described in :doc:`testing`. They are not
a separate framework:

- Same pytest suite, same markers, same fixtures.
- Same test bodies as the ``daemon`` level wherever possible, run against a
  real driver instead of a simulated one. A test that passes in simulation and
  fails on hardware has found something real, and that comparison is only
  possible if it is the same test.
- Deselected by default, so they never run by accident.

.. code-block:: console

   $ pytest -m hardware                              # everything, on the bench
   $ pytest -m hardware tests/hardware/test_zsblue_motion.py
   $ pytest -m hardware --junit-xml=results/zsblue-v1.2.0rc1.xml

Results are recorded against the software version under test. A subsystem
qualified against ``v1.2.0rc1`` is not qualified against ``v1.3.0``, and
:doc:`releases` treats that as a deployment gate.

Every AIT test states which requirement it verifies, so that the campaign
produces traceability rather than a pile of passing tests.

Tooling
-------

AIT work has three distinct shapes, and each has a right tool. Using the wrong
one is the main source of AIT work that cannot be reproduced afterwards.

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Use
     - Tool
     - Why
   * - Repeatable procedure
     - **pytest hardware test**
     - Anything that will be run more than once, or that discharges a
       requirement. Versioned, reviewed, produces a recorded result.
   * - Operational procedure
     - **Script**
     - Bring-up, alignment, pump-down, cooldown. A sequence of steps run by a
       person, with a defined outcome, that is not a pass/fail test.
   * - Exploration and characterisation
     - **Jupyter notebook**
     - Measuring something for the first time, fitting a model, deciding what
       the limit should be. Interactive, with plots and narrative.

Scripts
~~~~~~~

Scripts drive the instrument through the same keyword interface as everything
else, using the ``libby`` CLI or the Python client. They get no privileged
access and are subject to the same authority model, which means a script that
works on the bench works at the summit.

They live in the repository under version control. A bring-up procedure that
exists only in someone's home directory is lost the day they are on leave.

Notebooks
~~~~~~~~~

Notebooks are for the work whose shape is not yet known: characterising a
mechanism, finding where the real limits are, fitting a focus curve, deciding
what a threshold should be.

They are the right tool for that and the wrong tool for anything repeatable.
Two rules keep them from becoming a liability:

- **Notebooks are records, not procedures.** Commit them with outputs, as
  evidence of what was measured and when. Do not build operational dependencies
  on them.
- **A notebook that gets run twice becomes a script or a test.** The second run
  is the signal. What was learned moves into a hardware test, and the measured
  values move into reviewed configuration.

.. note::

   Values discovered in a notebook, particularly limits and named positions,
   are not configuration until they are in a reviewed configuration file. A
   soft limit that exists only in a notebook cell is not protecting anything.

GUIs for AIT
------------

AIT needs interfaces, and they are not the observer GUI. The observer GUI
presents the instrument in terms of observing intent, which is precisely the
abstraction AIT is trying to see through.

The hard hat GUI
~~~~~~~~~~~~~~~~

The hard hat GUI described in :doc:`../interfaces/hardhat-gui` is the primary
AIT interface, and AIT is its most demanding user. During AIT it provides:

- **Generated keyword panels.** Built from ``keys.describe``, so a daemon under
  development gets a working panel the moment it serves a keyword, with no GUI
  work. This is what makes the hard hat GUI usable on hardware that changes
  weekly.
- **Mechanism controls** with jog, absolute move, home, reference, drive
  enable and disable, and halt, showing position, target, and all four limits
  together. This is the interface used to *find* the limits before they exist
  in configuration.
- **The interlock inspector**, which is how an interlock is demonstrated to
  block rather than assumed to.
- **Raw keyword access**, for the cases nothing has anticipated. During AIT
  that is most cases.
- **Telemetry plots**, for watching a cooldown or a settling time.

Because the panels are generated, the hard hat GUI tracks the instrument
through AIT without a GUI development effort tracking alongside it.

Purpose-built AIT panels
~~~~~~~~~~~~~~~~~~~~~~~~

Some AIT activities warrant a dedicated panel: a cooldown monitor showing every
thermal and vacuum channel on one timeline, an alignment aid overlaying a
detector image with mechanism positions, a bus scan showing every node on an
EtherCAT bus and its state.

These are Qt applications like the other GUIs (ADR-0005), and they reuse the
shared keyword widgets rather than reimplementing them. A panel that displays a
temperature must agree with every other surface about its units and its
staleness, and it will not if it is written from scratch.

Purpose-built panels are expected to be temporary. Ones that survive into
operations should be reviewed for inclusion in the hard hat GUI rather than
maintained separately.

Authority during AIT
--------------------

AIT runs in engineering mode, under the authority model in
:doc:`../architecture/authority`. Two things follow, and both matter more
during AIT than at any other time:

**Safety still applies.** Hard limits, interlocks, and fault-state refusals are
enforced identically. Engineering limits are a wider *configured* envelope, not
the absence of one. AIT is when mechanisms are least understood and most
easily damaged, which is the worst possible time to have a bypass available.

**Everything is logged.** Every AIT command is recorded with the engineer's
identity, the same as any other command. The AIT command log is instrument
documentation: when a mechanism behaves oddly in year three, the record of what
it did in year one is the fastest route to understanding it.

Simulation stays in step
------------------------

The single most valuable thing AIT gives the software is knowledge of how the
hardware actually behaves. That knowledge is only kept if it goes back into the
simulated drivers.

Whenever real hardware disagrees with its simulator, the simulator is corrected
in the same change that records the finding:

- real timings, replacing estimates;
- real error codes and the conditions that produce them;
- real failure modes, including the ones nobody predicted;
- real limits and settling behaviour.

Every such correction makes the integration tests in CI more meaningful. Left
undone, the test suite gradually becomes a test of a fiction, and the first
sign of it is a green CI run alongside an instrument that does not work.
