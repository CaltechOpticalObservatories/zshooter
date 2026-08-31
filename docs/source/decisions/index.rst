Architectural decisions
=======================

Decisions that shape the ICS, why they were made, and what remains open. Each
records the alternatives so that a future revisit starts from the reasoning
rather than from scratch.

ADR-0001: Daemon granularity at hardware ownership boundaries
--------------------------------------------------------------

**Status:** Accepted

**Context.** A daemon can own one mechanism, one controller, or one subsystem.
The choice fixes the process count, the fault isolation, and where safety
reasoning lives. An earlier draft of the architecture implied one daemon per
mechanism (~30); HISPEC uses roughly one per subsystem (~10).

**Decision.** One daemon per hardware ownership boundary: per controller or
fieldbus, owning every mechanism attached to it. This yields ~21 daemons from
~12 implementations.

**Rationale.** Mechanisms sharing an EtherCAT bus or a Lakeshore chassis cannot
be owned by separate processes without a bus arbiter, which is a daemon by
another name, and one that separates safety logic from hardware access. Owning
by controller keeps a daemon's validation and its device access in the same
place.

**Consequences.** Fault isolation is coarser than per-mechanism: a daemon fault
takes out every mechanism on its bus. This is accepted, because a controller
fault would take them out anyway. Daemon internals must handle concurrent
commands to independent mechanisms on a shared bus.

**Open.** The mapping of mechanisms to controllers is provisional and must be
confirmed against the as-built electronics design. See
:doc:`../inventory/daemons`.

ADR-0002: Libby for daemon-to-daemon messaging
------------------------------------------------

**Status:** Accepted

**Context.** The ICS needs one message envelope shared by every daemon and
every client, with a transport that can change without changing code.

**Decision.** Libby, carrying the Bamboo envelope, for all daemon-to-daemon and
client-to-daemon messaging. Device-facing protocols remain per-device and are
confined to drivers.

**Rationale.** Libby gives request/response and publish/subscribe on one
envelope, a typed keyword layer with discoverable metadata, a daemon base
class, and a generic CLI that works against any peer. It is COO software,
already in use, and pluggable across ZeroMQ and RabbitMQ.

**Consequences.** ZShooter depends on Libby's maturity. The gaps listed in
:doc:`../architecture/messaging` (no ``ERROR`` message type, manual peer key
learning, and no cancellation primitive) must be closed in Libby or worked around
in ZShooter, and the workarounds should be pushed upstream rather than
accumulated locally.

ADR-0003: Deployment transport
--------------------------------

**Status:** Open

**Context.** Libby supports ZeroMQ (peer-to-peer, no broker, lowest latency,
requires an address book) and RabbitMQ (brokered, self-routing, easier to
monitor, broker is a dependency).

**Options.** RabbitMQ for the summit deployment, given the multi-host layout
and the address-book burden that ZeroMQ imposes while Libby's discovery
requires manual key learning. ZeroMQ for bench and single-host work.

**Decision needed by.** Completion of the first vertical slice
(:doc:`../operations/simulation`), which should be built against both to
confirm the abstraction genuinely holds.

ADR-0004: Peer identity and authentication
--------------------------------------------

**Status:** Open

**Context.** The authority model in :doc:`../architecture/authority` resolves a
role from a peer identity. How identities are established and trusted is not
decided.

**Options.** A static configured address book mapping peer IDs to roles:
simple, adequate for a closed summit network, and offering no protection
against a misconfigured or malicious client on that network. Or per-client
credentials: stronger, and more to operate.

**Considerations.** The answer depends more on remote observing than on summit
operation, and remote observing is the norm at Keck rather than the exception.
If clients command the instrument from Waimea or from a mainland remote site,
the static address-book answer is insufficient on its own. WMKO's own network
and access controls carry part of this; what they carry and what the ICS must
carry needs to be established rather than assumed.

ADR-0005: Qt (PyQt/PySide) for the GUIs
-----------------------------------------

**Status:** Accepted

**Context.** Three user-facing surfaces are needed: an observer GUI, a hard hat
GUI, and AIT tooling. They have different audiences and different rates of
change, but they display the same published state and issue commands through
the same keyword interface.

**Decision.** Qt, via PyQt or PySide, for all of them.

**Rationale.** It matches the team's existing experience and HISPEC's practice,
keeps the GUIs in the same language as the daemons and the shared library so
that keyword metadata and model types are reused rather than reimplemented, and
supports the metadata-generated panels the hard hat GUI and AIT tools depend
on. Remote access is served through VNC sessions on the control host.

**Consequences.** Remote observers reach the GUIs through VNC rather than a
browser. Widgets that render keyword state should be written once as a shared
widget library and used by all three surfaces, so a keyword displayed in the
observer GUI, the hard hat GUI, and an AIT panel cannot disagree about units,
staleness, or limits.

**Open.** PyQt versus PySide is not settled here. The licensing and packaging
differences matter more than the API differences, which are small.

ADR-0006: Simulation at the driver boundary
---------------------------------------------

**Status:** Accepted

**Context.** Simulation can be placed at the driver, at the daemon, or at the
transport.

**Decision.** At the driver: each driver ships a simulated implementation of
the same API, selected by configuration.

**Rationale.** This is the lowest possible seam, so everything above it
(validation, state machines, limits, interlocks, keyword serving, publication,
and logging) is the same code in simulation and on hardware. A higher seam would
leave the most safety-critical logic untested.

**Consequences.** Every driver carries the obligation to provide a simulator
that models timing and failure, not merely success. This is real effort per
driver and must be scoped as such.

Open questions beyond the ADRs
------------------------------

These are unresolved and are not yet decisions because the information needed
to decide is missing.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Question
     - Blocked on
   * - Does the ICS perform acquisition and guiding?
     - The requirements baseline. Substantially changes the daemon inventory
       if yes.
   * - Which detector controller per channel?
     - Detector selection. Determines the ``zscam_*`` daemon count and the
       readout mode vocabulary.
   * - What are the scientific observing modes?
     - The requirements baseline. Determines the observer GUI's configuration
       vocabulary and the required-daemon sets per mode.
   * - What is the authoritative interlock set?
     - The requirements baseline and review with instrument engineers.
   * - Which mechanisms are on which controllers?
     - The as-built electronics design.
   * - What does the DRP require in FITS headers?
     - Agreement with the data reduction pipeline team.
   * - How does the ICS talk to the Keck 1 telescope?
     - Agreement with WMKO: which protocol (KTL, mKTL), which telescope
       keywords ZShooter may read, and what offset authority an instrument
       holds.
   * - Does WMKO or the ICS provide guiding?
     - Agreement with WMKO. Removes or adds a substantial daemon.
