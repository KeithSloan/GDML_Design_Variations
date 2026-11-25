"""Shield study metrics (see studies/README.md for the interface).

Per run:
  dose_per_photon_Gy    mean dose to the phantom per incident photon
  uncollided_fraction   photons reaching the phantom without interacting;
                        reference exp(-mu/rho * rho * t) from NIST data
  areal_density_g_cm2   rho * t of the shield (rho as Geant4 used it)
Across runs (same physics list and source, relative to No_shield):
  dose_transmission     dose / dose without a shield
  buildup_factor        dose_transmission / uncollided_fraction
  mass_attenuation_eff_cm2_g  -ln(dose_transmission) / areal density
"""
import math

MEV_TO_J = 1.602176634e-13
REFERENCE_VARIANT = "No_shield"


def _volume(summary, name):
    for v in summary["volumes"]:
        if v["name"] == name:
            return v
    return None


def run_metrics(ctx):
    edep = ctx.events["Phantom_edep_MeV"]
    n = len(edep)
    mass = ctx.summary["detectors"]["Phantom"]["mass_kg"]
    dose = edep.mean() * MEV_TO_J / mass
    dose_err = edep.std(ddof=1) / math.sqrt(n) * MEV_TO_J / mass

    unc = ctx.events["Phantom_uncollided"]
    u = float(unc.mean())
    u_err = math.sqrt(max(u * (1 - u), 1.0 / n) / n)

    p = ctx.variant.params
    t_mm = float(p["thickness_mm"])
    shield = _volume(ctx.summary, "Shield")
    rho = shield["density_g_cm3"] if (t_mm > 0 and shield) else 0.0
    areal = rho * t_mm / 10.0

    metrics = {
        "dose_per_photon_Gy": (dose, dose_err),
        "uncollided_fraction": (u, u_err),
        "areal_density_g_cm2": (areal, None),
        "shield_mass_kg": ((shield["mass_kg"] if shield else 0.0), None),
    }
    refs = {}
    if t_mm == 0:
        refs["uncollided_fraction"] = 1.0
    else:
        mu = ctx.study.reference.get("mu_rho_cm2_g", {}).get(p["material"])
        if mu is not None:
            refs["uncollided_fraction"] = math.exp(-mu * areal)
    return metrics, refs


def derived(rows, study):
    ref = {(r["physics"], r["source"]): r for r in rows
           if r["variant"] == REFERENCE_VARIANT}
    for r in rows:
        r0 = ref.get((r["physics"], r["source"]))
        if r0 is None:
            continue
        d, e = r["dose_per_photon_Gy"], r["dose_per_photon_Gy_err"]
        d0, e0 = r0["dose_per_photon_Gy"], r0["dose_per_photon_Gy_err"]
        if r is r0:
            t, te = 1.0, 0.0
        else:
            t = d / d0
            te = t * math.sqrt((e / d) ** 2 + (e0 / d0) ** 2)
        r["dose_transmission"], r["dose_transmission_err"] = t, te

        u, ue = r["uncollided_fraction"], r["uncollided_fraction_err"]
        if u > 0:
            b = t / u
            r["buildup_factor"] = b
            r["buildup_factor_err"] = b * math.sqrt((te / t) ** 2 + (ue / u) ** 2) \
                if t > 0 else None
        areal = r["areal_density_g_cm2"]
        if areal > 0 and 0 < t < 1:
            mu = -math.log(t) / areal
            r["mass_attenuation_eff_cm2_g"] = mu
            r["mass_attenuation_eff_cm2_g_err"] = te / t / areal
