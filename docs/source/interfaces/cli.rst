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

   $ libby show zsblue.motion.slitwidth
   zsblue.motion.slitwidth = 1.0 arcsec

   $ libby show zsblue.motion.is%
   zsblue.motion.isconnected   = True
   zsblue.motion.ismoving      = False
   zsblue.motion.isreferenced  = True

   $ libby modify zsblue.motion.slitwidth=0.7
   zsblue.motion.slitwidth = 0.7 arcsec

   $ libby describe zsnir.thermal.detectortemperature
   zsnir.thermal.detectortemperature:
     type         float
     readonly     True
     units        K
     description  nIR detector temperature.

   $ libby list zshk.vacuum.%
   zshk.vacuum.dewarpressure
   zshk.vacuum.ionpumpcurrent
   zshk.vacuum.ionpumpstate

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

It is subject to the same authority model as every other client: a CLI session
carries an identity and a role, and commands beyond that role are rejected.
Engineering operations from the CLI require engineering authority to be held
explicitly, exactly as in the hard hat GUI, and are logged and announced the
same way.

It is not an observing interface. Nominal observing goes through the sequencer,
because the sequencer holds the state knowledge that keeps a night consistent.
