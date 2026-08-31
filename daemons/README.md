# Daemons

Deployable runtime daemons, one directory per `<group>/<scope>`. A daemon's
directory path is its address: `daemons/zsblue/motion/` serves peer
`zsblue_motion` and keywords `zsblue.motion.*`.

Daemons stay thin. A daemon module wires configuration to a driver, registers
keywords, and calls `serve()`. Behaviour worth testing lives in
`src/zshooter/`, where it can be tested without starting a process.

Planned groups:

| Group | Domain |
|---|---|
| `zsimg` | ZImager channel |
| `zsnir` | ZSpec nIR channel |
| `zsblue` | ZSpec Blue arm |
| `zsred` | ZSpec Red arm |
| `zscam` | Detector controllers |
| `zscal` | Calibration and lightpath |
| `zshk` | Housekeeping and infrastructure |
| `zskeck` | Gateways to WMKO domains (TCS, MAGIQ) |
| `zsseq` | Sequencing and coordination |

The daemon inventory is provisional pending confirmation against the as-built
electronics design and the L1/L2/L3 requirements baseline. See
[`docs/source/inventory/daemons.rst`](../docs/source/inventory/daemons.rst).
