"""Manufactured FSI solution figure for the verification paper (fig:mms_fsi):
(a) the fluid and solid domains in the reference configuration and the exact
interface y = 1 + eta(x, t) at t = 0, 0.2 and 0.4, for the full and flat
variants; (b, c) the fluid pressure error p - p_exact at the end time on the
deformed fluid mesh, for the partitioned (Dirichlet-Neumann, Aitken) and the
quasi-monolithic (QM) runs on the same mesh, with one colour scale.

The exact interface is evaluated with the case's exact evaluators (evalExact,
evalExactFlat: "interface X t" -> x y tx ty nx ny); the pressure error is the
pError field written by the case's error function object (p - p_exact at the
cell centres, not mean-corrected).

Usage:
  mms_fsi_figure.py EVAL_FULL EVAL_FLAT AITKEN_RUN QM_RUN OUT.pdf [TIME] [LABEL]
    EVAL_FULL, EVAL_FLAT: the exact evaluators of the full and flat variants
    AITKEN_RUN, QM_RUN: case directories with TIME/fluid/{pError,polyMesh/points}
      and constant/fluid/polyMesh/{faces,owner,boundary}
    TIME: time directory of the error fields (default 0.4)
    LABEL: mesh label for the panel titles (default "n = 128")
Prints the range and RMS of each error field."""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from matplotlib.ticker import FormatStrFormatter

plt.rcParams.update({"font.size": 8, "mathtext.fontset": "cm",
                     "font.family": "serif", "pdf.fonttype": 42})
FLUID, SOLID = "#dbe8f5", "#f2d4d0"
# Okabe-Ito
C02, C04 = "#0072B2", "#D55E00"

L, H, T = 2.0, 1.0, 0.5


# ---- minimal ASCII OpenFOAM readers ----------------------------------------
def _body(path):
    txt = Path(path).read_text()
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    return re.sub(r"//[^\n]*", "", txt)


def _list_after(txt, start):
    """The 'N ( ... )' list starting at or after index start: (string, end)."""
    m = re.compile(r"(\d+)\s*\(").search(txt, start)
    i, depth = m.end(), 1
    j = i
    while depth:
        depth += {"(": 1, ")": -1}.get(txt[j], 0)
        j += 1
    return int(m.group(1)), txt[i:j - 1]


def read_points(path):
    txt = _body(path)
    n, body = _list_after(txt, txt.index("}") + 1)
    p = np.array([[float(v) for v in s.split()]
                  for s in re.findall(r"\(([^()]*)\)", body)])
    assert len(p) == n
    return p


def read_faces(path):
    txt = _body(path)
    n, body = _list_after(txt, txt.index("}") + 1)
    f = [[int(v) for v in s.split()] for s in re.findall(r"\d+\s*\(([^()]*)\)", body)]
    assert len(f) == n
    return f


def read_labels(path):
    txt = _body(path)
    n, body = _list_after(txt, txt.index("}") + 1)
    v = np.array(body.split(), dtype=int)
    assert len(v) == n
    return v


def read_scalar_field(path):
    txt = _body(path)
    k = txt.index("internalField")
    n, body = _list_after(txt, k)
    v = np.array(body.split(), dtype=float)
    assert len(v) == n
    return v


def empty_patch(path):
    """(startFace, nFaces) of the empty (front/back) patch."""
    txt = _body(path)
    for m in re.finditer(r"(\w+)\s*\{([^{}]*)\}", txt):
        if re.search(r"\btype\s+empty\s*;", m.group(2)):
            s = int(re.search(r"startFace\s+(\d+)", m.group(2)).group(1))
            n = int(re.search(r"nFaces\s+(\d+)", m.group(2)).group(1))
            return s, n
    raise RuntimeError("no empty patch in " + str(path))


def fluid_cells(run, time):
    """Cell polygons (x, y) of the 2-D fluid mesh at time, and pError."""
    pm = Path(run) / "constant" / "fluid" / "polyMesh"
    pts = read_points(Path(run) / time / "fluid" / "polyMesh" / "points")
    faces = read_faces(pm / "faces")
    owner = read_labels(pm / "owner")
    s, n = empty_patch(pm / "boundary")
    err = read_scalar_field(Path(run) / time / "fluid" / "pError")
    zmin = pts[:, 2].min()
    polys = [None] * len(err)
    for fi in range(s, s + n):
        f = faces[fi]
        if np.allclose(pts[f, 2], zmin):
            polys[owner[fi]] = pts[f, :2]
    assert all(p is not None for p in polys)
    return polys, err


# ---- exact interface --------------------------------------------------------
def exact_interface(exe, t, nX=401):
    X = np.linspace(0.0, L, nX)
    inp = "".join(f"interface {x:.17g} {t:.17g}\n" for x in X)
    out = subprocess.run([exe], input=inp, capture_output=True, text=True, check=True).stdout
    v = np.array([[float(q) for q in l.split()] for l in out.strip().splitlines()])
    return v[:, 0], v[:, 1]


def interfaces(eval_full, eval_flat):
    """[(variant, t, x, y)] for t = 0.2, 0.4."""
    out = []
    for t in (0.2, 0.4):
        out.append(("full", t) + exact_interface(eval_full, t))
        out.append(("flat", t) + exact_interface(eval_flat, t))
    return out


STYLE = {("full", 0.2): dict(color=C02, ls="-", lw=1.2),
         ("flat", 0.2): dict(color=C02, ls="--", lw=1.0),
         ("full", 0.4): dict(color=C04, ls="-", lw=1.2),
         ("flat", 0.4): dict(color=C04, ls="--", lw=1.0)}


