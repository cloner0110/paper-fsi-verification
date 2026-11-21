# Manufactured FSI solution: results and provenance

This folder supports Section "Manufactured solution for transient ALE FSI with a finite-strain solid" (`sec:mms_fsi`, Table `tab:mms_fsi`) and Appendix `app:mms` of the paper.

**Not yet here:**

- the sympy/symengine derivation (`mms_fsi.py`), the C++ code generator, the independent checks of the generated code (`check_generated.C`), the solids4foam case library (sources, exact boundary conditions, error function object) and the case generator (`makeCase.py`).
- These are waiting for agreement on their packaging, and will be added here (or to solids4foam) later. Until then they are in the working directory `claude-runs/mms-fsi/` (`derive/`, `case/`) on the Mac used for the runs.

## Problem and runs

- 2-D channel with a compressible neo-Hookean wall (plane strain), closed-form manufactured solution with exact kinematic and traction continuity; see Appendix `app:mms`.
- **Full variant:** tilting, travelling, tangentially stretching interface. **Flat variant:** the interface stays flat and moves only vertically.
- Meshes: fluid n × n/2, solid n × n/4, square cells, n = 16, 32, 64, 128 faces on the interface. Combined refinement Δt = 0.32/n (0.02 to 0.0025). Run to t = 0.4.
- Errors are logged every step by the case's error function object:
  - `U_L2`, `p_L2`: volume-weighted RMS of |U − U_exact| and |p − p_exact| at the fluid cell centres, on the moving mesh (pressure not mean-corrected; the outlet fixes the level).
  - `D_L2`, `Us_L2`: solid displacement and velocity on the reference mesh.
  - `intD_L2`, `intTrac_L2`: face-area-weighted RMS of the interface displacement and of the traction applied to the solid, against the exact traction, on the solid interface.
  - `intP_L2`: fluid interface pressure. `*_L1`, `*_Linf` as named.
- Codes: OpenFOAM-v2512, macOS (arm64), local solids4foam worktree (branch `mms-fsi/qm`, later `mms-fsi/item4`; the quasi-monolithic source-term support has since been merged into solids4foam).
  - The partitioned n16–n64 runs used commit 4071b431e and the n128 runs commit 677865f55. The source changes between the two touch only the quasi-monolithic fluid, solid and coupling (`newtonIcoFluid`, `nonLinGeomTotalLagVelocitySolid`, `newtonQuasiMonolithicCouplingInterface`), not `pimpleFluid`, the displacement solid or the partitioned couplings.
  - The case files of n128 differ from n64 only in the block divisions and Δt (checked with `diff -r`).
- Couplings:
  - `aitken_full`: Dirichlet–Neumann, Aitken, `newMovingWallVelocity` + `fixedFluxPressure` on the interface.
  - `robin_full`: Robin–Neumann (`fixedRelaxation`, factor 1; `elasticWallVelocity` + `elasticWallPressure`).
  - Both: tolerance 1e-6 with the legacy (min) test, at most 200 iterations. At acceptance r1 ≈ 1e-4 (Aitken) and ≈ 1e-6 (Robin–Neumann).
  - `qm_full`, `qm_flat`: quasi-monolithic coupling of the companion paper (same meshes, mesh motion and Δt).
- A/B on Aitken, full variant, n16–n64 (2026-11-21):
  - `aitken_full_ab_S`: `flux(HbyA) skewCorrected linear`.
  - `aitken_full_ab_SM`: S + `movingWallPressure` on the interface.
  - `aitken_full_ab_SW`: S + the exact pressure gradient on the bottom wall.
  - None changes the fluid U/p orders. S raises the interface traction order (n32 to n64) from 1.41 to 1.61.

## Files

| File | Content | Origin |
|---|---|---|
| `summary_errors_t0.2_t0.4.csv` | L2 (and U, p L∞) errors at t = 0.2 and 0.4 for every series and level; the numbers of Table `tab:mms_fsi` | `make_csv.py` |
| `coupling_iterations.csv` | coupling iterations per step (mean, max) for the partitioned runs | `make_csv.py`, from `postProcessing/fsiResiduals.dat` |
| `errors_csv/<series>_n<n>.csv` | the full error history (every time step) of each run | `make_csv.py`, from `postProcessing/mmsFsiErrors/errors.dat` |
| `order_tables/{aitken,robin}_full_n16-n128.md` | four-level order tables of the partitioned runs, t = 0.2 and 0.4 | `case/orders.py <n16> <n32> <n64> <n128> --times 0.2 0.4` |
| `order_tables/aitken_full_ab_*.md` | the A/B order tables, n16–n64 | `case/orders.py` |
| `source_tables/*.md` | the order tables of the original study, copied unchanged from `case/results/` | |
| `checks/*.derive.log` | output of the derivation: the 11 symbolic and 40-digit checks (full, flat, and ρ_F = 2, ρ_S = 3) | `derive/run_checks.sh` |
| `checks/*.check.log` | output of the independent checks of the generated C++ | `derive/check_generated.C` |
| `make_csv.py` | the script that wrote the CSV files (absolute paths of the run directories inside) | |

**`source_tables/`:**

- `qm_combined_{full,flat}.md`: QM, Δt ∝ h (QM rows of Table `tab:mms_fsi`).
- `qm_space_{full,flat}.md`: QM, fixed Δt = 6.25e-4.
- `qm_time_*.md`: QM temporal differences on n32.
- `{aitken,robin}_combined_full.md`: partitioned n16–n64. Superseded by the four-level tables in `order_tables/`.

**Run directories:**

- partitioned n16–n64 and all QM runs: `claude-runs/mms-fsi/case/runs/{aitken-full,robin-full,qm-full,qm-flat}/n*`;
- partitioned n128: `claude-runs/mms-pfv/base/{aitken,robin}-n128`;
- A/B: `claude-runs/mms-pfv/{S,SM,SW}/n*`.

These directories are not archived here.
