"""Detector study metrics (see studies/README.md for the interface).

Cone source (point source emitting into a cone about +z):
  total_efficiency_abs   events with E >= threshold, per photon emitted
                         into 4 pi (cone efficiency x cone solid-angle fraction)
  peak_efficiency_abs    the same for the full-energy peak (E >= E0 - window;
                         deposited energy, no detector resolution applied)
  peak_to_total          peak counts / total counts
  With a detector resolution ([resolution] in study.toml, FWHM at 662 keV
  per crystal material): the deposited energy is smeared with a Gaussian of
  sigma = FWHM/2.355 * sqrt(E * E0), reproducibly (seed from the run name),
  and a peak window E0 +- k * FWHM is applied (k = [checks] peak_window_fwhm):
  fwhm_keV                      the FWHM used
  resolved_peak_efficiency_abs  full-energy events inside the window, per
                                photon emitted into 4 pi
  peak_purity                   full-energy events / all events in the window
                                (the rest is Compton continuum smeared in)
  peak_to_compton               peak height / mean height of the Compton
                                plateau ([checks] compton_region_MeV, the
                                358-382 keV region usual for Cs-137); peak
                                height = resolved peak counts / (1.0645 FWHM),
                                the height of a Gaussian of that area.  The
                                most resolution-sensitive figure here.
Pencil source (along the axis):
  uncollided_fraction    photons reaching the monitor without interacting;
                         reference exp(-sum mu/rho * rho * x) through the
                         housing (2 walls) and the crystal, NIST data
Both:
  crystal_mass_kg
"""
import math
import zlib

import numpy as np

FWHM_PER_SIGMA = 2.0 * math.sqrt(2.0 * math.log(2.0))
# area of a Gaussian = height x FWHM x this (sqrt(pi / (4 ln 2)))
GAUSS_AREA_PER_HEIGHT_FWHM = math.sqrt(math.pi / (4.0 * math.log(2.0)))


def _volume(summary, name):
    for v in summary["volumes"]:
        if v["name"] == name:
            return v
    raise KeyError(f"no volume {name} in summary.json")


def _binomial(k, n):
    p = k / n
    return p, math.sqrt(max(p * (1 - p), 1.0 / n) / n)


def fwhm_fraction(study, material):
    """FWHM at the source energy as a fraction, or None if not given."""
    value = study.raw.get("resolution", {}).get("fwhm_662keV", {}).get(material)
    return float(value) if value else None


def smear(e, e0, fwhm_rel, key):
    """Gaussian resolution, sigma = FWHM/2.355 * sqrt(E * E0); events with
    no deposit stay at 0.  Seeded by the run key, so re-analysis gives the
    same numbers."""
    rng = np.random.default_rng(zlib.crc32(key.encode()))
    out = np.zeros_like(e)
    hit = e > 0
    sigma = fwhm_rel / FWHM_PER_SIGMA * np.sqrt(e[hit] * e0)
    out[hit] = e[hit] + rng.standard_normal(int(hit.sum())) * sigma
    return out


