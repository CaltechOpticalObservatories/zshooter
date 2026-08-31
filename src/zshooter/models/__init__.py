"""Shared state, command, and result types.

The vocabulary every layer agrees on: daemon and command lifecycle states,
command results, fault descriptions, and limit sets. Defined once here so that
daemons, procedures, and clients cannot drift apart on what a state means.
"""
