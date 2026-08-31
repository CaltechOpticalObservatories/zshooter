Domain gateways
===============

ZShooter does not operate alone at Keck. Some of what it needs is owned,
operated, and messaged by W. M. Keck Observatory, in messaging domains that are
not ZShooter's.

The Keck 1 telescope control system is one: WMKO owns it and it lives in an
EPICS domain. Acquisition and guiding is another: WMKO owns it under MAGIQ.
Neither speaks the ZShooter message envelope, and neither should be asked to.

A **domain gateway** is a daemon whose job is translation between an external
messaging domain and the ZShooter bus.

.. mermaid::

   flowchart LR
       subgraph WMKO["WMKO domain (owned by Keck)"]
           TCS["Keck 1 TCS<br/>EPICS"]
           MAGIQ["MAGIQ<br/>acquisition + guiding"]
       end

       subgraph GW["Gateways"]
           GTCS["zskeck_tcs"]
           GMAG["zskeck_magiq"]
       end

       subgraph ZS["ZShooter domain"]
           SEQ["zsseq_obs"]
           DEV["device daemons"]
           GUI["GUIs"]
       end

       TCS <-->|"EPICS Channel Access"| GTCS
       MAGIQ <-->|"TBC"| GMAG
       GTCS <-->|"ZShooter envelope"| SEQ
       GMAG <-->|"ZShooter envelope"| SEQ
       GTCS -.->|"PUB telescope state"| DEV
       GTCS -.->|"PUB"| GUI
       GMAG -.->|"PUB acquisition state"| GUI

Why a gateway rather than direct access
---------------------------------------

Every daemon that needed telescope state could hold its own EPICS connection.
It should not, for the same reason that every daemon does not hold its own
connection to a motion controller:

**One point of contact.** The ADC solution, the rotator solution, and the FITS
header assembly all need telescope state. Routing them through one gateway
means one connection to configure, one to monitor, and one to fail. Ten
daemons independently reconnecting to a WMKO service during a network blip is
a self-inflicted incident.

**One place the external protocol appears.** EPICS stops at the gateway.
No other ZShooter daemon has an EPICS dependency, knows a process variable
name, or has to be rebuilt if WMKO changes something. The rest of the
instrument sees ordinary keywords.

**A clear ownership boundary.** The gateway is exactly where "ours" ends and
"theirs" begins. When something is wrong with telescope state, the question of
which team is looking at it has one answer.

**Testability.** A simulated gateway lets the whole instrument be exercised
without WMKO systems, which is what makes the integration tests in
:doc:`../development/testing` possible at all.

What a gateway does
-------------------

A gateway is a device daemon whose "device" happens to be another software
system. It follows the same rules: it owns its connection, holds state,
validates commands, publishes status, and defines a safe state.

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Responsibility
     - Detail
   * - **Translate inward**
     - Subscribe to or poll the external domain and republish its state as
       ZShooter keywords, with ZShooter units and naming conventions.
   * - **Translate outward**
     - Accept ZShooter commands and issue the corresponding external
       operation, within whatever authority the instrument actually holds.
   * - **Enforce the authority boundary**
     - Reject commands ZShooter is not permitted to make. The gateway is where
       "the instrument may request a small offset but may not slew the
       telescope" is enforced.
   * - **Report connection health**
     - Publish whether the external domain is reachable and when its state was
       last updated, distinctly from the values themselves.
   * - **Never invent data**
     - If the external domain is unreachable, publish that. Do not extrapolate,
       do not hold the last value silently, do not substitute a default.

Rules
-----

**A gateway translates; it does not decide.** Instrument policy stays in the
sequencer. A gateway that starts deciding when to offset the telescope has
become a second sequencer, in the place with the least visibility.

**Stale is not the same as bad.** External state carries an age, and consumers
can see it. A telescope position from four minutes ago is not a telescope
position. This is the same rule the GUIs follow in
:doc:`../interfaces/observer-gui`, applied at the source.

**Fail closed.** When the external domain is unreachable, dependent operations
are refused rather than run on assumptions. Interlocks conditioned on external
state treat silence as a blocking condition, per :doc:`safety`.

**The external domain is not under our control.** WMKO may change, restart, or
take down its services on its own schedule. A gateway must reconnect without
intervention, and the instrument must degrade in a defined way rather than
faulting the whole ICS. Which operations remain possible without the telescope
is a mode question, answered in :doc:`../operations/modes`.

Current gateways
----------------

.. list-table::
   :header-rows: 1
   :widths: 20 22 58

   * - Gateway
     - External domain
     - Provides
   * - ``zskeck_tcs``
     - Keck 1 TCS (EPICS)
     - Telescope pointing, rotator angle, airmass, parallactic angle, hour
       angle. Forwards permitted offsets.
   * - ``zskeck_magiq``
     - MAGIQ (WMKO)
     - Acquisition and guiding state. Scope TBC, see
       :doc:`../inventory/daemons`.

Both are specified by role rather than implementation while their interfaces
are agreed with WMKO. The role is stable; the protocol details are not yet
settled.
