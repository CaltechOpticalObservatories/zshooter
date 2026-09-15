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
fieldbus, owning every mechanism attached to it, and following the
instrument's four-assembly split. Against the SPIE 2026 design this yields 18
daemons from roughly a dozen implementations, covering 33 motion axes and 11
detector systems.

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
(:doc:`../development/testing`), which should be built against both to
confirm the abstraction genuinely holds.

ADR-0004: No command authority model
------------------------------------

**Status:** Accepted. Supersedes an earlier open question about peer identity
and authentication.

**Context.** An earlier draft carried a role-based authority model: clients
were classified as observer, sequencer, engineer, admin, or read-only, daemons
resolved a role from the requesting peer, and commands outside a role were
rejected. It also introduced device ownership, so that a running command or
sequence excluded other clients.

**Decision.** Remove both. Daemons do not ask who is calling. Any client that
can reach the bus can command any keyword, and whoever does so is expected to
know what that keyword does.

**Rationale.** The model was solving a problem ZShooter does not have. The
people who reach the instrument bus are observers, support astronomers,
observing assistants, and instrument engineers on a closed observatory
network, and what each of them may sensibly do is already bounded by what they
know. A role table encoded that knowledge as configuration, where it would go
stale, and made every daemon carry identity resolution in order to enforce it.

It also bought less safety than it appeared to. Safety comes from the daemon
refusing unsafe commands, which it does regardless of who asked. Authority
only ever governed who was allowed to make a request that was safe anyway.

**Consequences.** The validation chain in :doc:`../architecture/safety` loses
two of its seven checks and is about the hardware alone. The ``owner`` keyword
is gone. Concurrency is handled by daemon state: a ``busy`` daemon rejects a
second command with a ``state`` error, which is the honest reason. Engineering
work is governed by the engineering *mode* in :doc:`../operations/modes`,
which remains explicit and announced, because its purpose is to tell observers
what is happening rather than to withhold permission.

Nothing here protects the instrument from a client on the observatory network
that behaves badly. That is accepted: it is a network-boundary problem rather
than one an instrument daemon can solve, and WMKO's network controls are what
actually stand between the instrument and the outside.

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

ADR-0007: Shipped default configuration
---------------------------------------

**Status:** Accepted

**Context.** An earlier draft resolved configuration through four layers and
required a daemon to refuse to start rather than default anything. That made
every daemon's configuration long, mostly boilerplate, and slow to stand up on
the bench.

**Decision.** Each daemon ships a default configuration file next to its code
and carries the same defaults as literals, so it behaves sensibly even if that
file is missing. Instrument and deployment configuration supply only what
differs. Three layers, not four.

**Rationale.** Most configuration values are the same everywhere and are not
safety-relevant: publication cadences, retry policy, log destinations. Making
someone restate them per daemon adds work and adds places to get them wrong.

**Consequences.** Two categories still have no defaults and still block
startup when missing: hard limits with safe-state definitions, and hardware
identity such as controller addresses and bus node numbers. A guessed limit
looks like protection and is not; a guessed address commands the wrong device.
Defaults are applied before validation rather than as a fallback for values
that failed it, which is what keeps this safe. See
:doc:`../architecture/configuration`.

Open questions beyond the ADRs
------------------------------

These are unresolved and are not yet decisions because the information needed
to decide is missing.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Question
     - Blocked on
   * - How does acquisition divide between Keck and ZShooter's imager?
     - Agreement with WMKO. The imager sees a 2' field and provides
       acquisition support, so the split is not simply "Keck acquires".
   * - MAGIQ or STRATA?
     - What WMKO has in place at first light in 2029. Determines what
       ``zskeck_acq`` talks to.
   * - What are the two unidentified detector systems?
     - The design team. Nine of eleven are accounted for; if either of the
       remaining two is a slit-viewer it changes the acquisition workflow.
   * - What readout software do the LmAPD and qCMOS need?
     - Detector selection. The VIS qCCD is covered: it runs on an Archon and
       so uses ``camera-interface``. The NIR and imager focal planes have no
       COO driver, and the LmAPD part is not yet chosen.
   * - What are the scientific observing modes?
     - The requirements baseline. Determines the observer GUI's configuration
       vocabulary and the required-daemon sets per mode.
   * - What is the authoritative interlock set?
     - The requirements baseline and review with instrument engineers.
   * - Which mechanisms are on which controllers?
     - The as-built electronics design.
   * - What does the DRP require in FITS headers?
     - Agreement with the data reduction pipeline team.
   * - Which EPICS process variables does the ICS read and write?
     - Agreement with WMKO, along with the Channel Access client library and
       whether ZShooter connects directly or through a WMKO access layer.
   * - How does the ICS learn K1DM3 state?
     - Agreement with WMKO. Whether the instrument is receiving light at all
       depends on it.
   * - What is the facility glycol interface?
     - WMKO platform services. Determines the ``zshouse_glycol`` driver.
