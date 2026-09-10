Safety
======

Safety is enforced by the daemon that owns the hardware. That is the only place
it can be enforced completely, because it is the only place every command path
converges.

The validation chain
--------------------

Every command passes through the same chain before the daemon touches
hardware. The order matters: cheaper and more absolute checks come first.

.. mermaid::

   flowchart TB
       A["Command received"] --> B{"Daemon faulted?"}
       B -- yes --> R1["reject: fault active"]
       B -- no --> C{"Type / validator OK?"}
       C -- no --> R2["reject: invalid value"]
       C -- yes --> D{"Within active limits?"}
       D -- no --> R3["reject: out of limits"]
       D -- yes --> E{"Daemon state permits it?"}
       E -- no --> R4["reject: busy or not ready"]
       E -- yes --> F{"Interlocks clear?"}
       F -- no --> R5["reject: interlock"]
       F -- yes --> G["execute"]

``halt`` and ``safe`` skip the chain entirely. They are always accepted, in
every state, from every client.

The chain is about the *hardware*, not about the person. The daemon does not
ask who is calling; anyone who can reach the bus can command it, and the
expectation is that whoever does knows what the keyword means. What the daemon
does insist on is that the command itself is safe for the device right now.

Limits
------

Each mechanism carries four limits in configuration:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Limit
     - Meaning
   * - ``hardmin`` / ``hardmax``
     - Physical travel. Exceeding these damages hardware. Never overridable
       from software; enforced in the controller where the controller supports
       it, and in the daemon regardless.
   * - ``softmin`` / ``softmax``
     - The operating envelope. Narrower than hard limits, with margin. This is
       what observing commands are checked against.

Hard hat mode substitutes an engineering envelope for the observing envelope
where configuration defines one. It never substitutes anything for the hard
limits.

Interlocks
----------

An interlock is a cross-device condition that forbids an otherwise valid
command. Because interlocks span daemons, the daemon enforcing one subscribes
to the state it depends on and holds it locally, so that enforcement does not
require a synchronous round trip at command time, and so that a stale or
missing dependency fails closed.

Candidate ZShooter interlocks:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Interlock
     - Rule
   * - Calibration sources
     - Lamps and continuum sources may not be enabled unless the instrument
       is in calibration mode and the front-end selector is in a calibration
       position. Prevents illuminating the telescope beam.
   * - Front-end routing
     - Selector moves are inhibited while any detector is exposing. Moving
       the beam mid-exposure spoils the frame on every channel at once.
   * - Detector exposure
     - Exposure commands are rejected unless detector configuration is
       complete and the focal plane is at its operating temperature.
   * - Cryostat vacuum
     - Cooling is inhibited above a configured pressure threshold. Cooling a
       poor vacuum damages the cryostat.
   * - Cryogenic motion
     - NIR pre-optics mechanisms are inhibited above a configured
       temperature. Warm mechanisms in a cold design have different
       clearances, and moving them during cooldown or warm-up risks binding.
   * - Motion during readout
     - Mechanisms in the active light path are held during detector readout.
   * - Tracking mechanisms
     - The K-mirror and ADC are refused a new tracking solution when
       telescope state from ``zskeck.tcs`` is stale. Both track continuously,
       and extrapolating from a stale airmass drives them somewhere wrong
       rather than leaving them where they were.
   * - Glycol
     - Detector and cryocooler operation is inhibited on loss of facility
       glycol flow, and the condition is alerted well before it becomes a
       thermal problem.
   * - Warm-up
     - Detector power-down is required before a controlled warm-up.

.. note:: **TBC: interlock table**

   This list is provisional and derived from the mechanism inventory, not from
   the requirements baseline. The authoritative interlock set must be
   established from the L1/L2/L3 safety requirements and reviewed with the
   instrument engineers.

Safe states
-----------

Every daemon defines what "safe" means for its hardware, and can reach it on a
single ``safe`` trigger, including from fault state.

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Daemon class
     - Safe state
   * - Motion daemons
     - Stop motion, hold position under drive if holding is required to
       prevent a fall, otherwise disable drive. Do not home; do not park
       unless parking is unambiguously safe from the current position.
   * - Detector daemons
     - Abort the exposure, close the shutter, hold detector temperature
       control. Preserve any partial frame that can be preserved.
   * - Calibration daemons
     - Extinguish all lamps and continuum sources. Leave the front-end
       selector where it is; moving the beam is not a safe default.
   * - Thermal and cryogenic daemons
     - Hold the current setpoint. Never abandon temperature control; a cryostat
       left uncontrolled is less safe than one held.
   * - Vacuum daemons
     - Continue monitoring and continue publishing. Do not close valves
       automatically.
   * - Power daemons
     - Change nothing. Cutting power is not a safe default; it can strand
       mechanisms and abandon thermal control.

Two of these are worth stating plainly, because the intuitive answer is wrong:
**safe does not mean off**, and **safe does not mean parked**. Removing power
from a cryocooler or homing a stage through an unknown obstruction are both
ways of causing damage while believing you are preventing it.

Fault handling
--------------

On detecting a fault, a daemon:

1. Stops or inhibits unsafe activity where it can do so safely.
2. Enters ``fault``.
3. Publishes a fault event with a specific, actionable reason.
4. Reports the fault in ``isfaulted`` and ``faultreason``.
5. Logs it with enough context to diagnose after the fact: driver state, last
   command, and relevant telemetry at the time.
6. Refuses further commands except ``halt``, ``safe``, ``recover``, and reads.

Recovery is explicit. A daemon does not clear its own fault and resume, because
an automatically-cleared fault is a fault nobody investigates. ``recover``
re-runs initialisation and returns the daemon to ``idle``: never directly to
``ready``, so readiness must be re-established and re-observed.

Faults escalate. A device daemon entering ``fault`` during a sequence causes
the sequencer to stop the sequence at its next safe boundary and surface the
originating fault reason, rather than reporting a generic sequence failure.
