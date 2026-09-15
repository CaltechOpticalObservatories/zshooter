Messaging
=========

Two distinct communication problems
-----------------------------------

The ICS has two communication problems, and it is important not to confuse
them:

.. list-table::
   :header-rows: 1
   :widths: 22 39 39

   * -
     - Daemon to daemon
     - Driver to device
   * - **Protocol**
     - One common envelope, instrument-wide.
     - Whatever the device speaks.
   * - **Chosen for ZShooter**
     - Libby (Bamboo envelope).
     - Per device: serial, TCP ASCII, EtherCAT, SNMP, EPICS, MQTT, vendor SDK.
   * - **Who sees it**
     - Every daemon and every client.
     - Only the owning driver.
   * - **Changeable?**
     - Transport yes, envelope no.
     - Freely. It is an implementation detail.

Device protocols never appear on the instrument bus. If a vacuum gauge speaks
MQTT and a motion controller speaks EtherCAT, that difference stops at the
driver; both are represented on the bus by identical keyword reads and writes.

Libby
-----

ZShooter uses `Libby <https://github.com/CaltechOpticalObservatories/libby>`_
for all daemon-to-daemon and client-to-daemon messaging. Libby provides:

- the **Bamboo** message envelope, common to every message on the bus;
- **pluggable transports**, ZeroMQ (peer-to-peer) and RabbitMQ (brokered),
  selectable per deployment without changing daemon code;
- **request/response** (``rpc``) and **publish/subscribe** (``publish`` /
  ``topics``) on the same envelope;
- a **typed keyword layer** over RPC (see :doc:`keywords`);
- a **``LibbyDaemon`` base class** providing lifecycle, discovery, service
  registration, and topic subscription;
- a **CLI** that can read and write any keyword on any peer.

A ZShooter daemon is a ``LibbyDaemon`` subclass. It declares its peer identity,
registers typed keywords for the hardware it owns, subscribes to any topics it
needs, and calls ``serve()``.

The message envelope
--------------------

Every message on the instrument bus carries the Bamboo envelope:

.. list-table::
   :header-rows: 1
   :widths: 16 12 72

   * - Field
     - Type
     - Meaning
   * - ``version``
     - int
     - Protocol version. Strictly incrementing.
   * - ``type``
     - MsgType
     - Message type. ZShooter uses ``REQ``, ``RESP``, ``PUB``, ``HELLO``, and
       ``HEARTBEAT``.
   * - ``transid``
     - str
     - Transaction ID (UUID). Correlates a request with its progress events,
       its response, and its log records.
   * - ``key``
     - str
     - The keyword, command, or topic this message concerns.
   * - ``payload``
     - dict
     - JSON object: the value, parameters, result, or error.
   * - ``time``
     - str
     - Sender's message timestamp.
   * - ``sourceid``
     - str
     - Identity of the sending peer.
   * - ``destid``
     - str or None
     - Identity of the receiving peer; ``None`` for broadcast.

Binary data, for example a compressed detector frame, travels alongside the
envelope as an optional ``binary`` field on the message rather than inside the
JSON payload.

Bamboo also defines ``ACK``, ``SUBSCRIBE``, and ``CONFIG``. ZShooter does not
use ``ACK``: see :ref:`one-reply` below.

Envelope and payload division
-----------------------------

The envelope carries routing, identity, and correlation. The payload carries
content. The payload does not repeat what the envelope already says.

For keyword traffic, Libby fixes the payload convention:

.. code-block:: text

   {}                  ->  show    (read current value)
   {"value": V}        ->  modify  (apply V, then return the resulting value)

and responses carry ``{"ok": true, "value": V, "units": "..."}``.

Request and response
--------------------

.. _one-reply:

One request, one reply
~~~~~~~~~~~~~~~~~~~~~~

**Every request gets exactly one reply.** There is no separate acknowledgement
message. A ``REQ`` is answered by a ``RESP``, whether the command succeeded,
was rejected, or failed.