def run_metrics(ctx):
    e = ctx.events["Crystal_edep_MeV"]
    n = len(e)
    e0 = ctx.source.energy_MeV
    thr = float(ctx.study.checks.get("threshold_MeV", 0.010))
    window = float(ctx.study.checks.get("peak_window_MeV", 0.002))
    crystal = _volume(ctx.summary, "Crystal")
    p = ctx.variant.params
    metrics = {"crystal_mass_kg": (ctx.summary["detectors"]["Crystal"]["mass_kg"], None)}
    refs = {}

    n_tot = int(np.count_nonzero(e >= thr))
    full = e >= e0 - window
    n_peak = int(np.count_nonzero(full))
    src = ctx.source
    if src.cone_half_angle_deg > 0:
        frac = (1 - math.cos(math.radians(src.cone_half_angle_deg))) / 2
        tot, tot_err = _binomial(n_tot, n)
        pk, pk_err = _binomial(n_peak, n)
        metrics["total_efficiency_abs"] = (tot * frac, tot_err * frac)
        metrics["peak_efficiency_abs"] = (pk * frac, pk_err * frac)
        if n_tot:
            metrics["peak_to_total"] = _binomial(n_peak, n_tot)
        fwhm_rel = fwhm_fraction(ctx.study, p["material"])
        if fwhm_rel:
            k = float(ctx.study.checks.get("peak_window_fwhm", 1.0))
            measured = smear(e, e0, fwhm_rel, ctx.key)
            in_window = np.abs(measured - e0) <= k * fwhm_rel * e0
            n_win = int(np.count_nonzero(in_window))
            n_res = int(np.count_nonzero(in_window & full))
            res, res_err = _binomial(n_res, n)
            metrics["fwhm_keV"] = (fwhm_rel * e0 * 1000.0, None)
            metrics["resolved_peak_efficiency_abs"] = (res * frac, res_err * frac)
            if n_win:
                metrics["peak_purity"] = _binomial(n_res, n_win)
            lo, hi = ctx.study.checks.get("compton_region_MeV", (0.358, 0.382))
            n_c = int(np.count_nonzero((measured >= lo) & (measured < hi)))
            if n_res and n_c:
                width_keV = (hi - lo) * 1000.0
                peak_height = n_res / (GAUSS_AREA_PER_HEIGHT_FWHM * fwhm_rel * e0 * 1000.0)
                ptc = peak_height / (n_c / width_keV)
                metrics["peak_to_compton"] = (ptc, ptc * math.sqrt(1.0 / n_res + 1.0 / n_c))
    elif src.disc_radius_mm == 0:
        u, u_err = _binomial(int(ctx.events["Monitor_uncollided"].sum()), n)
        metrics["uncollided_fraction"] = (u, u_err)
        metrics["interaction_probability"] = _binomial(n_tot, n)
        mu = ctx.study.reference.get("mu_rho_cm2_g", {})
        housing = _volume(ctx.summary, "Housing")
        mu_h, mu_c = mu.get(p["housing_material"]), mu.get(p["material"])
        if mu_h is not None and mu_c is not None:
            x = (mu_h * housing["density_g_cm3"] * 2 * float(p["housing_mm"])
                 + mu_c * crystal["density_g_cm3"] * float(p["length_mm"])) / 10.0
            refs["uncollided_fraction"] = math.exp(-x)
    return metrics, refs


def derived(rows, study):
    pass


def _cone_contexts(contexts, study):
    cone = [s.name for s in study.sources if s.cone_half_angle_deg > 0]
    if not cone:
        return None, []
    first = study.physics_lists[0]
    sel = [c for c in contexts if c.source.name == cone[0] and c.physics == first]
    return cone[0], sel


def extra_plots(contexts, study, outdir, plt):
    """Deposited-energy spectra for the cone source, first physics list,
    without and (if [resolution] is given) with the detector resolution."""
    source, sel = _cone_contexts(contexts, study)
    if not sel:
        return []
    first = study.physics_lists[0]
    written = []

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bins = np.linspace(0.0, 0.7, 141)
    for ctx in sel:
        e = ctx.events["Crystal_edep_MeV"]
        e = e[e > 0]
        if e.size:
            ax.hist(e, bins=bins, histtype="step", label=ctx.variant.name)
    ax.set_yscale("log")
    ax.set_xlabel("energy deposited in crystal (MeV)")
    ax.set_ylabel("events / 5 keV")
    ax.set_title(f"Deposited-energy spectra, {source} ({first}), no resolution")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=7)
    fig.tight_layout()
    path = outdir / "spectra.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    written.append(path)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bins = np.linspace(0.0, 0.8, 161)   # room for the high side of wide peaks
    drawn = False
    for ctx in sel:
        fwhm_rel = fwhm_fraction(study, ctx.variant.params["material"])
        if not fwhm_rel:
            continue
        e0 = ctx.source.energy_MeV
        measured = smear(ctx.events["Crystal_edep_MeV"], e0, fwhm_rel, ctx.key)
        measured = measured[measured > 0]
        ax.hist(measured, bins=bins, histtype="step",
                label=f"{ctx.variant.name} ({fwhm_rel:.1%} FWHM)")
        drawn = True
    if drawn:
        ax.set_yscale("log")
        ax.set_xlabel("measured energy (MeV), resolution applied")
        ax.set_ylabel("events / 5 keV")
        ax.set_title(f"Spectra with detector resolution, {source} ({first})")
        ax.legend(fontsize=7)
        fig.tight_layout()
        path = outdir / "spectra_resolution.png"
        fig.savefig(path, dpi=130)
        written.append(path)
    plt.close(fig)
    return written
