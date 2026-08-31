Operational workflows
=====================

Workflows are the multi-step operations the sequencer executes. They are the
reason the sequencer exists: each one spans several daemons, has ordering
constraints, and has a correct way to be abandoned partway through.

Every workflow uses the same command contract as any other client. None of
them has a private path to hardware.

Start of night
--------------

.. mermaid::

   flowchart TB
       A["Verify all daemons reachable"] --> B["Check daemon states"]
       B --> C{"All required ready?"}
       C -- no --> D["Report which, and why"]
       D --> Z["Stop: operator decision"]
       C -- yes --> E["Verify cryostat temps + vacuum in range"]
       E --> F["Verify detectors at operating temperature"]
       F --> G["Reference mechanisms not already referenced"]
       G --> H["Confirm calibration lightpath disengaged"]
       H --> I["Establish TCS communication"]
       I --> J["Publish instrument ready"]

Mechanisms are referenced only if they are not already referenced. Homing a
mechanism that already knows where it is wastes time and creates risk for no
benefit.

Configure for a target
----------------------

The sequencer reads one target from the list and configures the instrument for
it. Independent mechanisms move in parallel; dependent ones are serialised.

.. mermaid::

   flowchart TB
       A["Read target record"] --> B["Validate configuration<br/>against limits + mode"]
       B --> C{"Valid?"}
       C -- no --> R["Reject, hold on target"]
       C -- yes --> D["Command channel mechanisms<br/>(parallel across arms)"]
       D --> E["Command detector configuration"]
       E --> F["Compute + command ADC<br/>from TCS airmass"]
       F --> G["Command rotator from<br/>position angle + parallactic"]
       G --> H["Wait for all in position"]
       H --> I["Publish configured"]

ADC and rotator are commanded after the mechanism moves because both depend on
telescope state from ``zskeck_tcs``, which is not known until the telescope is
pointed.

Acquire target
--------------

Acquisition and guiding is owned by Keck, under MAGIQ. ZShooter does not
acquire or guide; it waits on MAGIQ and gates the exposure on the result.

.. mermaid::

   flowchart TB
       A["Instrument configured for target"] --> B["Telescope pointed<br/>(WMKO)"]
       B --> C["MAGIQ acquires and locks guiding<br/>(WMKO)"]
       C --> D["zskeck_magiq publishes<br/>acquired + guiding state"]
       D --> E{"Acquired and guiding?"}
       E -- no --> F["Hold. Surface MAGIQ state<br/>to the observer"]
       F --> D
       E -- yes --> G["Sequencer proceeds to exposure"]

The sequencer's role is to wait, to show the observer what MAGIQ is reporting,
and to refuse to start a science exposure until the reported state permits it.
It does not compute offsets and does not command the telescope beyond whatever
limited offset authority is agreed.

.. note:: **TBC: MAGIQ functional split**

   The exact division of responsibility, the state MAGIQ publishes, how
   ZShooter subscribes to it, and what the instrument may request are all to be
   agreed with WMKO. Until then this workflow is a shape rather than a
   specification. The open questions are listed in
   :doc:`../inventory/daemons`.

   The behaviour that most needs deciding is what happens to a running sequence
   when guiding is lost mid-exposure: whether the exposure is abandoned,
   completed and flagged, or paused.

Science exposure
----------------

.. mermaid::

   sequenceDiagram
       participant S as zsseq_obs
       participant C as zscam_*
       participant M as motion daemons
       participant T as zskeck_tcs

       S->>S: verify all required daemons ready
       S->>M: hold mechanisms in lightpath
       S->>C: configure exposure
       C-->>S: ACK configured
       S->>C: expose
       C-->>S: ACK, exposure started
       C-->>S: PUB progress (1 Hz)
       S->>T: record telescope state for header
       C-->>S: PUB readout started
       C-->>S: RESP complete, file written
       S->>M: release mechanism hold
       S->>S: advance to next target

Exposures across channels start together where the observing configuration
calls for simultaneity, and each channel reports independently. One channel
failing does not silently abandon the others; the sequencer decides based on
configured policy whether to continue with the remainder.

Nodded nIR observation
----------------------

