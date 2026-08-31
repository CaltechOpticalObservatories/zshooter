# ZShooter ICS

Instrument control software for **ZShooter**, a multi-channel imaging
spectrograph: an imaging channel (ZImager) and three spectroscopic channels
(ZSpec nIR, Blue, Red), with shared calibration, thermal, vacuum, power, and
telescope-interface infrastructure.

The ICS conforms to the COO
[ICS architecture](https://github.com/CaltechOpticalObservatories/ics-architecture)
and uses [Libby](https://github.com/CaltechOpticalObservatories/libby) for all
daemon-to-daemon messaging.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Extras: `daemon` (Libby messaging, installs from git), `docs` (Sphinx),
`dev` (pytest, ruff).

## Build the docs

```bash
pip install -e ".[docs]"
make -C docs html
open docs/build/html/index.html
```

## Test

```bash
pytest                 # everything except hardware tests
pytest -m daemon       # one test level
pytest --cov           # with coverage
pytest -m hardware     # requires real devices; deselected by default
```

Levels are selected with markers: unmarked (unit), `daemon`, `integration`,
`interface`, `hardware`. See
[docs/source/development/testing.rst](docs/source/development/testing.rst).

## CI and releases

CI runs lint, tests on Python 3.11-3.13, a `-W` docs build, and a distribution
build on every PR. Tagging is the release mechanism: `setuptools-scm` derives
the version from the git tag, so `git tag -a v1.2.0` produces version `1.2.0`
and there is no version string to edit.

```bash
pre-commit install     # run the same lint rules locally
```

See [ci.rst](docs/source/development/ci.rst) and
[releases.rst](docs/source/development/releases.rst).