Rejection is fast because validation is cheap and happens before the daemon
touches hardware. A command that is going to be refused is refused in
milliseconds, which is what a two-stage acknowledgement would otherwise have
been used to convey.

For a long-running command the reply arrives at completion, and progress in the
meantime is published, not returned. Clients therefore have exactly one thing
to wait for and one place to find the outcome.

Message flow
~~~~~~~~~~~~

.. mermaid::

   sequenceDiagram
       participant C as Client (GUI / sequencer)
       participant D as Device daemon
       participant H as Hardware

       C->>D: REQ  transid=T  key=zsvis.motion.slitwidth  {"value": 1.0}
       D->>D: validate against limits + current state
       D-->>C: PUB  zsvis.motion.status   (state: busy)
       D->>H: driver call
       D-->>C: PUB  transid=T   progress
       H-->>D: motion complete
       D-->>C: RESP transid=T  {"ok": true, "value": 1.0, "units": "arcsec"}
       D-->>C: PUB  zsvis.motion.status   (state: idle)

A rejected command produces an immediate ``RESP`` carrying the error, and the
daemon never enters ``busy``. A command that is accepted and then fails reports
the failure in its ``RESP`` at the point it gives up. The two are
distinguishable without parsing prose, which matters because they mean
different things about the hardware: see :doc:`state-models`.

Timeouts
~~~~~~~~

Because there is no acknowledgement, a client's timeout must cover the whole
operation, not just its acceptance. This is why every slow keyword advertises
``timeout_s`` in its metadata and why clients read it before issuing a modify.
See :doc:`keywords`.

Broadcast
---------

Commands are point to point: one client asks one daemon to do one thing.
Almost everything else is broadcast. Instrument state, telemetry, events,
progress, and alerts are published once and consumed by whoever needs them.

Why broadcast is the default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**State has many consumers and one owner.** Detector temperature is needed by
the detector daemon's own logic, the sequencer's readiness check, both GUIs,
the FITS header writer, the trending database, and the night log. Serving that
by request would mean seven pollers asking the same question and seven
different answers in flight at once.

**Publication does not depend on being asked.** A daemon publishes whether or
not anyone is listening. A client that connects mid-night sees the full
instrument state without a startup handshake, and a client that restarts
recovers by subscribing rather than by interrogating twenty daemons.

**It keeps clients out of the command path.** A GUI that polls with commands
generates command traffic, fills the command log, and competes with the
sequencer for a daemon's attention. A GUI that subscribes costs nothing extra.

Topics
~~~~~~

Broadcast topics use the same namespace as keywords, so there is one
vocabulary rather than two:

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
status panel can subscribe to ``zsvis.motion.%`` and the watchdog to
``%.%.heartbeat``.

Channels
~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 16 24 24 36

   * - Channel
     - Cadence
     - Retained
     - Consumer response
   * - **Heartbeat**
     - 1 Hz
     - No
     - Detect absence. Silence is the signal.
   * - **State**
     - On change, plus periodic refresh
     - Last value
     - Display; gate decisions on it.
   * - **Telemetry**
     - Per keyword class
     - Historical store
     - Trend, diagnose, write to headers.
   * - **Event**
     - On occurrence
     - Log
     - Record.
   * - **Alert**
     - On occurrence
     - Until cleared
     - Act. See :doc:`observability`.

Periodic refresh
~~~~~~~~~~~~~~~~

State is published on change **and** on a slow periodic cadence. Publishing
only on change is an appealing optimisation that fails in two specific ways:

- a subscriber that connects after the last change has nothing, and cannot
  tell "no change since I connected" from "this daemon is not publishing";
- a dropped publication is invisible, and a consumer can hold a wrong value
  indefinitely. With periodic refresh the state self-corrects on the next
  cycle.

Staleness
~~~~~~~~~

Every published value carries the time it was produced, and consumers are
expected to use it.

