"""Configuration loading and validation.

Configuration resolves in four layers (instrument, deployment, operational, and
session) and is validated against a schema at daemon start. A daemon that
fails validation refuses to start rather than starting with defaults.

See ``docs/source/architecture/configuration.rst``.
"""
