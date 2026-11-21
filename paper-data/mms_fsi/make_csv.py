import csv, os, sys
R = "/Volumes/OpenFOAM/philipc-v2512/claude-runs/mms-fsi/case/runs"
B = "/Users/philipc/claude-runs/mms-pfv"
PD = sys.argv[1]
series = {
    "aitken_full": [f"{R}/aitken-full/n16", f"{R}/aitken-full/n32", f"{R}/aitken-full/n64", f"{B}/base/aitken-n128"],
    "robin_full":  [f"{R}/robin-full/n16", f"{R}/robin-full/n32", f"{R}/robin-full/n64", f"{B}/base/robin-n128"],
    "qm_full":     [f"{R}/qm-full/n{n}" for n in (16, 32, 64, 128)],
    "qm_flat":     [f"{R}/qm-flat/n{n}" for n in (16, 32, 64, 128)],
    "aitken_full_ab_S":  [f"{B}/S/n{n}" for n in (16, 32, 64)],
    "aitken_full_ab_SM": [f"{B}/SM/n{n}" for n in (16, 32, 64)],
    "aitken_full_ab_SW": [f"{B}/SW/n{n}" for n in (16, 32, 64)],
}
summary = []
iters = []
for name, runs in series.items():
    for i, run in enumerate(runs):
        n = [16, 32, 64, 128][i]
        f = os.path.join(run, "postProcessing", "mmsFsiErrors", "errors.dat")
        lines = open(f).read().splitlines()
        hdr = lines[0].lstrip("#").split()
        rows = [l.split() for l in lines[1:] if l.strip()]
        with open(os.path.join(PD, "errors_csv", f"{name}_n{n}.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(hdr)
            w.writerows(rows)
        for r in rows:
            t = float(r[0])
            if any(abs(t - T) < 1e-6 for T in (0.2, 0.4)):
                d = dict(zip(hdr, r))
                summary.append([name, n, f"{t:g}"] + [d[c] for c in (
                    "U_L2", "p_L2", "D_L2", "intD_L2", "intTrac_L2", "intP_L2", "U_Linf", "p_Linf")])
        fr = os.path.join(run, "postProcessing", "fsiResiduals.dat")
        if os.path.exists(fr):
            m = {}
            for l in open(fr):
                if l.startswith("#") or not l.strip() or not l.split()[0][0].isdigit():
                    continue
                p = l.split()
                t = float(p[0])
                k = int(float(p[1]))
                m[t] = max(m.get(t, 0), k)
            vals = [m[t] for t in sorted(m) if t > 0]
            iters.append([name, n, len(vals), f"{sum(vals)/len(vals):.1f}", max(vals)])
with open(os.path.join(PD, "summary_errors_t0.2_t0.4.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["series", "n", "time", "U_L2", "p_L2", "D_L2", "intD_L2", "intTrac_L2", "intP_L2", "U_Linf", "p_Linf"])
    w.writerows(summary)
with open(os.path.join(PD, "coupling_iterations.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["series", "n", "steps", "mean_iterations_per_step", "max_iterations_per_step"])
    w.writerows(iters)
