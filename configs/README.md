# Configuration

Per-daemon configuration, versioned and reviewed. Limits, named positions,
modes, timeouts, readiness conditions, and safe states are data here, not code
in `src/`.

Configuration resolves in four layers, each overriding the one above:

| Layer | Changes | Contents |
|---|---|---|
| `instrument/` | Rarely, under review | Hard limits, hardware topology, controller addresses, driver selection, safe states, interlocks |
| `deployment/` | Per site or bench | Transport, peer addresses, host assignment, log destinations, simulation flags |
| `operational/` | Per observing run | Soft limits, named positions, default exposure parameters, calibration presets, readiness thresholds |
| `session/` | Per night, auto-reset | Operator overrides of the values marked user-editable |

Hard limits live only in the instrument layer and cannot be overridden from
below. This is enforced at load time, not by convention.

See [`docs/source/architecture/configuration.rst`](../docs/source/architecture/configuration.rst).
