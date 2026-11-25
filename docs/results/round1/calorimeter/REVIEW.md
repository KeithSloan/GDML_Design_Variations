# Review: Sampling calorimeter (1 GeV electrons, 10 GeV pions)

Reviewed 25 Nov 2026 from `review_input.md` (full statistics: 36 runs; 2000
electrons and 500 pions per run; GDML from FreeCAD 1.1.4 / GDML workbench
2.2.16; Geant4 11.4.3).  Following docs/REVIEW_GUIDE.md.  Three-way values
are FTFP_BERT / QGSP_BIC / FTFP_BERT_EMZ.

## Summary

- **Electrons:** finer sampling clearly gives the best electromagnetic
  resolution.  Pb 1 mm / scintillator 2 mm × 120 reaches σ/E = 0.059–0.063
  at 1 GeV, in the same 360 mm as the 2/4 mm baseline (0.077–0.081).  The
  resolution ranking is the same under all three physics lists.
- **Pions:** these variants cannot answer the pion half of the objective
  (e/π, physics-list differences for hadron showers).  They are only
  0.83–2.46 interaction lengths deep, and contain 21–48 % of the pion
  energy.  The pion numbers measure leakage, not the calorimeter.  A
  deeper, wider design is proposed below.

## Validity

- **Runs:** 36 of 36 ok, no Geant4 warnings, no overlaps reported when
  reading the GDML.
- **Reference check, electron e/mip:** all 18 runs inside the expected
  0.55–1.0 range (0.681–0.887).  Iron is highest (0.870–0.887) and the
  thick-lead variant lowest (0.681–0.684), as expected for high-Z
  absorbers.
- **Electron showers are contained longitudinally.**  The last layer holds
  0.4–4.8 × 10⁻⁴ of the signal, and the profiles in
  `plots/longitudinal_profile.png` fall to zero before the back.
  Containment is 0.970–0.982; the rest escapes laterally or backwards.
- **Pion showers are not contained.**  The profiles are still rising or
  flat at the back face, and the last layer holds 0.55–3.0 % of the
  signal.  `render/Pb2_Sc4_x60__FTFP_BERT__pi_10GeV_xz.png` shows deposits
  at full strength at the back face and out to the 200 mm lateral edges.
  So all pion results are dominated by leakage (see Limitations).
- **Geometry in the renders:** as designed (60 alternating Pb/scintillator
  layers to 360 mm, then vacuum).
- **Profile plot:** it shows the fraction of signal per layer, so variants
  with fewer, thicker layers appear higher.  Compare the shapes, not the
  heights.

## Results — electrons (1 GeV), the electromagnetic objective

| variant | depth (mm / X₀) | resolution σ/E (FB / BIC / EMZ) | sampling fraction (FB) | containment (FB) |
|---|---|---|---|---|
| Pb1_Sc2_x120 | 360 / 21.9 | 0.0633 ± 0.0010 / 0.05892 ± 0.00094 / 0.05924 ± 0.00094 | 0.19039 ± 0.00025 | 0.96966 ± 0.00062 |
| Pb2_LAr4_x60 | 360 / 23.1 | 0.0762 ± 0.0012 / 0.0763 ± 0.0012 / 0.0752 ± 0.0012 | 0.18917 ± 0.00031 | 0.97136 ± 0.00042 |
| Pb2_Sc4_x60 | 360 / 21.9 | 0.0802 ± 0.0013 / 0.0811 ± 0.0013 / 0.0766 ± 0.0012 | 0.17475 ± 0.00031 | 0.97023 ± 0.00044 |
| W1p4_Sc4_x60 | 324 / 24.5 | 0.0843 ± 0.0013 / 0.0844 ± 0.0013 / 0.0817 ± 0.0013 | 0.15222 ± 0.00029 | 0.98167 ± 0.00025 |
| Fe6_Sc4_x60 | 600 / 21.0 | 0.0993 ± 0.0016 / 0.0972 ± 0.0016 / 0.0956 ± 0.0015 | 0.09232 ± 0.00020 | 0.97821 ± 0.00060 |
| Pb4_Sc4_x30 | 240 / 21.7 | 0.1209 ± 0.0019 / 0.1225 ± 0.0020 / 0.1176 ± 0.0019 | 0.09329 ± 0.00025 | 0.98038 ± 0.00028 |

