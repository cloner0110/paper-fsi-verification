# Hessenthaler Phase I on the rF fluid meshes (Section `sec:hessenthaler`)

Data behind Tables `tab:hessenthaler_results` and `tab:hessenthaler_validation`.

## Files

- `hv_pfv_summary.csv`: per run, tip u_y window statistics (t = 40-45, 20-25, 5-10 s), centreline
  deviation from MRI, voxel velocity difference, coupling iterations per step. `QM_B` rows are the
  quasi-monolithic levels 1-3 of the companion paper (paper-monolithic-fsi
  `paper-data/hessenthaler/summary.csv`, rounded).
- `hv_pfv_differences.csv`: differences between meshes, between interface pressure conditions and
  against the quasi-monolithic solutions.

Both are copied unchanged from the analysis directory `claude-runs/hv-analysis/` (20 Nov 2026), whose
README gives the commands.

## Runs (UCD Sonic, `/scratch/pcardiff/hv/`, read only)

| Run | Interface pressure | Fluid cells | Ranks | Wall time (t = 0-45 s) |
|---|---|---|---|---|
| `P_rF0_LUST_b02_mwp` | `movingWallPressure` | 122 435 | 24 | 51 792 s |
| `P_rF1_LUST_b02_mwp` | `movingWallPressure` | 312 180 | 24 | 66 835 s |
| `P_rF2_LUST_b02_mwp` | `movingWallPressure` | 832 552 | 48 | running (t = 34 on 20 Nov 2026) |
| `P_rF0_LUST_b02` | `zeroGradient` | 122 435 | 24 | 52 360 s |
| `P_rF1_LUST_b02` | `zeroGradient` | 312 180 | 24 | 30 259 s |
| `P_rF2_LUST_b02` | `zeroGradient` | 832 552 | 48 | 133 556 s |

Wall times are the final `ClockTime` of `log.solids4Foam` (one segment per run, no restarts).

Build: OpenFOAM v2512 (`_87ed40d256-20251219`), solids4foam `206437983` (#671 merge) + PR #676
(outlet BC), user build `64896b0a5`, GCC 11.5.0 `-O3`, `linux64GccDPInt32Opt`.

The six cases differ only in `0/fluid/p` on the `interface` patch (checked with `diff` over
`system/`, `constant/` and `0/`); the meshes of the two runs on each level are identical (md5 of
`points`). Set-up read from the run directories:

- `controlDict`: deltaT 0.002, endTime 45; inflow and solid body force ramped with `3s^2 - 2s^3`
  over 0.5 s.
- `fsiProperties`: IQNILS, couplingReuse 2, predictor and predictSolid yes, relaxationFactor 0.05,
  outerCorrTolerance 1e-4, requireAllResidualMeasures yes (strict test), nOuterCorr 60,
  allowUnconvergedCoupling yes, AMI transfer.
- fluid: `pimpleFluid`, `backward`, nOuterCorrectors 20, nCorrectors 3, nNonOrthogonalCorrectors 1,
  residualControl U and p 1e-5; `leastSquares` gradients, `Gauss LUST grad(U)`; mesh motion
  `velocityLaplacian`, `quadratic inverseDistance (interface)`.
- outlet: p fixedValue 0, U `backflowStabilisedOutletVelocity` beta 0.2; interface U
  `newMovingWallVelocity`.
- solid: `nonLinearGeometryTotalLagrangianTotalDisplacement`, neoHookeanElastic mu 64200 Pa,
  K 620600 Pa (nu = 0.45), rho 1058.3; PETSc SNES (newtonls, snes_rtol 1e-6); `backward`;
  blockMesh 12 x 8 x 65.

Meshes: cfMesh `cartesianMesh` from `constant/triSurface/fluidDomain.fms` with `system/meshDict` of
each run: maxCellSize / boundaryCellSize / interface localRefinement (thickness 1.5 mm) and
`tipSweep` box / `flapSweep` box = 5.657 / 2.857 / 0.714 / 1.428 mm (rF0), 4.00 / 2.02 / 0.505 /
1.01 mm (rF1), 2.828 / 1.428 / 0.357 / 0.714 mm (rF2); a `merging` box (78 x 78 x 160 mm, centre
z = 50 mm) at boundaryCellSize. `checkMesh` (v2512, local copies): maximum non-orthogonality 39.5°,
37.5°, 37.3°; all `Mesh OK`. Job-script comment: "R1 recipe: shifted octree, tip-path box, 1.5 mm
interface band; strict checkMesh OK".

## Notes

- The tip of rF0 and rF1 wanders by 0.1-0.2 mm peak to peak over t = 25-45 s (both conditions);
  only zeroGradient rF2 settles monotonically.
- zeroGradient rF2 reaches nOuterCorr = 60 in 441 steps from t = 36.9 s (residual about 2e-4
  against 1e-4); the tip is steady to 1e-4 mm.
- Apparent order of the zeroGradient sequence (Celik form, r = 1.366, 1.387): 5.6.
