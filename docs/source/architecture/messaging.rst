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
     - Daemon ↔ daemon
     - Driver ↔ device
   * - **Protocol**
     - One common envelope, instrument-wide.
     - Whatever the device speaks.
   * - **Chosen for ZShooter**
     - Libby (Bamboo envelope).
     - Per device: serial, TCP ASCII, EtherCAT, SNMP, MQTT, vendor SDK.
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
- **pluggable transports**: ZeroMQ (peer-to-peer) and RabbitMQ (brokered),
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
     - ``REQ``, ``RESP``, ``ACK``, ``PUB``, ``SUBSCRIBE``, ``HELLO``,
       ``CONFIG``.
   * - ``transid``
     - str
     - Transaction ID (UUID). Correlates a request with its ``ACK``, progress
       ``PUB`` events, final ``RESP``, and log records.
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
     - Identity of the receiving peer; ``None`` for broadcast/publish.

Binary data (for example a compressed detector frame) travels alongside the
envelope as an optional ``binary`` field on the message rather than inside the
JSON payload.

Envelope and payload division
-----------------------------

The envelope carries routing, identity, and correlation. The payload carries
content. The payload does not repeat what the envelope already says.

For keyword traffic, Libby fixes the payload convention:

.. code-block:: text

   {}                  ->  show    (read current value)
   {"value": V}        ->  modify  (apply V, then return the resulting value)

and responses carry ``{"ok": true, "value": V, "units": "..."}``.

Message flow
------------

A short command completes with a single response. A long-running command (a
stage move, an exposure, a cooldown) is acknowledged immediately, publishes
progress, and completes later, all under one ``transid``.

.. mermaid::

   sequenceDiagram
       participant C as Client (GUI / sequencer)
       participant D as Device daemon
       participant H as Hardware

       C->>D: REQ  transid=T  key=zsblue.motion.slitwidth  {"value": 1.0}
       D->>D: validate against limits + current state
       D-->>C: ACK  transid=T   (accepted, command owns the device)
       D->>H: driver call
       D-->>C: PUB  transid=T   progress
       D-->>C: PUB  zsblue.motion.status   (state: busy)
       H-->>D: motion complete
       D-->>C: RESP transid=T  {"ok": true, "value": 1.0, "units": "arcsec"}
       D-->>C: PUB  zsblue.motion.status   (state: idle)

Rejection happens before ``ACK``: a daemon that refuses a command responds
immediately with an error payload and never enters the running state. A
command that is accepted and then fails reports the failure in its final
response.

Status publication is independent of all of this. Every daemon publishes its
status and heartbeat on a fixed cadence regardless of whether anyone is
commanding it, so a client that connects mid-night sees the full instrument
state without asking.

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
   :doc:`../operations/simulation`. Recorded as ADR-0003 in
   :doc:`../decisions/index`.

Known gaps
----------

These are open items against Libby/Bamboo that ZShooter depends on. They are
tracked here because the ICS design assumes them.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Gap
     - Impact on ZShooter
   * - No ``ERROR`` message type
     - The COO ICS specification distinguishes ``ERROR`` from ``RESP``.
       Bamboo's ``MsgType`` currently has no ``ERROR`` member, so failures ride
       in the ``RESP`` payload. ZShooter needs rejection and failure to be
       distinguishable without parsing payload conventions.
   * - Peer discovery requires manual key learning
     - ``learn_peer_keys()`` must be called explicitly in ``on_start``.
       Workable for a fixed instrument inventory, but it makes the address book
       a piece of configuration that must be kept correct.
   * - No command cancellation primitive
     - Aborting an exposure or halting a stage mid-move is a hard requirement.
       ZShooter will define a ``halt`` / ``abort`` trigger keyword per daemon
       (see :doc:`keywords`) rather than relying on transport-level
       cancellation.
   * - No retries at the protocol level
     - By design. Retry policy is an application concern; ZShooter must define
       it explicitly per command class rather than assuming delivery.
   * - Envelope field names differ from the COO specification
     - Bamboo uses ``transid`` / ``time`` / ``type``; the specification document
       says ``trans_id`` / ``timestamp`` / ``msg_type``, and additionally
       defines ``qos`` and ``delivery_policy``. The two should be reconciled;
       ZShooter follows the Bamboo implementation.
