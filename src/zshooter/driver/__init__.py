"""Vendor drivers.

A driver speaks one vendor's protocol and nothing else: no instrument state, no
message bus, no limit checking beyond what the device itself imposes. Each
driver ships a simulated implementation of the same API, selected by
configuration.

Most ZShooter drivers are shared COO packages consumed as git submodules,
following the HISPEC arrangement. See ``docs/source/inventory/drivers.rst`` for
the inventory and ``docs/source/operations/simulation.rst`` for the simulation
contract.
"""
