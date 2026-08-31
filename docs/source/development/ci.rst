Continuous integration
======================

CI runs on every push to ``main``, every pull request, and every tag. It is
defined in ``.github/workflows/``.

.. mermaid::

   flowchart LR
       PR["Pull request"] --> L["Lint<br/>ruff check + format"]
       PR --> T["Test<br/>py3.11 / 3.12 / 3.13"]
       PR --> D["Docs<br/>sphinx -W"]
       PR --> B["Build<br/>sdist + wheel"]

       L --> G{"All green?"}
       T --> G
       D --> G
       B --> G

       G -- no --> X["Blocked"]
       G -- yes --> M["Merge to main"]

       M --> PAGES["Publish docs<br/>to GitHub Pages"]
       M --> TAG["Tag vX.Y.Z"]
       TAG --> REL["Build + GitHub release"]

Workflows
---------

.. list-table::
   :header-rows: 1
   :widths: 24 22 54

   * - Workflow
     - Trigger
     - Does
   * - ``ci.yml``
     - PR, push to ``main``, tags
     - Lint, test across three Python versions, build the docs, build the
       distribution.
   * - ``docs.yml``
     - Push to ``main``
     - Rebuilds and publishes documentation to GitHub Pages.
   * - ``release.yml``
     - Tag ``v*``
     - Builds sdist and wheel, verifies the version matches the tag, creates a
       GitHub release. See :doc:`releases`.
   * - ``update-submodules.yml``
     - Weekly, or manual
     - Opens a PR when a pinned driver submodule moves upstream.

Jobs
----

**Lint.** ``ruff check`` and ``ruff format --check`` over ``src`` and
``tests``. Formatting is checked, not applied, so CI never disagrees with what
is committed.

**Test.** The full suite except hardware, on Python 3.11, 3.12, and 3.13, with
coverage. The matrix is not decoration: the summit hosts and developer laptops
will not run the same Python for the whole life of the instrument.

The checkout uses ``fetch-depth: 0``. setuptools-scm derives the version from
git history, and a shallow clone silently produces a wrong version, which would
then mask exactly the tag problems ``release.yml`` exists to catch.

**Docs.** Built with ``-W --keep-going``, so a Sphinx warning fails the build.
A broken cross-reference or a document missing from a toctree is a defect,
caught on the PR that introduced it rather than discovered months later.
``linkcheck`` also runs but does not fail the build, because external sites go
down for reasons that have nothing to do with this repository.

**Build.** ``python -m build`` plus ``twine check``, so packaging problems
surface on every PR rather than at the moment someone is trying to cut a
release.

Merge requirements
------------------

A pull request should not merge unless lint, test, docs, and build are all
green. Configure this as branch protection on ``main``: CI that can be
bypassed by clicking merge is advisory, not a gate.

Local checks
------------

``.pre-commit-config.yaml`` runs the same lint and formatting rules locally,
plus whitespace, YAML, and TOML checks:

.. code-block:: console

   $ pip install pre-commit
   $ pre-commit install
   $ pre-commit run --all-files      # first time, or after changing the config

To reproduce a CI run before pushing:

.. code-block:: console

   $ ruff check src tests && ruff format --check src tests
   $ pytest --cov
   $ python -m sphinx -W --keep-going -b html docs/source docs/build/html
   $ python -m build

What CI cannot catch
--------------------

This matters more for instrument software than for a library, and it should not
be inferred from a green badge:

- **Real device behaviour.** EtherCAT bus timing, controller-specific error
  codes, detector readout, vendor firmware quirks. Simulated drivers model what
  we *believe* devices do.
- **Real timing under load.** Several daemons commanding a shared bus while a
  detector reads out.
- **Hardware topology mistakes.** The daemon-to-controller mapping in
  :doc:`../inventory/daemons` is provisional; CI cannot tell that two
  mechanisms which the configuration says are on separate buses are physically
  on one.
- **Interactions with WMKO systems.** The Keck 1 telescope interface is a
  client of observatory services that cannot be exercised from CI.

Hardware test campaigns cover this ground, and they, not CI, are the gate for
summit deployment. CI's job is to guarantee that a version reaching the bench is
worth the bench time.