At 1 GeV the stochastic term (σ/E × √E) equals the resolution: 6–12 %/√GeV.

**Trade-offs (the objective):**
- **Best resolution:** Pb1_Sc2_x120.  Halving both layers of the baseline
  improves σ/E by 21–27 % at the same depth and lead content.
  Pb4_Sc4_x30, with double the lead per layer, is 51–54 % worse than the
  baseline.  The resolution follows the sampling frequency, as expected.
- **Liquid argon vs scintillator** at the same thickness (Pb2_LAr4 vs
  Pb2_Sc4): LAr is the same or slightly better, with differences of
  0.8–2.7 σ, not established.  Its sampling fraction is higher
  (0.189 vs 0.175).
- **Most compact for its resolution:** W1p4_Sc4_x60 at 324 mm (24.5 X₀).
  It has the best containment (0.980–0.982), with resolution
  (0.082–0.084) close to the Pb baseline.
- **Shortest overall:** Pb4_Sc4_x30 at 240 mm, but with the worst
  resolution.
- **Least suitable for electromagnetic calorimetry:** Fe6_Sc4_x60, which
  needs 600 mm for the same X₀ and is worse in resolution.

## Results — pions (10 GeV)

| variant | depth (λ) | containment (FB / BIC / EMZ) | σ/E (FB) | e/π (FB / BIC / EMZ) |
|---|---|---|---|---|
| Fe6_Sc4_x60 | 2.46 | 0.452 / 0.457 / 0.477 (± 0.011) | 0.504 ± 0.020 | 1.918 ± 0.043 / 1.899 ± 0.044 / 1.822 ± 0.040 |
| W1p4_Sc4_x60 | 1.16 | 0.264 / 0.297 / 0.276 (± 0.011) | 0.899 ± 0.046 | 2.90 ± 0.12 / 2.573 ± 0.097 / 2.79 ± 0.11 |
| Pb2_Sc4_x60 | 1.00 | 0.214 / 0.249 / 0.234 (± 0.010) | 1.005 ± 0.055 | 3.55 ± 0.16 / 3.02 ± 0.12 / 3.21 ± 0.14 |
| Pb1_Sc2_x120 | 1.00 | 0.230 / 0.218 / 0.228 (± 0.010) | 0.982 ± 0.053 | 3.41 ± 0.15 / 3.56 ± 0.16 / 3.43 ± 0.15 |
| Pb2_LAr4_x60 | 0.94 | 0.247 / 0.226 / 0.243 (± 0.010) | 0.893 ± 0.045 | 3.45 ± 0.14 / 3.72 ± 0.16 / 3.48 ± 0.14 |
| Pb4_Sc4_x30 | 0.83 | 0.217 / 0.226 / 0.231 (± 0.010) | 1.034 ± 0.058 | 3.20 ± 0.15 / 3.05 ± 0.14 / 2.98 ± 0.13 |

Containment, resolution and e/π all follow the depth in interaction
lengths.  e/π of 1.8–3.7 is mostly the escaping energy, not the
calorimeter's intrinsic e/h, so the "e/π close to 1" part of the objective
cannot be judged from these variants.

## Physics-list dependence

