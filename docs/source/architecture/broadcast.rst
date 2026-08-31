Broadcast system
================

Commands are point to point: one client asks one daemon to do one thing. Almost
everything else in the ICS is broadcast. Instrument state, telemetry, events,
progress, alerts, and heartbeats are published once and consumed by whoever
needs them.

This page defines how that publish and subscribe layer works.

Why broadcast is the default
----------------------------

**State has many consumers and one owner.** Detector temperature is needed by
the detector daemon's own logic, the sequencer's readiness check, the observer
GUI, the hard hat GUI, the FITS header writer, the trending database, and the
night log. Serving that by request would mean seven pollers asking the same
question, and seven different answers in flight at once.

**Publication does not depend on being asked.** A daemon publishes whether or
not anyone is listening. A client that connects mid-night sees the full
instrument state without a startup handshake, and a client that crashes and
restarts recovers by subscribing rather than by interrogating twenty daemons.

**It keeps clients out of the command path.** A GUI that polls with commands is
generating command traffic, filling the command log, and competing with the
sequencer for a daemon's attention. A GUI that subscribes costs the daemon
nothing extra.

Topic structure
---------------

Broadcast topics use the same namespace as keywords, so there is one vocabulary
to learn rather than two:

.. code-block:: text

   <group>.<scope>.<name>          state and telemetry, per keyword
   <group>.<scope>.status          compound daemon status
   <group>.<scope>.event           events from that daemon
   <group>.<scope>.alert           alerts from that daemon
   <group>.<scope>.heartbeat       liveness

   zsseq.obs.sequence              sequence progress
   zsseq.obs.instrument            aggregated instrument state
   <transid>                       progress for one running command

Subscribers use the same ``%`` wildcard convention as keyword queries, so a
status panel can subscribe to ``zsblue.motion.%`` and a watchdog to
``%.%.heartbeat``.

Channels
--------

Five kinds of thing are broadcast. They differ in cadence, in retention, and in
what a consumer is expected to do about them.

.. list-table::
   :header-rows: 1
   :widths: 16 22 22 40

   * - Channel
     - Cadence
     - Retained
     - Consumer response
   * - **Heartbeat**
     - Fixed, 1 Hz
     - No
     - Detect absence. Silence is the signal.
   * - **State**
     - On change, plus periodic refresh
     - Yes, last value
     - Display, gate decisions on it.
   * - **Telemetry**
     - Fixed, per keyword class
     - Historical store
     - Trend, diagnose, write to headers.
   * - **Event**
     - On occurrence
     - Log
     - Record. Notable but not necessarily actionable.
   * - **Alert**
     - On occurrence
     - Until cleared
     - Act. See :doc:`alerts`.

The distinction between event and alert is the one most often collapsed, and
collapsing it is how operators learn to ignore the message pane. It is treated
separately in :doc:`alerts`.

Periodic refresh
----------------

State is published on change **and** on a slow periodic cadence, typically
every few seconds. Publishing only on change is a common and appealing
optimisation, and it fails in two specific ways:

- A subscriber that connects after the last change has nothing, and cannot
  tell "no change since I connected" from "this daemon is not publishing".
- A dropped publication is invisible. With periodic refresh, the state
  self-corrects on the next cycle; without it, a consumer can hold a wrong
  value indefinitely.

The refresh cadence is slow enough not to matter for load and fast enough that
no consumer is ever wrong for long.

Staleness
---------

Every published value carries the time it was produced, and consumers are
expected to use it.

A value is **stale** when it is older than a per-keyword threshold, typically a
small multiple of its publication cadence. Stale is a third state alongside
good and bad, and it must be visible:

- GUIs display staleness rather than showing an old number as though it were
  current. A frozen value that looks live is worse than a blank one.
- Interlocks treat stale dependencies as blocking, per :doc:`safety`. A daemon
  that has stopped hearing about the calibration lightpath must not enable
  lamps.
- The sequencer does not gate a decision on stale state; it waits or stops.

Staleness is why heartbeats exist separately from state. A daemon can be alive
and healthy while a particular value is stale because its hardware stopped
responding, and the two conditions call for different responses.

Delivery expectations
---------------------

Broadcast is best effort. There are no retries at the protocol level, by
design.

This is workable because of what is broadcast: a dropped telemetry sample is
replaced by the next one, and a dropped state publication is corrected by the
next periodic refresh. It is **not** workable for anything where a single
missed message changes behaviour, which is why:

- **Commands are not broadcast.** They are request and response, with
  acknowledgement and correlation.
- **Alerts are retained until cleared**, not fired once and forgotten. An alert
  that is published once and dropped is an alert that did not happen.
- **Consumers must be idempotent.** Receiving the same state twice must be
  harmless, because with periodic refresh it is guaranteed.

Ordering is not guaranteed across topics. A consumer that needs two values to
agree with each other reads them as one compound status publication rather than
correlating two separate ones.

Subscriber rules
----------------

**Subscribe; do not poll.** A client that repeatedly asks for a value it could
have subscribed to is a defect, not a style preference.

**Never assume you are the only subscriber.** Publication is one to many. A
consumer cannot acknowledge, consume, or otherwise affect a message on behalf
of others.

**Handle absence explicitly.** Every subscriber needs defined behaviour for
"this topic has produced nothing for longer than expected". Blank is an honest
display; a stale value presented as current is not.

**Do not republish.** A consumer that re-broadcasts state it received creates a
second source of truth with a different timestamp. If something needs deriving
from several daemons' state, the derived value is published by the one daemon
that owns the derivation, as the sequencer does for aggregated instrument
state.

Simulation and test
-------------------

Because broadcast is the primary way state moves, it is also the primary thing
integration tests assert on. A test subscribes exactly as a GUI does and checks
what was published, in what order, and with what timing.

Fault injection covers the broadcast layer itself: dropped publications, a
daemon that goes silent without dying, and stale dependencies. The last of
these is the test that catches interlocks which fail open, and it is covered in
:doc:`../development/testing`.
