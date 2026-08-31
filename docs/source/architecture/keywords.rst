Keywords and addressing
=======================

The instrument's entire control surface is a namespace of typed keywords. A
keyword is a named, typed value with metadata, served by exactly one daemon.
Reading instrument state, commanding a mechanism, and triggering an action are
all keyword operations.

This is what lets one CLI, one GUI framework, and one sequencer work against
every daemon without per-daemon client code.

Addressing
----------

.. code-block:: text

   <group>.<scope>.<name>
      │       │       └── keyword served by that daemon
      │       └────────── daemon scope: the hardware ownership boundary
      └────────────────── group: the instrument subsystem

The Libby peer identity is ``<group>_<scope>``; the keyword address is
``<group>.<scope>.<name>``. Examples:

.. code-block:: text

   zsblue.motion.slitwidth
   zsblue.motion.focusposition
   zsnir.thermal.detectortemperature
   zshk.vacuum.dewarpressure
   zscal.lamps.arclampstate
   zsseq.obs.sequencestate

Naming rules
------------

- Lowercase throughout. No underscores inside a name segment: Libby's ``%``
  wildcard matches within a segment, and consistent unbroken names make
  wildcard queries predictable (``libby show zsblue.motion.is%``).
- Groups are the subsystem prefixes fixed in :doc:`../inventory/daemons`:
  ``zsimg``, ``zsnir``, ``zsblue``, ``zsred``, ``zscal``, ``zscam``, ``zshk``,
  ``zskeck``, ``zsseq``.
- Names are stable. A keyword name is an interface; renaming one breaks the
  GUI, the sequencer, scripts, and the night log.
- Names carry no routing information. ``group`` and ``scope`` already say where
  the keyword lives.
- Where a daemon owns several mechanisms, the mechanism is part of the name:
  ``zsimg.motion.rotuposition``, ``zsimg.motion.rotvposition``.

Keyword types
-------------

Libby provides five keyword types. Every ZShooter keyword is one of them:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Use
   * - ``BoolKeyword``
     - Binary state and predicates: ``isconnected``, ``isreferenced``,
       ``ismoving``, ``isinposition``.
   * - ``IntKeyword``
     - Counts and discrete indices: ``filterslot``, ``exposurecount``.
   * - ``FloatKeyword``
     - Physical quantities: positions, temperatures, pressures, times.
       Always carries ``units``.
   * - ``StringKeyword``
     - Names and enumerated states: ``daemonstate``, ``mode``, ``filtername``,
       ``faultreason``.
   * - ``TriggerKeyword``
     - Actions with no value: ``halt``, ``home``, ``abort``, ``recover``.

Access mode is inferred from what is supplied: a getter alone makes the keyword
read-only, a setter alone write-only, both read-write.

Required metadata
-----------------

Every ZShooter keyword must declare:

- ``description``: one line, written for a support astronomer at 3 a.m.
- ``units``: mandatory on every ``FloatKeyword``. A dimensioned number
  without units on the bus is a defect.
- ``timeout_s``: on any keyword whose modify is slow. The CLI and GUIs read
  this from ``keys.describe`` to size their own timeouts, so a stage move that
  takes 40 seconds must advertise it or clients will time out prematurely.
- ``validator``: wherever a value range or discrete set is known. This is the
  first line of the safety chain described in :doc:`safety`.

Standard keywords
-----------------

Every ZShooter daemon serves this set, so that generic clients (the status
panel, the watchdog, the night-log recorder) work against any daemon without
special-casing.

.. list-table::
   :header-rows: 1
   :widths: 22 12 66

   * - Keyword
     - Type
     - Meaning
   * - ``daemonstate``
     - string
     - Daemon lifecycle state (see :doc:`state-models`).
   * - ``mode``
     - string
     - Active operating mode, including ``engineering`` and ``simulation``.
   * - ``isconnected``
     - bool
     - Driver is connected to its hardware.
   * - ``isready``
     - bool
     - Daemon is ready for nominal observing operations.
   * - ``isfaulted``
     - bool
     - A fault is active.
   * - ``faultreason``
     - string
     - Human-readable description of the active fault; empty when healthy.
   * - ``heartbeat``
     - float
     - Timestamp of the last liveness publication.
   * - ``lastcommand``
     - string
     - Key of the most recent command.
   * - ``lastresult``
     - string
     - Outcome of the most recent command.
   * - ``owner``
     - string
     - Current command authority holder (see :doc:`authority`).
   * - ``halt``
     - trigger
     - Stop activity and hold safely. Always accepted, in every state.
   * - ``safe``
     - trigger
     - Enter the daemon's defined safe state.
   * - ``recover``
     - trigger
     - Explicit recovery from fault state.

``halt`` is special: it must be accepted unconditionally, including while the
daemon is busy, faulted, or owned by another client. It is the one command that
never fails validation.

Motion daemons additionally serve, per mechanism: ``<mech>position``,
``<mech>target``, ``<mech>softmin``, ``<mech>softmax``, ``<mech>hardmin``,
``<mech>hardmax``, ``<mech>ismoving``, ``<mech>isreferenced``,
``<mech>home``.

Discovery
---------

Libby auto-registers two meta-services on every peer:

- ``keys.list``: enumerate keyword names, with ``%`` wildcards.
- ``keys.describe``: full metadata for one keyword.

These make the instrument self-describing. The hard hat GUI builds its
engineering panels from ``keys.describe`` rather than from hand-maintained
per-daemon layouts, and the FITS header writer can be driven from the same
metadata.

.. note:: **TBC: keyword catalogue**

   The complete per-daemon keyword catalogue is not yet written. It should be
   generated from the daemon configuration schemas rather than maintained by
   hand, and it depends on the mechanism list being finalised against the
   L1/L2/L3 requirements.