The nIR channel nods between exposures for sky subtraction. The nod mechanism
is on the nIR motion bus but is commanded inside the exposure loop rather than
during configuration, which makes it the one mechanism whose timing is coupled
to detector readout.

.. mermaid::

   flowchart TB
       A["Configure nIR channel"] --> B["Move to nod position A"]
       B --> C["Expose at A"]
       C --> D["Wait for readout complete"]
       D --> E["Move to nod position B"]
       E --> F["Expose at B"]
       F --> G["Wait for readout complete"]
       G --> H{"Nod cycles remaining?"}
       H -- yes --> B
       H -- no --> I["Return to nominal position"]

The nod move must not begin until readout completes. This is enforced by the
motion-during-readout interlock in :doc:`../architecture/safety`, not by the
sequencer alone. The sequencer getting the ordering right is expected, and the
interlock is what makes it safe when it does not.

Calibration sequence
--------------------

.. mermaid::

   flowchart TB
       A["Enter calibration mode"] --> B["Engage calibration lightpath"]
       B --> C{"Lightpath confirmed?"}
       C -- no --> R["Abort: lamps stay off"]
       C -- yes --> D["Configure channels for cal type"]
       D --> E["Enable lamp, set modulation"]
       E --> F["Wait for lamp stabilisation"]
       F --> G["Expose"]
       G --> H["Extinguish lamp"]
       H --> I{"More cal frames?"}
       I -- yes --> D
       I -- no --> J["Disengage lightpath"]
       J --> K["Exit calibration mode"]

The lightpath confirmation at step C is not a convenience check. Enabling a
lamp with the calibration path disengaged illuminates the telescope beam, and
this is the interlock that prevents it. It is enforced in ``zscal_lamps``, not
here; this workflow merely avoids provoking a rejection it knows would come.

Lamps are extinguished after every frame rather than left on across a set.
Lamp hours are a consumable.

Abort
-----

Abort is not one operation. Three different things get called "abort", and
conflating them is how instruments get damaged.

.. list-table::
   :header-rows: 1
   :widths: 18 30 52

   * - Action
     - Scope
     - Behaviour
   * - ``halt``
     - One daemon
     - Stop that daemon's activity immediately and hold. Always accepted, in
       any state, from any commanding role.
   * - Stop sequence
     - The sequence
     - Finish the current step if finishing is safe, then stop. Preserves the
       in-progress exposure where possible.
   * - Instrument ``safe``
     - Everything
     - Every daemon enters its safe state. Exposure aborted, lamps out, motion
       stopped, thermal control maintained.

Stopping a sequence is the ordinary operator action. Instrument ``safe`` is
for when something is wrong. Both are always available; neither waits for the
current command to finish if waiting would be unsafe.

Fault recovery
--------------

.. mermaid::

   flowchart TB
       A["Daemon publishes fault"] --> B["Sequencer stops sequence<br/>at next safe boundary"]
       B --> C["Fault surfaced in both GUIs<br/>with originating reason"]
       C --> D["Engineer inspects via hard hat"]
       D --> E{"Cause understood?"}
       E -- no --> F["Investigate: telemetry history,<br/>command log, driver state"]
       F --> E
       E -- yes --> G["Command recover"]
       G --> H["Daemon re-initialises to idle"]
       H --> I{"Readiness re-established?"}
       I -- no --> D
       I -- yes --> J["Daemon reports ready"]
       J --> K["Operator resumes sequence"]

Recovery is never automatic and never returns a daemon directly to ``ready``.
The sequencer does not resume by itself; resuming is an operator decision,
because the sequencer cannot know whether the underlying cause was addressed.

End of night
------------

.. mermaid::

   flowchart TB
       A["Complete or stop sequence"] --> B["Extinguish all lamps"]
       B --> C["Park mechanisms at configured<br/>stow positions"]
       C --> D["Confirm detector temperature<br/>control continues"]
       D --> E["Release TCS"]
       E --> F["Write night log summary"]
       F --> G["Publish end-of-night state"]

Cooling is not stopped. Thermal and vacuum daemons keep running, keep
controlling, and keep logging through the day. The overnight and daytime
telemetry record is what makes a slow cryostat problem visible before it
becomes a lost night.