- **Electron resolution:** EMZ gives a lower (better) σ/E than FTFP_BERT
  in all six variants, by 1.3–6.4 %, each at 0.6–3 σ.
  - The trend is consistent, but not established per variant.
  - QGSP_BIC, which shares FTFP_BERT's EM physics, agrees with FTFP_BERT
    except for Pb1_Sc2_x120 (−6.9 %, −3.2 σ).  There EMZ is also low, so
    the FTFP_BERT value may be a fluctuation.
  - The error on σ/E assumes Gaussian fluctuations; leakage tails make it
    somewhat optimistic.
- **Sampling fraction, EM option:** for thin layers the EM model changes
  the energy scale.
  - Pb1_Sc2_x120 under EMZ is −2.0 % (−11.4 σ, significant).
  - The 2/4 mm and iron variants are −0.5 to −0.65 % (about −2 σ).
  - Thick lead is +0.3 %.
  - This affects calibration (about 2 % at 1 mm/2 mm sampling), not the
    ranking.
- **Sampling fraction, iron with QGSP_BIC:** +1.2 % (+4.1 σ, significant)
  for electrons in Fe6_Sc4_x60, with the same sign for pions (+1.3 %).
  - FTFP_BERT and QGSP_BIC share their EM physics, so the difference must
    come from the hadronic models.  In an electron shower these handle
    photo-nuclear products such as neutrons, to which hydrogen-rich
    scintillator is sensitive.
  - This is a plausible cause, not checked here.  It is worth a targeted
    run (see proposals).
- **Pions:** no difference between lists is significant with 500 pions.
  The largest are containment in Pb2_Sc4_x60 (0.214 vs 0.249, 2.4 σ) and
  e/π in W1p4 (2.90 vs 2.57, 2.1 σ).  They are leakage-dominated anyway.
- **Conclusion:** the electromagnetic ranking holds for all lists.  The
  hadronic comparison this study was meant to make needs a contained
  design.

## Recommendation

- **Electromagnetic resolution:** choose Pb1_Sc2_x120.  If depth is the
  constraint, W1p4_Sc4_x60 is the better compromise.
- **Calibration:** for absolute energy scale with thin sampling layers,
  check the EM option (EMZ vs standard), since the sampling fraction moves
  by about 2 %.
- **Hadrons:** do not draw hadronic or e/π conclusions from this round.
  Run a contained hadron design first.

## Proposed next variants

These are proposals for approval.

```toml
[[variants]]   # fine tungsten sampling: Pb1_Sc2 resolution in less depth?
name = "W0p7_Sc2_x120"
absorber_material = "G4_W"
absorber_mm = 0.7
active_mm = 2.0
layers = 120
note = "about 25 X0 in 324 mm"

[[variants]]   # fine liquid-argon sampling, to settle LAr vs scintillator
name = "Pb1_LAr2_x120"
active_material = "G4_lAr"
absorber_mm = 1.0
active_mm = 2.0
layers = 120
note = "as Pb1_Sc2_x120 with LAr"
```

- **A separate hadronic study (`hcal`).**  It needs a wider world, beam
  pipe and mesh, so it isn't a variant of this study.  Proposed design:
  - an 800 × 800 mm iron/scintillator calorimeter, Fe 20 mm / Sc 5 mm ×
    60 layers, 1500 mm deep, about 7.5 λ (estimated from this study's λ
    values);
  - 10 GeV π⁺ and e⁻, 2000 events each;
  - physics lists FTFP_BERT, QGSP_BIC and QGSP_BERT.
  This is where e/π and hadronic physics-list differences become
  measurable.
- **More events:** 8000 electrons per run (4×) would show whether the EMZ
  resolution trend is real (about 4 σ per variant).

## Limitations

- **Energy deposited, not a detector signal:** no Birks quenching in the
  scintillator, no recombination in liquid argon, no photostatistics or
  noise.  Quenching in particular changes e/h, so even a contained design
  would need it for a realistic e/π.
- **Width:** 200 × 200 mm is enough for electron showers, but too narrow
  for hadron showers.
- **Beam:** one energy per particle, a pencil beam at normal incidence,
  and no upstream material.
