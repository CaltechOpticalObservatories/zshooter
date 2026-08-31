Releases and deployment
=======================

Versioning
----------

The version comes from the git tag. ``setuptools-scm`` derives it from history,
so there is no version string in the source to edit and no way for the tag and
the package to disagree.

.. code-block:: console

   $ git tag -a v1.2.0 -m "ZShooter ICS 1.2.0"
   $ git push origin v1.2.0

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Git state
     - Version
     - Meaning
   * - Tagged ``v1.2.0``
     - ``1.2.0``
     - A release. Deployable.
   * - After the tag
     - ``1.2.1.dev4+g8a3f21c``
     - Development build. Never deployed to the summit.
   * - Uncommitted changes
     - ``…+g8a3f21c.d20260830``
     - Dirty tree. The ``.d`` suffix is the giveaway.

Tag scheme
~~~~~~~~~~

``vMAJOR.MINOR.PATCH``, with ``rc`` suffixes for candidates
(``v1.2.0rc1``). Release candidates are marked as pre-releases automatically
and are for bench qualification, never for a scheduled observing run.

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Bump
     - When
   * - MAJOR
     - A change requiring coordinated action: a message envelope version
       change, a keyword rename, a configuration schema change that existing
       config files will not satisfy.
   * - MINOR
     - New capability, backward compatible. New daemons, new keywords, new
       workflows.
   * - PATCH
     - Fixes only. No new keywords, no config schema change.

Keyword names and the message envelope are interfaces. Renaming a keyword
breaks the GUI, the sequencer, engineering scripts, and the night log, so it is
a MAJOR change even when it looks cosmetic.

What ``release.yml`` does
-------------------------

On a ``v*`` tag: builds the sdist and wheel, runs ``twine check``, **verifies
the installed version matches the tag**, and creates a GitHub release with the
artefacts attached.

The version check guards against a tag applied to a dirty tree or a malformed
tag name: cases where the artefact would be labelled differently from what
anyone believes was released.

Deployment
----------

A deployment is a **pair**: a code version and a configuration version. Both
are versioned, both are recorded, and both must be independently
rollback-able.

This matters because most changes at an instrument are configuration changes (a
soft limit, a named position, a readiness threshold), and treating them as
untracked would make the most frequently changed part of the system the least
auditable part. Every daemon publishes the identity of the configuration it is
running (see :doc:`../architecture/configuration`), so what is deployed can be
verified rather than assumed.

Promotion
~~~~~~~~~

.. mermaid::

   flowchart LR
       T["Tag vX.Y.Z"] --> S["<b>sim</b><br/>full suite in CI"]
       S --> L["<b>lab</b><br/>hardware tests<br/>per subsystem"]
       L --> P["<b>summit</b><br/>production"]

       L -. "failures" .-> F["Fix, retag"]
       F --> S

The **same artefact** is promoted through the three environments described in
:doc:`../inventory/deployment`. It is not rebuilt per environment. A rebuild is
a different artefact, and then the thing that was qualified is not the thing
that was deployed.

Environments differ only in the deployment configuration layer.

Deployment windows
~~~~~~~~~~~~~~~~~~

- **Never during a night.** Not between targets, not "just the housekeeping
  daemon".
- **Not the day before a scheduled run**, for anything beyond a PATCH. A
  deployment needs a day of operation behind it before it is trusted with
  telescope time.
- **Daytime, with an engineer present**, and with the instrument in
  ``maintenance`` or ``safe`` mode.

Not every deployment is instrument-wide. Daemons restart individually, so a
fix to one daemon can be deployed alone. The exception is a **message envelope
version change**, which is a flag day: every peer must be updated together,
because peers on different envelope versions cannot talk. This is why an
envelope change is a MAJOR bump.

Rollback
~~~~~~~~

**Roll back first, diagnose afterwards.** At night, the question is not "why
did this break" but "how quickly can the instrument observe again". Diagnosis
happens the next day, from the telemetry and command log, which are still there.

Rollback must therefore be:

- **Faster than diagnosis**: a version change and a daemon restart, not a
  rebuild;
- **Available for configuration independently of code**, since a bad limit is
  more likely than a bad release;
- **Rehearsed.** A rollback path first attempted during a failure is not a
  rollback path.

Release checklist
-----------------

.. list-table::
   :header-rows: 1
   :widths: 8 92

   * - ✓
     - Step
   * - ☐
     - CI green on ``main``: lint, tests on all three Python versions, docs,
       build.
   * - ☐
     - Hardware tests run on the bench for every subsystem the release
       touches, results recorded against the candidate version.
   * - ☐
     - Configuration schema changes, if any, have a migration path for existing
       config files.
   * - ☐
     - Keyword additions or renames reviewed against the GUIs, the sequencer,
       and engineering scripts.
   * - ☐
     - Documentation updated in the same PR as the change, particularly
       :doc:`../inventory/daemons` and :doc:`../architecture/keywords`.
   * - ☐
     - Version bump level agreed (MAJOR / MINOR / PATCH) against the rules
       above.
   * - ☐
     - Tag pushed; ``release.yml`` green; artefacts attached to the release.
   * - ☐
     - Deployment window agreed with the instrument scientist and scheduled
       outside observing.
   * - ☐
     - Rollback target identified: the specific previous code and configuration
       versions to return to.

.. note:: **TBC: deployment tooling**

   HISPEC deploys with Ansible (``ansible/`` with roles and inventory), which
   would suit ZShooter's multi-host layout and gives the same promotion path
   across ``sim``, ``lab``, and ``summit``. This should be settled alongside
   the host allocation in :doc:`../inventory/deployment`, and the choice needs
   to cover configuration deployment and rollback, not only code.
