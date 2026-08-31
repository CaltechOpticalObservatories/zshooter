"""Per-device-class control logic and state models.

One module per class of device (motion axis, temperature loop, cryocooler,
vacuum gauge, lamp, or detector) holding the logic that is shared by every daemon
owning that kind of hardware. Device modules use drivers; they do not talk to
hardware directly.
"""
