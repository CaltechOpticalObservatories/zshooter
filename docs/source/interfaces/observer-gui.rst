Observer GUI
============

Audience and purpose
--------------------

The observer GUI is used by visiting and remote astronomers to carry out an
observing programme. Its users are expert astronomers but not instrument
experts, they may be using ZShooter for the first and only time, and they are
working at night under time pressure.

The design consequence: the GUI presents the instrument in terms of *what the
observer is trying to achieve*, not in terms of the instrument's mechanisms.
An observer selects an observing configuration; they do not position a
rotator.

Relationship to the backend
---------------------------

The observer GUI commands ``zsseq_obs`` and subscribes to published state from
every daemon. It does not command device daemons directly.

Routing observing commands through the sequencer is what makes the instrument
consistent: the sequencer knows which operations are permitted in the current
state, which may run in parallel, and which must be serialised. An observer
GUI that commanded mechanisms directly would have to reimplement all of that,
and would get it wrong differently from the sequencer.

.. mermaid::

   flowchart LR
       OBS["Observer GUI"] -->|commands| SEQ["zsseq_obs"]
       SEQ -->|commands| D["device daemons"]
       D -.->|PUB status, telemetry, events| OBS
       SEQ -.->|PUB sequence + instrument state| OBS

Content
-------

**Instrument state**: one unambiguous indicator of whether the instrument is
ready, and when it is not, *what specifically* is not ready and whether it is
being worked on. The most common question at the console is "why can't I
start?", and it should be answered on screen without a phone call.

**Target list**: import, edit, reorder, and insert targets. Because the
sequencer reads one target at a time, the pending portion remains editable
during an observation, including inserting a target of opportunity ahead of
the queue.

**Observing configuration**: channel selection, slit, filter, exposure
parameters, calibration selection, expressed as configurations rather than as
mechanism positions.

**Exposure progress**: what is exposing, elapsed and remaining time, readout
progress, and where the data went.

**Quicklook**: the most recent frame per active channel, enough to answer "did
that work?" without leaving the GUI.

**Messages**: a view onto the event stream, filtered to what an observer needs
to act on, and never the only place an event is recorded.

**Hard hat banner**: a persistent, unmissable indicator whenever any subsystem
is in engineering mode, naming the subsystem and who holds it. See
:doc:`hardhat-gui`.

Design rules
------------

- **Never the only copy of anything.** Every value displayed is published
  state. Closing the GUI loses nothing; opening a second one shows the same
  instrument.
- **Distinguish stale from current.** A GUI showing a value from a daemon that
  stopped publishing four minutes ago must say so. A frozen number that looks
  live is worse than a blank one.
- **Pre-validate, but never rely on it.** Disabling an out-of-range control is
  good practice; the daemon still validates. If the two disagree, the daemon
  is right.
- **Report rejection reasons verbatim.** The daemon's reason is specific;
  "command failed" is not. Do not paraphrase it into uselessness.
- **Match the observing workflow.** The layout follows the order of a night,
  not the structure of the daemon inventory.

Implementation
--------------

The observer GUI is a Qt application (PyQt or PySide), as are the hard hat GUI
and the AIT tooling. Remote observers reach it through a VNC session on the
control host.

Widgets that render keyword state are shared across all three surfaces rather
than written per GUI. A value shown in the observer GUI, the hard hat GUI, and
an AIT panel must agree on its units, its limits, and whether it is stale,
which it will not do if three people implement it three times. See ADR-0005 in
:doc:`../decisions/index`.
