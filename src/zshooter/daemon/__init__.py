"""Daemon base classes and conventions.

ZShooter daemons subclass Libby's ``LibbyDaemon``. This package holds what
every ZShooter daemon shares on top of it: the standard keyword set, the daemon
lifecycle state machine, the command validation chain, ownership and authority
enforcement, and safe-state handling.

See ``docs/source/architecture/state-models.rst`` and
``docs/source/architecture/authority.rst``.
"""
