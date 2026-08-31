Design principles
=================

The following principles are normative for ZShooter. They are the COO ICS
design rules, made specific to this instrument. Where a design choice is
contested, these principles decide it.

Hardware is owned by exactly one daemon
---------------------------------------

Every piece of hardware has exactly one owning daemon, and that daemon is the
only software permitted to talk to it. GUIs, scripts, the sequencer, and
engineering tools all reach hardware through the owning daemon.

This is what makes safety enforceable: if there were two paths to a motor, a
safety check on one of them would be decorative.

The corollary drives the daemon inventory: where two mechanisms share a
controller or a fieldbus, they share a daemon, because two processes cannot
safely arbitrate one bus. See :doc:`../decisions/index` (ADR-0001).

Drivers are libraries; daemons are processes
--------------------------------------------

A **driver** is a library that knows how to speak a vendor's protocol. It has
no message-bus presence, no lifecycle, and no opinion about instrument state.
A **daemon** is a process that owns hardware, holds state, validates commands,
and speaks the instrument message protocol.

This separation is what makes drivers reusable across COO instruments (the same
``lakeshore`` driver serves HISPEC and ZShooter), and it keeps daemons
testable, because a daemon under test can be handed a simulated driver.

One message envelope, many transports
-------------------------------------

All daemon-to-daemon communication uses a single message envelope. The
transport underneath it is pluggable and may change without changing daemon
code or client code.

Communication *below* the driver layer, from a driver to its device, is
whatever the device speaks: serial, raw TCP, EtherCAT, SNMP, MQTT, a vendor
SDK. Device protocols are a driver implementation detail and never leak onto
the instrument message bus. See :doc:`messaging`.

Safety lives next to the hardware
---------------------------------

The daemon that owns a device is the final authority on whether a command to
that device is safe. Clients may pre-validate for a better user experience,
but a client-side check is never the only check. A daemon must reject an
unsafe command even when the request comes from the sequencer, from hard hat
mode, or from an engineer who is certain they know better.

Status is published, not returned
---------------------------------

Instrument state is published continuously and independently of command
replies. Any number of clients may observe it; none of them owns it. State
that exists only inside a GUI does not exist.

Every command is traceable
--------------------------

Every command carries a transaction identifier that ties together its request,
acceptance, progress events, completion or failure, and log records. It must
always be possible to reconstruct, after the fact, what was commanded, by whom,
whether it was accepted, whether it completed, and why it failed.

The sequencer is a client, not a backdoor
-----------------------------------------

The sequencer uses exactly the same command contract as the GUI and the CLI. It
gets no private API, no privileged call path, and no exemption from validation
or logging. If the sequencer needs a capability, that capability is added to
the daemon's public interface where every client can use it.

Configuration is data
---------------------

Limits, named positions, modes, timeouts, and safe states are versioned
configuration data, not code. They can be reviewed, diffed, and audited
without reading Python. See :doc:`configuration`.

Simulation uses the same interfaces
-----------------------------------

Every daemon runs in simulation without hardware, exposing the same keywords,
the same state model, and the same failure behaviour. This is a requirement,
not a convenience: without it, neither the GUIs nor the sequencer can be
developed or regression-tested before the instrument exists.

Anti-patterns
-------------

The following are explicitly rejected for ZShooter:

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Anti-pattern
     - Why it is rejected
   * - A GUI opening a socket to hardware
     - Bypasses the owning daemon and every safety check it holds.
   * - Commands that return only a string
     - Cannot be correlated, logged, or acted on programmatically.
   * - State that exists only as GUI text
     - Invisible to the sequencer, to engineering tools, and to the night log.
   * - Hidden safety checks in client code
     - Silently lost the moment a second client appears.
   * - A sequencer with a private control path
     - Makes the sequencer untestable and daemon validation optional.
   * - Hardcoded limits and positions
     - Cannot be reviewed or changed without a code release.
   * - A daemon with no simulation mode
     - Blocks all software development until hardware is available.
