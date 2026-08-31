Requirements
============

.. toctree::
   :maxdepth: 2

   traceability

Status
------

.. warning:: **The requirements baseline has not yet been ingested.**

   The L1/L2/L3 requirements for ZShooter exist as spreadsheets
   (``ZShooter L1-L3 Requirements Update (inprogress JIB 26.8)`` and the
   ``-2`` revision) but have not been read into this documentation set.

   Everything downstream of the requirements is therefore **provisional**:

   - the mechanism list, and so the daemon inventory in
     :doc:`../inventory/daemons`
   - the interlock table in :doc:`../architecture/safety`
   - the scientific observing modes in :doc:`../operations/modes`
   - whether acquisition and guiding are ICS responsibilities
   - the detector controller selection
   - the acceptance criteria every component must be verified against

   These are marked ``TBC`` where they appear.

Why traceability matters here
-----------------------------

Two things need to be answerable at any point in the project, and neither is
answerable without a maintained trace:

**Forward**: for a given requirement, which daemon, keyword, workflow, or
interlock satisfies it, and how is that verified? Without this, requirements
are silently dropped: nobody notices that nothing implements L2-047 until
commissioning.

**Backward**: for a given daemon or keyword, which requirement justifies its
existence? Without this, the ICS accumulates capability that nobody asked for
and that nobody maintains, while the effort that built it was not spent on
something that was required.

Ingestion plan
--------------

1. **Import** both spreadsheet revisions and reconcile them, recording where
   the ``-2`` revision differs.
2. **Filter** to requirements that levy something on the ICS. Not all do; an
   optical throughput requirement generally does not, though a requirement to
   *measure* throughput does.
3. **Classify** each ICS requirement as bearing on: a mechanism (implies a
   daemon), a measurement (implies a keyword and telemetry), a safety rule
   (implies an interlock or limit), an operation (implies a workflow), a
   performance target (implies a timing budget), or an interface (implies a
   contract with an external system).
4. **Reconcile** the mechanism-derived requirements against the daemon
   inventory. Every mechanism must have an owning daemon; every daemon must
   trace to at least one requirement. Discrepancies in either direction are
   findings, not bookkeeping errors.
5. **Populate** :doc:`traceability`.
6. **Derive** L3 software requirements where an L2 requirement needs
   decomposition to be verifiable.

Step 4 is the one that will produce real findings. It is where a missing
acquisition camera, an unaccounted-for mechanism, or a daemon nobody needs
becomes visible, and it is far cheaper to discover now than after scaffolding
is generated.

Verification
------------

Each ICS requirement carries a verification method:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Method
     - Applies to
   * - Inspection
     - Structural and documentary requirements: layering, logging content,
       configuration being data.
   * - Analysis
     - Timing budgets, throughput, and coverage arguments.
   * - Test (simulated)
     - Anything exercisable against simulated drivers: command validation,
       limits, interlocks, state machines, workflows, fault handling. Most ICS
       requirements land here, and they run in CI.
   * - Test (hardware)
     - Requirements that depend on real device behaviour: driver correctness,
       timing against real controllers, end-to-end data path.
   * - Demonstration
     - Operational requirements verified by carrying out an observation.

Requirements verifiable by simulated test should be written so that they *are*
verifiable that way. A requirement phrased so that it can only be checked with
the full instrument at the telescope will be checked once, late, under
pressure.
