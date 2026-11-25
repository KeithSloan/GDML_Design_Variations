"""Calorimeter study metrics (see studies/README.md for the interface).

Per run (signal = energy deposited in the active layers):
  resolution          sigma/mean of the signal
  stochastic_term     resolution * sqrt(E/GeV)   (electron sources only)
  sampling_fraction   mean(active) / mean(active + absorber)
  containment         mean(active + absorber) / beam energy
  signal_MeV_per_GeV  mean signal per GeV of beam energy
  e_over_mip          sampling_fraction / f_mip (MIP sampling fraction from
                      PDG dE/dx); checked against [checks] e_over_mip_range
  shower_max_layer    layer with the largest mean signal
  depth_X0, depth_lambda  total depth from Geant4's material properties
Across runs (same variant and physics list):
  e_over_pi           signal_MeV_per_GeV(electrons) / (pions), on pion rows
"""
import math

import numpy as np

ELECTRON_LIKE = {"e-", "e+", "gamma"}


def _volume(summary, name):
    for v in summary["volumes"]:
        if v["name"] == name:
            return v
    raise KeyError(f"no volume {name} in summary.json")


def _profile(summary, det, n_events):
    copies = summary["detectors"][det]["copies"]
    layers = sorted(int(k) for k in copies)
    if not layers:
        return np.zeros(0)
    prof = np.zeros(max(layers) + 1)
    for k, (s, _s2) in copies.items():
        prof[int(k)] = s / n_events
    return prof


def run_metrics(ctx):
    p = ctx.variant.params
    act = ctx.events["Active_edep_MeV"]
    ab = ctx.events["Absorber_edep_MeV"]
    tot = act + ab
    n = len(act)
    e0 = ctx.source.energy_MeV
    gev = e0 / 1000.0

    m_act, m_tot = act.mean(), tot.mean()
    s_act = act.std(ddof=1)
    res = s_act / m_act
    res_err = res * math.sqrt(1.0 / (2 * (n - 1)) + res ** 2 / n)

    cov = np.cov(act, tot)
    f = m_act / m_tot
    f_err = f * math.sqrt(max(cov[0, 0] / m_act ** 2 + cov[1, 1] / m_tot ** 2
                              - 2 * cov[0, 1] / (m_act * m_tot), 0.0) / n)

    absorber, active = _volume(ctx.summary, "Absorber"), _volume(ctx.summary, "Active")
    a, s, layers = float(p["absorber_mm"]), float(p["active_mm"]), int(p["layers"])
    metrics = {
        "resolution": (res, res_err),
        "sampling_fraction": (f, f_err),
        "containment": (m_tot / e0, tot.std(ddof=1) / math.sqrt(n) / e0),
        "signal_MeV_per_GeV": (m_act / gev, s_act / math.sqrt(n) / gev),
        "depth_mm": (layers * (a + s), None),
        "depth_X0": (layers * (a / absorber["radlen_mm"] + s / active["radlen_mm"]), None),
        "depth_lambda": (layers * (a / absorber["nuclear_int_length_mm"]
                                   + s / active["nuclear_int_length_mm"]), None),
    }
    if ctx.source.particle in ELECTRON_LIKE:
        metrics["stochastic_term"] = (res * math.sqrt(gev), res_err * math.sqrt(gev))

    prof = _profile(ctx.summary, "Active", n)
    if prof.size:
        metrics["shower_max_layer"] = (float(np.argmax(prof)), None)
        metrics["last_layer_fraction"] = (float(prof[-1] / prof.sum()), None)

    refs = {}
    dedx = ctx.study.reference.get("dedx_min_MeV_cm2_g", {})
    da, ds = dedx.get(p["absorber_material"]), dedx.get(p["active_material"])
    if da and ds:
        la = da * absorber["density_g_cm3"] * a / 10.0   # MeV per layer
        ls = ds * active["density_g_cm3"] * s / 10.0
        f_mip = ls / (la + ls)
        metrics["f_mip"] = (f_mip, None)
        metrics["e_over_mip"] = (f / f_mip, f_err / f_mip)
        if ctx.source.particle in ELECTRON_LIKE:
            refs["e_over_mip"] = tuple(ctx.study.checks.get("e_over_mip_range",
                                                            (0.55, 1.0)))
    return metrics, refs


def derived(rows, study):
    by = {(r["variant"], r["physics"], r["source"]): r for r in rows}
    electrons = [s.name for s in study.sources if s.particle in ELECTRON_LIKE]
    hadrons = [s.name for s in study.sources if s.particle not in ELECTRON_LIKE]
    if not electrons:
        return
    for r in rows:
        if r["source"] not in hadrons:
            continue
        e = by.get((r["variant"], r["physics"], electrons[0]))
        if e is None:
            continue
        se, see = e["signal_MeV_per_GeV"], e["signal_MeV_per_GeV_err"]
        sp, spe = r["signal_MeV_per_GeV"], r["signal_MeV_per_GeV_err"]
        ratio = se / sp
        r["e_over_pi"] = ratio
        r["e_over_pi_err"] = ratio * math.sqrt((see / se) ** 2 + (spe / sp) ** 2)


def extra_plots(contexts, study, outdir, plt):
    """Mean active-layer signal per layer, one panel per source."""
    sources = [s.name for s in study.sources]
    fig, axes = plt.subplots(1, len(sources), figsize=(6 * len(sources), 4.2),
                             squeeze=False)
    first = study.physics_lists[0]
    for ax, src in zip(axes[0], sources):
        for ctx in contexts:
            if ctx.source.name != src or ctx.physics != first:
                continue
            prof = _profile(ctx.summary, "Active", len(ctx.events["Active_edep_MeV"]))
            if prof.size:
                ax.plot(np.arange(prof.size) / prof.size, prof / prof.sum(),
                        label=ctx.variant.name)
        ax.set_xlabel("depth (fraction of calorimeter)")
        ax.set_ylabel("fraction of signal per layer")
        ax.set_title(f"Longitudinal profile, {src} ({first})")
        ax.legend(fontsize=7)
    fig.tight_layout()
    path = outdir / "longitudinal_profile.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return [path]