def panel_geometry(ax, curves):
    ax.fill_between([0, L], 0, H, color=FLUID, lw=0)
    ax.fill_between([0, L], H, H + T, color=SOLID, lw=0)
    ax.plot([0, L, L, 0, 0], [0, 0, H + T, H + T, 0], color="black", lw=0.8)
    ax.plot([0, L], [H, H], color="black", lw=0.8)
    for v, t, x, y in curves:
        ax.plot(x, y, **STYLE[(v, t)])
    ax.text(1.0, 0.5, "fluid", ha="center", va="center")
    ax.text(1.0, 1.3, "solid", ha="center", va="center")
    ax.text(-0.05, 0.5, "inlet", rotation=90, ha="right", va="center", fontsize=7)
    ax.text(L + 0.05, 0.5, "outlet", rotation=90, ha="left", va="center", fontsize=7)
    ax.text(1.0, -0.04, "no-slip wall", ha="center", va="top", fontsize=7)
    ax.text(1.0, H + T + 0.04, "clamped", ha="center", va="bottom", fontsize=7)
    ax.text(1.0, H - 0.04, "interface $Y = 1$", ha="center", va="top", fontsize=7)
    ax.set_xlim(-0.2, L + 0.2)
    ax.set_ylim(-0.2, H + T + 0.2)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y$")
    ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.set_yticks([0, 0.5, 1, 1.5])


def panel_interface(ax, curves):
    ax.axhline(H, color="black", lw=0.8, label="$t = 0$")
    for v, t, x, y in curves:
        ax.plot(x, y, label=f"{v}, $t = {t}$", **STYLE[(v, t)])
    ax.set_xlim(0, L)
    ax.set_ylim(0.99, 1.135)
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y = 1 + \\eta$")
    ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.legend(loc="upper left", fontsize=7, frameon=False, ncol=1,
              handlelength=2.4, borderaxespad=0.3)


def panel_error(ax, polys, err, norm, title):
    pc = PolyCollection(polys, array=err, cmap="RdBu_r", norm=norm,
                        edgecolors="none", antialiased=False)
    ax.add_collection(pc)
    xy = np.vstack(polys)
    ax.plot([0, L], [0, 0], color="black", lw=0.6)
    ax.set_xlim(-0.02, L + 0.02)
    ax.set_ylim(-0.02, xy[:, 1].max() + 0.03)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$")
    ax.set_xticks([0, 0.5, 1, 1.5, 2])
    ax.set_yticks([0, 0.5, 1])
    ax.set_title(title, fontsize=8)
    ax.text(0.03, 0.06, "max $|p - p_\\mathrm{ex}| = " + sci(abs(err).max()) + "$",
            transform=ax.transAxes, fontsize=7, ha="left", va="bottom")
    return pc


def sci(v):
    """2-digit LaTeX scientific notation."""
    m, e = f"{v:.1e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def main():
    if len(sys.argv) < 6:
        sys.exit(__doc__)
    eval_full, eval_flat, run_a, run_q, out = sys.argv[1:6]
    time = sys.argv[6] if len(sys.argv) > 6 else "0.4"
    label = sys.argv[7] if len(sys.argv) > 7 else "n = 128"

    pa, ea = fluid_cells(run_a, time)
    pq, eq = fluid_cells(run_q, time)
    for nm, e in (("Aitken", ea), ("QM", eq)):
        print(f"{nm}: pError min {e.min():.3e} max {e.max():.3e} "
              f"rms {np.sqrt(np.mean(e**2)):.3e} (unweighted)")
    vmax = max(abs(ea).max(), abs(eq).max())
    norm = Normalize(vmin=-vmax, vmax=vmax)
    curves = interfaces(eval_full, eval_flat)

    fig = plt.figure(figsize=(5.9, 4.0))
    top = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25], left=0.08, right=0.97,
                           bottom=0.56, top=0.94, wspace=0.3)
    bot = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 0.035], left=0.08, right=0.895,
                           bottom=0.07, top=0.44, wspace=0.1)
    ax0 = fig.add_subplot(top[0])
    ax0b = fig.add_subplot(top[1])
    ax1 = fig.add_subplot(bot[0])
    ax2 = fig.add_subplot(bot[1], sharey=ax1)
    cax = fig.add_subplot(bot[2])

    panel_geometry(ax0, curves)
    panel_interface(ax0b, curves)
    fig.text(0.08, 0.975, "(a) domains at $t = 0$, and exact interface "
             "$y = 1 + \\eta(x, t)$ (right: vertical scale enlarged)",
             ha="left", va="top", fontsize=8)

    tl = f"{float(time):g}"
    pc = panel_error(ax1, pa, ea, norm,
                     f"(b) partitioned (Aitken), ${label}$, $t = {tl}$")
    panel_error(ax2, pq, eq, norm,
                f"(c) quasi-monolithic, ${label}$, $t = {tl}$")
    ax1.set_ylabel("$y$")
    plt.setp(ax2.get_yticklabels(), visible=False)
    ax1.annotate("outlet–wall corner", xy=(1.98, 0.2), xytext=(1.3, 0.25),
                 fontsize=7, ha="center", va="center",
                 arrowprops=dict(arrowstyle="->", lw=0.6))
    cb = fig.colorbar(pc, cax=cax)
    for ax in (ax0, ax0b, ax1, ax2):
        ax.xaxis.set_major_formatter(FormatStrFormatter("%g"))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%g"))
    cb.ax.tick_params(labelsize=7)
    cb.set_label("$p - p_\\mathrm{ex}$", fontsize=8)

    fig.savefig(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
