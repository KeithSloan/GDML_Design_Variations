"""Detector study metrics (see studies/README.md for the interface).

Cone source (point source emitting into a cone about +z):
  total_efficiency_abs   events with E >= threshold, per photon emitted
                         into 4 pi (cone efficiency x cone solid-angle fraction)
  peak_efficiency_abs    the same for the full-energy peak (E >= E0 - window;
                         deposited energy, no detector resolution applied)
  peak_to_total          peak counts / total counts
Pencil source (along the axis):
  uncollided_fraction    photons reaching the monitor without interacting;
                         reference exp(-sum mu/rho * rho * x) through the
                         housing (2 walls) and the crystal, NIST data
Both:
  crystal_mass_kg
"""
import math

import numpy as np


def _volume(summary, name):
    for v in summary["volumes"]:
        if v["name"] == name:
            return v
    raise KeyError(f"no volume {name} in summary.json")


def _binomial(k, n):
    p = k / n
    return p, math.sqrt(max(p * (1 - p), 1.0 / n) / n)


def run_metrics(ctx):
    e = ctx.events["Crystal_edep_MeV"]
    n = len(e)
    e0 = ctx.source.energy_MeV
    thr = float(ctx.study.checks.get("threshold_MeV", 0.010))
    window = float(ctx.study.checks.get("peak_window_MeV", 0.002))
    crystal = _volume(ctx.summary, "Crystal")
    metrics = {"crystal_mass_kg": (ctx.summary["detectors"]["Crystal"]["mass_kg"], None)}
    refs = {}

    n_tot = int(np.count_nonzero(e >= thr))
    n_peak = int(np.count_nonzero(e >= e0 - window))
    src = ctx.source
    if src.cone_half_angle_deg > 0:
        frac = (1 - math.cos(math.radians(src.cone_half_angle_deg))) / 2
        tot, tot_err = _binomial(n_tot, n)
        pk, pk_err = _binomial(n_peak, n)
        metrics["total_efficiency_abs"] = (tot * frac, tot_err * frac)
        metrics["peak_efficiency_abs"] = (pk * frac, pk_err * frac)
        if n_tot:
            metrics["peak_to_total"] = _binomial(n_peak, n_tot)
    elif src.disc_radius_mm == 0:
        u, u_err = _binomial(int(ctx.events["Monitor_uncollided"].sum()), n)
        metrics["uncollided_fraction"] = (u, u_err)
        metrics["interaction_probability"] = _binomial(n_tot, n)
        mu = ctx.study.reference.get("mu_rho_cm2_g", {})
        p = ctx.variant.params
        housing = _volume(ctx.summary, "Housing")
        mu_h, mu_c = mu.get(p["housing_material"]), mu.get(p["material"])
        if mu_h is not None and mu_c is not None:
            x = (mu_h * housing["density_g_cm3"] * 2 * float(p["housing_mm"])
                 + mu_c * crystal["density_g_cm3"] * float(p["length_mm"])) / 10.0
            refs["uncollided_fraction"] = math.exp(-x)
    return metrics, refs


def derived(rows, study):
    pass


def extra_plots(contexts, study, outdir, plt):
    """Deposited-energy spectra for the cone source, first physics list."""
    cone = [s.name for s in study.sources if s.cone_half_angle_deg > 0]
    if not cone:
        return []
    first = study.physics_lists[0]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bins = np.linspace(0.0, 0.7, 141)
    for ctx in contexts:
        if ctx.source.name != cone[0] or ctx.physics != first:
            continue
        e = ctx.events["Crystal_edep_MeV"]
        e = e[e > 0]
        if e.size:
            ax.hist(e, bins=bins, histtype="step", label=ctx.variant.name)
    ax.set_yscale("log")
    ax.set_xlabel("energy deposited in crystal (MeV)")
    ax.set_ylabel("events / 5 keV")
    ax.set_title(f"Deposited-energy spectra, {cone[0]} ({first}), no resolution")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=7)
    fig.tight_layout()
    path = outdir / "spectra.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return [path]
