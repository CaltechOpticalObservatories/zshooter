ZShooter Instrument Control Software
====================================

This is the design documentation for the ZShooter Instrument Control System
(ICS): the software that commands the instrument's mechanisms, detectors,
calibration hardware, and support infrastructure, and that presents the
instrument to observers and engineers.

ZShooter's ICS conforms to the Caltech Optical Observatories `ICS architecture
<https://github.com/CaltechOpticalObservatories/ics-architecture>`_, which
defines the minimum command-and-control spine shared by COO instruments. This
documentation is the ZShooter-specific expansion of that specification: it
names the concrete daemons, drivers, keywords, modes, safety rules, and
workflows that the general specification deliberately leaves open.

.. note::

   The ICS is in the **design phase**. No implementation scaffolding exists
   yet. These documents define what will be built and are expected to change
   as the requirements baseline and hardware controller topology firm up.
   Sections carrying open questions are marked with ``TBC``.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   overview
   architecture/index
   inventory/index
   interfaces/index
   operations/index
   development/index
   decisions/index