A value is **stale** when it is older than a per-keyword threshold, typically a
small multiple of its publication cadence. Stale is a third state alongside
good and bad, and it must be visible:

- GUIs display staleness rather than showing an old number as though it were
  current. A frozen value that looks live is worse than a blank one.
- Interlocks treat stale dependencies as blocking, per :doc:`safety`.
- The sequencer does not gate a decision on stale state; it waits or stops.

Staleness is why heartbeats exist separately from state. A daemon can be alive
and healthy while one value is stale because its hardware stopped responding,
and the two conditions call for different responses.

Delivery expectations
~~~~~~~~~~~~~~~~~~~~~

Broadcast is best effort, and there are no retries at the protocol level.

This is workable because of what is broadcast: a dropped telemetry sample is
replaced by the next one, and a dropped state publication is corrected by the
next refresh. It is **not** workable where a single missed message changes
behaviour, which is why commands are request and response rather than
broadcast, and why alerts are retained until cleared rather than fired once.

Ordering is not guaranteed across topics. A consumer that needs two values to
agree with each other reads them from one compound status publication rather
than correlating two separate ones.

Subscriber rules
~~~~~~~~~~~~~~~~

**Subscribe; do not poll.** A client that repeatedly asks for a value it could
have subscribed to is a defect, not a style preference.

**Handle absence explicitly.** Every subscriber needs defined behaviour for
"this topic has produced nothing for longer than expected". Blank is honest; a
stale value presented as current is not.

**Do not republish.** A consumer that re-broadcasts state it received creates a
second source of truth with a different timestamp. Values derived from several
daemons are published by the one daemon that owns the derivation, as the
sequencer does for aggregated instrument state.

Transport selection
-------------------

The transport is a deployment choice, set per daemon in configuration:

.. list-table::
   :header-rows: 1
   :widths: 16 42 42

   * - Transport
     - Properties
     - Suits
   * - ZeroMQ
     - Peer-to-peer, no broker, lowest latency. Requires each peer to bind an
       address and to hold an address book.
     - Bench work, single-host development, latency-sensitive paths.
   * - RabbitMQ
     - Brokered. No address book; the broker routes. Easier to scale and to
       monitor; the broker is a dependency.
     - Multi-host summit deployment.

Switching is a one-line change in a daemon's configuration. Because both
transports carry the same envelope, a client does not need to know which is in
use, and the two can coexist during migration.

.. note:: **TBC: deployment transport**

   The reference transport for the summit deployment is not yet fixed.
   RabbitMQ is the likely choice given the multi-host layout, but this should
   be settled by prototyping the vertical slice described in
   :doc:`../development/testing`. Recorded as ADR-0003 in
   :doc:`../decisions/index`.

Known gaps
----------

Open items against Libby that ZShooter depends on:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Gap
     - Impact on ZShooter
   * - No ``ERROR`` message type
     - Failures ride in the ``RESP`` payload. Workable, but rejection and
       failure must remain distinguishable from the payload alone.
   * - Peer discovery requires manual key learning
     - ``learn_peer_keys()`` must be called explicitly in ``on_start``.
       Workable for a fixed instrument inventory, but it makes the address
       book configuration that has to be kept correct.
   * - No command cancellation primitive
     - Aborting an exposure or halting a stage mid-move is a hard
       requirement. ZShooter defines ``halt`` and ``abort`` trigger keywords
       per daemon rather than relying on transport-level cancellation. See
       :doc:`state-models`.
   * - No retries at the protocol level
     - By design. Retry policy is an application concern and must be defined
       per command class rather than assumed.
   * - Envelope field names differ from the COO specification
     - Bamboo uses ``transid`` / ``time`` / ``type``; the specification says
       ``trans_id`` / ``timestamp`` / ``msg_type`` and adds ``qos`` and
       ``delivery_policy``. ZShooter follows the Bamboo implementation.
