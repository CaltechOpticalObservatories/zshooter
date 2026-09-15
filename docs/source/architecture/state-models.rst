State models
============

Two state machines are normative across the ICS: the lifecycle of a command,
and the lifecycle of a daemon. Every ZShooter daemon implements both, using
these names, so that clients can reason about any daemon uniformly.

Command lifecycle
-----------------

.. mermaid::

   stateDiagram-v2
       [*] --> requested
       requested --> rejected: validation failed
       requested --> accepted: validation passed
       requested --> cancelled: cancelled before adjudication
       accepted --> running
       accepted --> cancelled: cancelled before execution
       running --> completed
       running --> failed
       running --> cancelling: halt / abort
       cancelling --> cancelled: stopped cleanly
       cancelling --> failed: cancel did not succeed
       completed --> [*]
       failed --> [*]
       rejected --> [*]
       cancelled --> [*]

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - State
     - Meaning
   * - ``requested``
     - Sent by a client; not yet adjudicated.
   * - ``accepted``
     - Validated, and the daemon has taken responsibility for it. Not yet
       touching hardware.
   * - ``rejected``
     - Refused before execution: out of limits, wrong state, blocked by an
       interlock, or an active fault. Nothing was done to the hardware.
   * - ``running``
     - Executing.
   * - ``completed``
     - Finished successfully.
   * - ``failed``
     - Started and did not finish successfully.
   * - ``cancelling``
     - A ``halt`` or ``abort`` is being processed against running hardware.
   * - ``cancelled``
     - Terminated before normal completion at a client's request.

Cancelling before execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A command can be cancelled at any point, not only once it is running. A
command that has not yet reached the hardware goes straight to ``cancelled``:
there is nothing to stop and nothing to undo, so the transient ``cancelling``
state would be dishonest.

``cancelling`` exists only for the case where hardware is already in motion
and has to be brought to rest, which takes time and can be reported on.

Cancelling can fail
~~~~~~~~~~~~~~~~~~~

A cancellation is a request to the hardware, and hardware can refuse it. A
stage that will not stop, a controller that does not answer, a shutter that
jams part-way: in each case the cancel itself has failed, and the command ends
in ``failed`` rather than ``cancelled``.

The distinction is not pedantic. ``cancelled`` means the instrument is in a
known state that somebody chose. ``failed`` out of ``cancelling`` means the
mechanism is somewhere nobody chose and needs looking at before it is used
again. A client that treats a failed cancel as a successful one will carry on
against hardware that is not where it thinks.

Rejected is not failed
~~~~~~~~~~~~~~~~~~~~~~

A rejection means the instrument is untouched and the client should fix its
request. A failure means the hardware may be in an indeterminate state and
needs inspection. Clients must be able to tell these apart without parsing
error text, which is what the error ``category`` in :doc:`observability`
provides.

Every transition is published under the command's ``transid`` and written to
the command log described in :doc:`observability`.

Daemon lifecycle
----------------

.. mermaid::

   stateDiagram-v2
       [*] --> offline
       offline --> starting: process start
       starting --> initializing: process up
       initializing --> idle: hardware connected, config loaded
       initializing --> fault: connect or config failure
       idle --> ready: readiness conditions met
       ready --> busy: command accepted
       busy --> ready: command finished
       ready --> idle: readiness lost
       idle --> fault
       ready --> fault
       busy --> fault
       fault --> initializing: recover
       fault --> offline: shutdown
       ready --> offline: shutdown
       idle --> offline: shutdown

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - State
     - Meaning
   * - ``offline``
     - Not running or not reachable. Inferred by clients from missing
       heartbeats, since an offline daemon cannot report it.
   * - ``starting``
     - Process is up; not yet functional.
   * - ``initializing``
     - Loading configuration, connecting drivers, reading hardware state.
   * - ``idle``
     - Functional and not executing a command, but not yet ready for observing:
       for example, a stage that is connected but unreferenced, or a detector
       that has not reached operating temperature.
   * - ``ready``
     - Meets every condition for nominal observing operations. The sequencer
       will not start a science exposure unless all required daemons are
       ``ready``.
   * - ``busy``
     - Executing a command or a protected operation.
   * - ``fault``
     - An error prevents normal operation. Requires explicit ``recover``.

The ``idle`` / ``ready`` distinction is the instrument's readiness contract.
Each daemon defines, in configuration, the conditions that make it ready (for
example a homed stage, a detector below its temperature setpoint, or a dewar
below its pressure threshold), and publishes both the boolean and the specific
unmet condition, so that "why can't I start?" has an answer on screen.

Instrument state
----------------

The sequencer aggregates daemon states into a single instrument state that the
observer GUI displays. This aggregate is derived and published; it is not
separately owned, and no daemon takes instruction from it.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Instrument state
     - Derivation
   * - ``offline``
     - One or more required daemons are not reachable.
   * - ``initializing``
     - Any required daemon is ``starting`` or ``initializing``.
   * - ``notready``
     - All required daemons reachable; at least one is not ``ready``.
   * - ``ready``
     - All required daemons are ``ready``.
   * - ``observing``
     - A sequence is running.
   * - ``fault``
     - Any required daemon is ``fault``.
   * - ``safe``
     - The instrument has been commanded to its safe state.

"Required" is per observing mode: the NIR spectrograph being offline does
not stop a VIS-only observation, and neither prevents imaging. The
required-daemon set for each mode is configuration, not code. See
:doc:`../operations/modes`.
