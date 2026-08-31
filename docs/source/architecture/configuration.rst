Configuration
=============

Limits, named positions, modes, timeouts, readiness conditions, and safe states
are configuration data, not code. They are reviewable, diffable, and versioned
independently of a software release.

Layers
------

Configuration resolves in four layers, each overriding the one above:

.. list-table::
   :header-rows: 1
   :widths: 22 30 48

   * - Layer
     - Changes
     - Contents
   * - **Instrument**
     - Rarely, under review
     - Hard limits, hardware topology, controller addresses, driver
       selection, safe-state definitions, interlock rules.
   * - **Deployment**
     - Per site or bench
     - Transport selection, peer addresses, host assignment, log
       destinations, simulation flags.
   * - **Operational**
     - Per observing run
     - Soft limits, named positions, default exposure parameters, calibration
       presets, readiness thresholds.
   * - **Session**
     - Per night, resets automatically
     - Operator overrides of the small set of values marked user-editable.

Session overrides reset at the UTC date boundary, so every observer starts from
a known configuration rather than inheriting the previous night's adjustments.

Hard limits live only in the instrument layer and cannot be overridden by any
layer below it. This is enforced at load time, not by convention.

Per-daemon configuration
------------------------

Each daemon loads one configuration document. Illustrative shape:

.. code-block:: yaml

   peer:
     group: zsblue
     scope: motion
     transport: rabbitmq

   driver:
     kind: coo-ethercat
     interface: eth1
     simulate: false

   readiness:
     - all_mechanisms_referenced
     - no_active_faults

   mechanisms:
     slitwidth:
       node: 3
       units: arcsec
       hardmin: 0.0
       hardmax: 12.0
       softmin: 0.3
       softmax: 10.0
       engineeringmin: 0.0      # hard hat envelope
       engineeringmax: 12.0
       timeout_s: 30.0
       description: Slit width.
       named:
         narrow: 0.7
         standard: 1.0
         wide: 5.0

     focusposition:
       node: 4
       units: mm
       hardmin: -12.0
       hardmax: 12.0
       softmin: -10.0
       softmax: 10.0
       timeout_s: 45.0
       description: Collimator focus stage position.

Validation
----------

Configuration is validated against a schema at daemon start, and a daemon that
fails validation refuses to start rather than starting with defaults. Starting
with a silently-defaulted soft limit is the failure mode this rule exists to
prevent.

Validation checks structure, and also the relationships that make limits
meaningful:

- ``hardmin <= softmin < softmax <= hardmax``
- engineering envelope within hard limits
- every named position within soft limits
- every ``FloatKeyword`` declares ``units``
- every mechanism declares ``timeout_s``
- referenced driver kinds and controller nodes exist and are unique

Provenance
----------

Every daemon publishes the identity of the configuration it is running:
file path, version, and content hash. Two daemons believed to be identically
configured can then be checked rather than assumed, and a night-log entry can
record what the instrument was actually configured as.

Configuration changes at the instrument and operational layers are made through
version control and reviewed. There is no path by which a limit changes without
a diff.
