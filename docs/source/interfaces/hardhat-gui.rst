Hard hat GUI
============

Audience and purpose
--------------------

The hard hat GUI is the engineering interface for support astronomers,
observing assistants, and instrument engineers. It is used for
troubleshooting, alignment, commissioning, maintenance, and answering the
question "what is the instrument actually doing?" when the observer GUI says
something is wrong.

Its users understand the instrument's mechanisms. It therefore presents the
instrument the way it is actually built, daemon by daemon and mechanism by
mechanism, which is exactly what the observer GUI must not do.

Relationship to the backend
---------------------------

The hard hat GUI addresses device daemons directly, under the explicit
engineering authority described in :doc:`../architecture/authority`.

.. mermaid::

   flowchart LR
       HH["Hard hat GUI"] -->|"direct, engineering authority"| D["device daemons"]
       HH -->|"sequencer operations"| SEQ["zsseq_obs"]
       D -.->|"PUB full keyword state"| HH

This is the one place in the architecture where a GUI bypasses the sequencer.
It bypasses **only the sequencer**: never daemon validation, never limits,
never interlocks, never logging.

Content
-------

**Daemon roster**: every daemon, its state, heartbeat age, connection status,
active fault, current owner, and configuration version. Whether a daemon has
stopped publishing is visible at a glance.

**Per-daemon panels**: for each daemon, the full keyword surface: every value,
its units, whether it is writable, its limits, and its description. These are
**generated from** ``keys.list`` **and** ``keys.describe``, not hand-built.
A new keyword appears in the GUI without a GUI change, and a GUI panel cannot
drift out of date with the daemon it controls.

**Mechanism controls**: per-mechanism jog, absolute move, home, reference,
drive enable and disable, and halt, with live position, target, and the four
limits displayed together so that a commanded value can be seen in context.

**Engineering envelope**: where an engineering limit differs from the
observing limit, both are shown, along with which is currently active.

**Interlock inspector**: the current state of every interlock and, when one is
blocking, exactly which condition is unmet and which daemon publishes it.
Debugging an interlock without this means guessing.

**Fault and recovery**: the active fault with its captured context, and the
explicit ``recover`` action.

**Command history**: the recent command log, filterable by daemon, by
requester, and by outcome, with rejections included. Rejections are usually the
fastest route to understanding a misconfiguration.

**Telemetry plots**: trends for temperature, pressure, and position. Cryostat
history is the primary diagnostic for detector problems and needs to be
reachable without leaving the tool.

**Raw keyword access**: arbitrary read and write of any keyword on any daemon,
subject to daemon validation, for cases the panels do not anticipate.

Entering and leaving
--------------------

Entry is explicit, per subsystem, and refused while a sequence is running. The
engineer's identity is recorded and published in the affected daemons'
``owner`` keyword.

Entry is announced. The observer GUI shows a persistent banner; the event
stream records it. There is no quiet engineering mode: an observer who does not
know an engineer is moving a mechanism will misdiagnose everything that
follows.

On exit, affected daemons return to observing limits and must re-establish
readiness. A daemon left in a non-nominal configuration reports ``idle``
rather than ``ready``, so the instrument cannot slip back into observing with
a mechanism parked somewhere unexpected.

What it must not become
-----------------------

- **A second control system.** It uses the same keywords and the same
  validation as everything else. It gets no special daemon interface.
- **A way around a limit.** An engineer who needs a wider envelope changes the
  engineering limits in reviewed configuration. There is no button that
  disables checking.
- **Unlogged.** Hard hat commands are logged with the same detail as observing
  commands, plus the engineer's identity. Commissioning history is instrument
  documentation.
