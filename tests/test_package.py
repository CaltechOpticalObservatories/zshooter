"""Smoke tests for the package skeleton.

These assert that the installed package matches the layer model documented in
``docs/source/architecture/layers.rst``. They are deliberately shallow, since
there is nothing to test yet beyond the structure, but they fail loudly if a
subpackage is renamed or dropped without the documentation following.
"""

import importlib

import pytest

SUBPACKAGES = [
    "algorithms",
    "config",
    "daemon",
    "devices",
    "driver",
    "models",
    "procedures",
    "telemetry",
]


def test_version_is_available():
    import zshooter

    assert isinstance(zshooter.__version__, str)
    assert zshooter.__version__


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports(name):
    module = importlib.import_module(f"zshooter.{name}")
    assert module.__doc__, f"zshooter.{name} should document what belongs in it"
