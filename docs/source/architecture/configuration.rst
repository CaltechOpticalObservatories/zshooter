Configuration
=============

Limits, named positions, modes, timeouts, readiness conditions, and safe states
are configuration data, not code. They are reviewable, diffable, and versioned
independently of a software release.

Defaults and overrides
----------------------

Configuration resolves in three layers, each overriding the one above:

.. list-table::
   :header-rows: 1
   :widths: 20 28 52

   * - Layer
     - Where
     - Contents
   * - **Defaults**
     - Shipped in the repository
     - Every value that has a sensible default: publication cadences,
       timeouts, retry policy, log destinations, readiness thresholds,
       simulation settings.
   * - **Instrument**
     - ``configs/``, versioned and reviewed
     - The values that are specific to this instrument and cannot be
       guessed: hard and soft limits, hardware topology, controller
       addresses, driver selection, named positions, interlock rules.
   * - **Deployment**
     - Per site or bench
     - Transport selection, peer addresses, host assignment, simulation
       flags.

Each daemon ships a **default configuration file** alongside its code, and the
code carries the same defaults as literals so it behaves sensibly even if that
file is missing. Instrument and deployment configuration supply only what
differs. A daemon's effective configuration is the merge, and the daemon
publishes what it actually resolved to.

The point of shipping defaults is that a daemon should start and be useful
with as little configuration as possible. A new motion daemon on the bench
needs its controller address and its limits, not fifty lines restating
cadences that are the same everywhere.

What must not be defaulted
~~~~~~~~~~~~~~~~~~~~~~~~~~

Two categories have no defaults, and a daemon refuses to start without them
rather than guessing:

- **Hard limits and safe-state definitions.** A guessed travel limit is worse
  than no limit, because it looks like protection. These live only in the
  instrument layer and cannot be overridden from below.
- **Hardware identity.** Controller addresses, bus node numbers, and device
  serial numbers. A daemon that defaults these will happily command the wrong
  device.

Everything else may be defaulted. Getting a publication cadence wrong costs a
graph; getting a limit wrong costs a mechanism.

Per-daemon configuration
------------------------

Each daemon loads one configuration document, merged over its shipped
defaults. Illustrative instrument-layer shape, carrying only what the defaults
cannot supply:

.. code-block:: yaml

   peer:
     group: zsvis
     scope: motion

   driver:
     kind: coo-ethercat
     interface: eth1          # hardware identity: no default
     # simulate: false        # defaulted

   # readiness conditions, publication cadences, and retry policy
   # all come from the shipped defaults unless overridden here.

   mechanisms:
     # The slit is a discrete selector, not a positioner: it has named
     # widths rather than a continuous range.
     slitwidth:
       node: 3                # hardware identity: no default
       kind: selector
       units: arcsec
       timeout_s: 30.0        # defaulted, overridden because motion is slow
       description: Slit width.
       positions:
         narrow: 0.30
         standard: 0.70
         wide: 1.00

     focusposition:
       node: 4
       units: mm
       hardmin: -12.0         # no default
       hardmax: 12.0          # no default
       softmin: -10.0
       softmax: 10.0
       engineeringmin: -12.0  # engineering-mode envelope
       engineeringmax: 12.0
       timeout_s: 45.0
       description: Pre-optics focus stage position.

     # The K-mirror tracks continuously from telescope state rather than
     # being positioned once, so it carries a rate limit as well as travel
     # limits.
     kmirrorangle:
       node: 5
       units: deg
       hardmin: -200.0
       hardmax: 200.0
       softmin: -195.0
       softmax: 195.0
       maxrate: 2.0
       description: K-mirror field de-rotation angle.

Validation
----------

The merged configuration is validated against a schema at daemon start. A
daemon that fails validation refuses to start rather than running on a
configuration it cannot make sense of.

Defaults are applied *before* validation, not as a fallback for values that
failed it. A missing cadence is filled in silently; a missing hard limit is a
startup failure. The difference is what makes shipped defaults safe.

Validation checks structure, and also the relationships that make limits
meaningful:

- ``hardmin <= softmin < softmax <= hardmax``
- engineering envelope within hard limits
- every named position within soft limits
- every ``FloatKeyword`` declares ``units``
- referenced driver kinds and controller nodes exist and are unique
- every value with no default is present

Provenance
----------

Every daemon publishes the identity of the configuration it is running:
file path, version, and content hash. Two daemons believed to be identically
configured can then be checked rather than assumed, and a night-log entry can
record what the instrument was actually configured as.

Configuration changes at the instrument and operational layers are made through
version control and reviewed. There is no path by which a limit changes without
a diff.
