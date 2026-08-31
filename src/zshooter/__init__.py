"""ZShooter instrument control software.

The reusable library behind the ZShooter ICS. Deployable daemons live in
``daemons/`` at the repository root and stay thin: they wire configuration to a
driver, register keywords, and serve. Behaviour worth testing lives here, where
it can be tested without starting a process.

See ``docs/source/architecture/layers.rst`` for the layer model this package
implements.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("zshooter")
except PackageNotFoundError:  # not installed, e.g. running from a source tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
