Command line
============

The ``libby`` CLI is the third client, and the one that needs no ZShooter code
at all: because every daemon exposes typed keywords with discoverable
metadata, the generic Libby CLI already speaks to the whole instrument.

Verbs
-----

.. code-block:: text

   libby show     <group>.<scope>.<name>      # read (% wildcards in name)
   libby modify   <group>.<scope>.<name>=V    # write (exact name)
   libby list     <group>.<scope>.<pattern>   # enumerate keywords
   libby describe <group>.<scope>.<name>      # metadata for one keyword

Against ZShooter:

.. code-block:: console

   $ libby show zsvis.motion.slitwidth
   zsvis.motion.slitwidth = 1.0 arcsec

   $ libby show zsvis.motion.is%
   zsvis.motion.isconnected   = True
   zsvis.motion.ismoving      = False
   zsvis.motion.isreferenced  = True

   $ libby modify zsvis.motion.slitwidth=0.7
   zsvis.motion.slitwidth = 0.7 arcsec

   $ libby describe zshouse.thermal.detectortemperature
   zshouse.thermal.detectortemperature:
     type         float
     readonly     True
     units        K
     description  nIR detector temperature.

   $ libby list zshouse.vacuum.%
   zshouse.vacuum.dewarpressure
   zshouse.vacuum.ionpumpcurrent
   zshouse.vacuum.ionpumpstate

``--json`` on any verb gives machine-readable output, which is what makes the
CLI usable from shell scripts and from the night-log tooling.

Timeouts
--------

The CLI reads ``timeout_s`` from ``keys.describe`` before issuing a modify, so
slow operations get an appropriately long wait automatically. This is why
:doc:`../architecture/keywords` requires every slow keyword to advertise it: a
40-second stage move with no declared timeout will appear to fail from the
command line while succeeding in the hardware.

Configuration
-------------

The CLI reads ``~/.libby/cli_config.yaml`` for transport and peer addressing.
ZShooter ships site configurations for the ``sim``, ``lab``, and ``summit``
environments so that an engineer switching context changes one file rather than
remembering addresses.

Use and limits of use
---------------------

The CLI is the right tool for scripted engineering procedures, for
commissioning measurements, for CI checks against a simulated instrument, and
for the fastest possible answer to "what is that value right now".

Like every other client it reaches daemons through the same keywords and the
same validation, and its commands are logged the same way. It is expected to
be used by someone who knows what the keyword they are writing does.

It is not an observing interface. Nominal observing goes through the sequencer,
because the sequencer holds the state knowledge that keeps a night consistent.
