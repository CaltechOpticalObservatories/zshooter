Command authority
=================

Multiple clients can reach the same daemon: the observer GUI, the sequencer,
the hard hat GUI, a CLI session, an engineering script. Without an explicit
authority model, they issue conflicting commands and the instrument does
something nobody asked for.

Authority answers one question per command: *is this requester allowed to do
this, right now?*

Roles
-----

.. list-table::
   :header-rows: 1
   :widths: 18 30 52

   * - Role
     - Held by
     - May do
   * - ``observer``
     - Observer GUI, remote observers
     - Read everything. Issue nominal observing commands through the
       sequencer.
   * - ``sequencer``
     - The sequencer daemon
     - Own the instrument for the duration of a sequence. Command any device
       daemon within its nominal envelope.
   * - ``engineer``
     - Hard hat GUI, engineering CLI sessions
     - Everything ``sequencer`` may do, plus direct device addressing,
       engineering-limit operation, and individual mechanism commands that
       have no observing-mode equivalent.
   * - ``admin``
     - Instrument team
     - Change configuration, force ownership release, override limits where
       the configuration permits it.
   * - ``readonly``
     - Status displays, night-log recorders, remote monitors
     - Read and subscribe. Never command.

Every request carries its requester identity in the envelope's ``sourceid``.
Role is resolved from configuration mapping peer identities to roles, not
asserted by the client in its payload.

Ownership
---------

Authority is about *who you are*; ownership is about *what is currently in
use*. Both are checked.

- A long-running command owns its device until it completes, fails, or is
  cancelled. A second command for that device is rejected while it is held.
- A running sequence takes instrument-level ownership. Direct device commands
  from other clients are rejected for the duration, with a rejection reason
  naming the owning sequence.
- Ownership is published as the ``owner`` keyword on every daemon, so a GUI
  can grey out a control and say *who* holds it rather than failing on submit.
- ``halt`` and ``safe`` ignore ownership. Anyone with a commanding role can
  always stop the instrument.

Hard hat mode
-------------

Hard hat mode is ZShooter's explicit engineering mode, used by support
astronomers, observing assistants, and instrument engineers for
troubleshooting, alignment, commissioning, and maintenance.

What it grants:

- **Direct device addressing.** Commands go to device daemons rather than
  through the sequencer, so a single mechanism can be exercised in isolation.
- **Per-mechanism operations** that have no observing-mode equivalent: homing,
  referencing, drive enable and disable, raw controller queries, jog moves.
- **Engineering limits.** Where configuration defines a wider engineering
  envelope than the observing envelope, hard hat mode operates within it.
- **The full keyword surface**, including keywords hidden from the observer
  GUI, discovered through ``keys.describe`` rather than hand-built panels.

What it does **not** grant:

- **No bypass of daemon safety.** Hardware limits, interlocks, and fault-state
  refusals apply identically in hard hat mode. Engineering limits are a
  *different configured envelope*, not the absence of one. A hard hat command
  that would damage hardware is rejected exactly as any other would be.
- **No bypass of logging.** Every hard hat command is logged with the same
  detail as an observing command, plus the engineer's identity.
- **No private control path.** Hard hat mode uses the same keywords, the same
  envelope, and the same validation as every other client.

Entering and leaving:

- Entry is explicit: an operator action, never a side effect of opening a
  window or connecting a client.
- Entry is **visible**. The daemon's ``mode`` keyword reports ``engineering``,
  and the observer GUI displays a persistent, unmissable banner naming the
  subsystem in hard hat mode and who holds it. An observer must never be
  unaware that an engineer is driving a mechanism.
- Entry is refused while a sequence is running, unless the sequence is
  explicitly aborted or paused first.
- Exit returns the affected daemons to observing limits and re-establishes
  readiness conditions. A daemon left in a non-nominal position on exit reports
  ``idle``, not ``ready``, so the instrument cannot silently return to
  observing with a mechanism parked somewhere unexpected.

Enforcement
-----------

Authority is checked by the daemon, not by the GUI.

A GUI that greys out a control is providing a good user experience; it is not
providing security or safety. The daemon rejects a command from an
insufficiently privileged requester regardless of which client sent it, and the
rejection reason distinguishes *insufficient authority* from *device owned by
another client* from *unsafe request*, because those need three different
responses from the person at the console.

.. note:: **TBC: identity and authentication**

   How peer identities are established and trusted is not yet decided. The
   options range from a static configured address book (simple, adequate for a
   closed summit network) to per-client credentials. This matters more for
   remote observing than for summit operation. Recorded as ADR-0004 in
   :doc:`../decisions/index`.
