# Review: Gamma-ray crystal detector (Cs-137, 662 keV), round 2

Reviewed 25 Nov 2026 from `review_input.md`.
- **Runs:** 54, with 100 000 photons per cone run and 50 000 per pencil
  run.  The 36 round-1 runs were reused unchanged, and the 18 new ones are
  BGO_2in, BGO_eqmass_NaI3in and LYSO_2in.
- **Versions:** GDML from FreeCAD 1.1.4 and GDML workbench 2.2.16, design
  commit 3fc0a90; Geant4 11.4.3.
- **Analysis:** analysed with commit 3124427, which adds energy resolution
  (study.toml `[resolution]`: FWHM at 662 keV of NaI 7.0 %, CsI 8.5 %,
  BGO 10 %, LYSO 7.5 %, LaBr₃ 3.0 %).

Written following docs/REVIEW_GUIDE.md.  Where all three lists are quoted,
values are given as FTFP_BERT / FTFP_BERT_EMZ / FTFP_BERT_LIV.
Efficiencies are per photon emitted into 4π.  The round-1 review is in
[../../round1/detector/REVIEW.md](../../round1/detector/REVIEW.md).

## Summary

- **At equal mass, BGO beats NaI.**  BGO_eqmass_NaI3in (1.273 kg, the mass
  of the 3 × 3 inch NaI) has 27–30 % more full-energy-peak efficiency than
  NaI_3in, with or without energy resolution applied.  Its peak-to-total
  is 0.83–0.84 against 0.55–0.56.  It is the most efficient detector
  tested.
- **BGO stays ahead of LYSO at 2 inches.**  BGO's lead over LYSO narrows
  from 15–19 % at 1.5 inch to 11–13 % at 2 inch, and stays significant
  (9–11 σ).
- **Energy resolution** leaves the efficiency ranking unchanged.  The
  resolved peak holds 97.8–98.6 % of the full-energy events.
  - LaBr₃ has the purest peak window.
  - BGO has the highest peak-to-Compton ratio, through its high
    photofraction despite the worst resolution.
- **Correction to round 1:** FTFP_BERT's higher peak efficiency for the
  high-Z crystals is not only its stronger attenuation.  FTFP_BERT also
  simulates no X-ray escape, which raises its peak-to-total, and the two
  effects contribute comparably.  Quote EMZ or LIV for absolute values.
- **Validity:** two reference mismatches, both FTFP_BERT-only, the known
  option-0 effect.  LYSO passes its other five checks.

## Validity

- **Runs:** 54 of 54 ok.  Every run has its requested number of photons,
  with no Geant4 warnings and no overlaps reported when reading the GDML.
- **Reference check, uncollided fraction vs NIST:** 25 of 27 pass.
  - **`CsI_1p5in__FTFP_BERT`:** 0.2461 ± 0.0019 vs 0.25336 (−2.88 %,
    −3.8 σ).  This is the round-1 failure.
  - **`LYSO_2in__FTFP_BERT`** (new): 0.03584 ± 0.00083 vs 0.038603
    (−7.16 %, −3.3 σ).  Under EMZ and LIV the same GDML passes
    (0.04032 ± 0.00088, +4.5 %, +2.0 σ; 0.03826 ± 0.00086, −0.9 %,
    −0.4 σ).  LYSO_1p5in passes under all three lists.  So the LYSO
    definition from `addMaterial` is right, and the failure is the
    option-0 effect.
  - **The pattern:**
    - FTFP_BERT is below the reference for all 9 crystals (−0.34 % to
      −7.16 %).  With the shield study that is 21 of 21 cases.
    - EMZ and LIV scatter on both sides.
    - The thick new crystals show the largest FTFP_BERT deficits:
      BGO_2in −5.6 %, BGO_eqmass_NaI3in −4.1 %, LYSO_2in −7.2 %.  These are
      within 1.1–3.3 σ, because only 1–4 % of photons get through
      uncollided.
- **New crystals in the renders:** as designed.
  - `render/BGO_eqmass_NaI3in__FTFP_BERT__Cs137_cone_xz.png` shows a BGO
    cylinder 61 mm long and about 61 mm across in its 1 mm aluminium
    housing.
  - Deposits stay in the crystal and housing, concentrated in the front
    half.
- **Resolution metrics:** each run uses its own seeded smearing, so
  rerunning the analysis gives the same numbers.  `fwhm_keV` matches the
  table above (46.3 keV for NaI … 19.9 keV for LaBr₃).

## Results

Cone source, peak efficiency without and with resolution (10⁻³), with
peak-to-total:

| variant | crystal mass (kg) | peak efficiency (FB / EMZ / LIV) | resolved peak efficiency, E₀ ± 1 FWHM (FB / EMZ / LIV) | peak-to-total (FB / EMZ / LIV) |
|---|---|---|---|---|
| BGO_eqmass_NaI3in | 1.273 | 14.396 ± 0.087 / 14.006 ± 0.086 / 14.120 ± 0.086 | 14.148 ± 0.086 / 13.747 ± 0.086 / 13.872 ± 0.086 | 0.8399 / 0.8297 / 0.8283 (± 0.0024) |
| NaI_3in | 1.274 | 11.100 ± 0.079 / 10.967 ± 0.078 / 11.087 ± 0.079 | 10.897 ± 0.078 / 10.764 ± 0.078 / 10.881 ± 0.078 | 0.5562 / 0.5516 / 0.5542 (± 0.0029) |
| BGO_2in | 0.734 | 9.859 ± 0.075 / 9.692 ± 0.075 / 9.650 ± 0.074 | 9.688 ± 0.075 / 9.505 ± 0.074 / 9.485 ± 0.074 | 0.8257 / 0.8107 / 0.8059 (± 0.0030) |
| LYSO_2in | 0.731 | 8.702 ± 0.071 / 8.743 ± 0.071 / 8.715 ± 0.071 | 8.526 ± 0.071 / 8.574 ± 0.071 / 8.536 ± 0.071 | 0.7588 / 0.7454 / 0.7500 (± 0.0033) |
| BGO_1p5in | 0.310 | 5.340 ± 0.057 / 5.103 ± 0.056 / 5.109 ± 0.056 | 5.238 ± 0.057 / 5.014 ± 0.056 / 5.009 ± 0.056 | 0.7822 / 0.7658 / 0.7642 (± 0.0042) |
| LYSO_1p5in | 0.308 | 4.486 ± 0.053 / 4.442 ± 0.053 / 4.359 ± 0.052 | 4.402 ± 0.052 / 4.367 ± 0.052 / 4.265 ± 0.052 | 0.6989 / 0.6903 / 0.6894 (± 0.0048) |
| CsI_1p5in | 0.196 | 2.375 ± 0.039 / 2.399 ± 0.039 / 2.449 ± 0.040 | 2.339 ± 0.039 / 2.353 ± 0.039 / 2.414 ± 0.039 | 0.4758 / 0.4815 / 0.4872 (± 0.0058) |
| LaBr3_1p5in | 0.221 | 2.156 ± 0.037 / 2.046 ± 0.036 / 2.036 ± 0.036 | 2.114 ± 0.037 / 2.005 ± 0.036 / 1.998 ± 0.036 | 0.4112 / 0.3992 / 0.4066 (± 0.0057) |
| NaI_1p5in | 0.159 | 1.668 ± 0.033 / 1.681 ± 0.033 / 1.690 ± 0.033 | 1.639 ± 0.033 / 1.653 ± 0.033 / 1.666 ± 0.033 | 0.3874 / 0.3932 / 0.3858 (± 0.0061) |

The ranking is the same under all three lists, with and without
resolution.

**The round-2 questions** (comparisons are my arithmetic on the table):
- **Equal mass (BGO_eqmass_NaI3in vs NaI_3in):**
  - BGO has +29.7 / +27.7 / +27.4 % peak efficiency (26–28 σ), and the
    same with resolution (+29.8 / +27.7 / +27.5 %).
  - NaI's *total* efficiency is higher (19.9–20.0 vs 16.9–17.1 × 10⁻³),
    because its 76 mm face takes a larger solid angle than BGO's 61 mm.
  - BGO converts far more of its interactions into the peak (peak-to-total
    0.83–0.84 vs 0.55–0.56).
- **Size (BGO_2in, LYSO_2in):**
  - Going from 1.5 to 2 inches multiplies the peak efficiency by
    1.85–1.90 for BGO and 1.94–2.00 for LYSO.
  - BGO_2in beats LYSO_2in by 13.3 / 10.8 / 10.7 % (9–11 σ).  At 1.5 inch
    the margin was 19.0 / 14.9 / 17.2 %.
  - BGO_2in reaches 87–89 % of NaI_3in's peak efficiency at 58 % of its
    mass.
- **Per kilogram (10⁻³/kg):** BGO_1p5in 16.5–17.2; LYSO_1p5in 14.1–14.6;
  BGO_2in 13.1–13.4; LYSO_2in 11.9–12.0; BGO_eqmass 11.0–11.3; NaI_3in
  8.6–8.7.  Efficiency per kilogram falls with size, as it must.

**With energy resolution** (Cs137_cone; new metrics this round):

| variant | FWHM (keV) | peak purity (FB / EMZ / LIV) | peak-to-Compton (FB / EMZ / LIV) |
|---|---|---|---|
| LaBr3_1p5in | 19.9 | 0.99873 ± 0.00063 / 0.99800 ± 0.00082 / 0.99899 ± 0.00058 | 16.5 ± 1.2 / 14.28 ± 0.96 / 14.60 ± 1.00 |
| NaI_3in | 46.3 | 0.99663 ± 0.00045 / 0.99455 ± 0.00058 / 0.99425 ± 0.00059 | 12.49 ± 0.51 / 12.03 ± 0.48 / 12.51 ± 0.51 |
| NaI_1p5in | 46.3 | 0.9963 ± 0.0012 / 0.9892 ± 0.0021 / 0.9877 ± 0.0022 | 6.14 ± 0.46 / 5.83 ± 0.42 / 6.08 ± 0.45 |
| CsI_1p5in | 56.2 | 0.9952 ± 0.0012 / 0.9913 ± 0.0016 / 0.99640 ± 0.00100 | 7.65 ± 0.58 / 7.74 ± 0.59 / 7.81 ± 0.59 |
| LYSO_1p5in | 49.6 | 0.99546 ± 0.00083 / 0.9927 ± 0.0011 / 0.9919 ± 0.0011 | 23.1 ± 2.1 / 24.3 ± 2.2 / 19.8 ± 1.7 |
| LYSO_2in | 49.6 | 0.99663 ± 0.00051 / 0.99379 ± 0.00069 / 0.99260 ± 0.00076 | 30.4 ± 2.2 / 27.6 ± 1.9 / 31.0 ± 2.3 |
| BGO_1p5in | 66.2 | 0.99554 ± 0.00075 / 0.9875 ± 0.0013 / 0.9872 ± 0.0013 | 29.3 ± 3.1 / 32.3 ± 3.7 / 27.7 ± 2.9 |
| BGO_2in | 66.2 | 0.99559 ± 0.00055 / 0.99238 ± 0.00073 / 0.99000 ± 0.00083 | 45.2 ± 4.3 / 41.3 ± 3.8 / 35.2 ± 3.0 |
| BGO_eqmass_NaI3in | 66.2 | 0.99585 ± 0.00044 / 0.99068 ± 0.00067 / 0.99062 ± 0.00067 | 43.1 ± 3.3 / 42.9 ± 3.4 / 43.8 ± 3.5 |

- **Resolved peak efficiency:** applying the resolution keeps 97.8–98.6 %
  of the full-energy events in the E₀ ± 1 FWHM window.  It changes no
  ranking.  A single isolated line at 662 keV does not reward resolution.
- **Peak purity:** LaBr₃ is highest (0.9980–0.9990).  Its narrow window
  admits almost no Compton or escape events.
  - Under EMZ and LIV the others are 0.987–0.996.
  - FTFP_BERT's purities are systematically higher, for the reason given
    under Physics-list dependence.
- **Peak-to-Compton:** this depends on the photofraction as well as on
  the resolution.
  - BGO leads (28–32 at 1.5 inch, 35–45 at 2 inch and equal mass), then
    LYSO.
  - LaBr₃ (14–17) is 2–3 times NaI_1p5in and about twice CsI_1p5in, at
    similar or lower peak-to-total, so mainly through resolution.
  - NaI_3in reaches 12–12.5.
  - BGO_2in vs LYSO_2in is 3.0 / 3.2 / 1.1 σ: not established under LIV.
- **What resolution does not show here:** LaBr₃'s advantage is separating
  nearby lines.  This study has one line, so that is still untested (see
  proposals).

## Physics-list dependence

- **X-ray escape (correction to round 1):** FTFP_BERT simulates no X-ray
  escape, while EMZ and LIV do.
  - The cone-run event files (`runs/*_1p5in__*__Cs137_cone/events.csv.gz`)
    were examined by hand for events missing a fixed energy just below
    662 keV.
  - Under EMZ and LIV, events cluster at missing energies of 75–77 and
    87–88 keV in BGO, 53–54 and 61 keV in LYSO, 29 keV in NaI, 31 keV in
    CsI and 33 keV in LaBr₃.  These are the K X-ray energies of Bi, Lu,
    I, Cs and La.
  - Under FTFP_BERT there are none.
  - This is consistent with atomic de-excitation being off by default in
    the standard EM option (0) and on in options 4 (EMZ) and Livermore
    (LIV).
  - **Consequences:**
    - FTFP_BERT counts escape events as full-energy events, so its
      peak-to-total is higher.  The BGO peak-to-total flags (EMZ and LIV
      lower by 1.2–2.4 %, 3.1–4.8 σ) are this effect.
    - Peak efficiency is total efficiency × peak-to-total.  For BGO_1p5in
      (FB vs EMZ), total efficiency is +2.4 % (1.8 σ; the stronger
      attenuation) and peak-to-total +2.1 % (2.8 σ; no escape).  Together
      they give the +4.6 % in peak efficiency (5.340 vs 5.103 × 10⁻³).
    - For BGO_eqmass_NaI3in the flagged −2.7 % (EMZ, −3.2 σ) splits
      similarly.
    - Round 1 attributed the whole difference to attenuation.
    - Escape also explains FTFP_BERT's higher peak purity, where an
      escape line falls inside the window, e.g. iodine's 29 keV against
      NaI's ±46 keV.
  - This is a finding about the physics lists, not the designs.
    Fluorescence matters for any crystal of high atomic number.
- **Uncollided fraction:** the flagged CsI (+3.9 to +4.0 %) and LYSO_2in
  (EMZ +12.5 %, 3.7 σ) differences are the option-0 attenuation effect
  under Validity.
- **Rankings:** the same under all three lists for every efficiency
  metric.

## Recommendation

- **Highest peak efficiency for a given mass, or for a given size up to
  2 inch:** BGO.  At the mass of a 3 × 3 inch NaI it gives about 28 %
  more peak efficiency and a far cleaner spectrum (peak-to-total 0.83 vs
  0.55).
- **LYSO** is 11–13 % behind BGO at 2 inch.  Choose it for timing or
  light yield, not for 662 keV efficiency.
- **LaBr₃:** choose it for line separation and peak purity, not for
  efficiency.  At this size it has less than half of BGO's peak efficiency.
- **Physics list:** quote EMZ or LIV for detector efficiencies and spectra.
  FTFP_BERT lacks X-ray escape and gives high-Z peak efficiencies up to
  about 6 % higher (LaBr₃ and BGO at 1.5 inch).

## Proposed next variants

The size and equal-mass questions are answered.  The open question is
spectroscopy, which needs a source with several lines.  These are
proposals for approval:

- **A multi-line source (design change):** e.g. Ba-133's 356 and 384 keV
  lines, 28 keV apart.  These are resolved by LaBr₃ (FWHM about 15 keV
  there with the √E scaling) and blended by BGO (about 49 keV).
  - `study.py` sources currently take one energy, so this needs a GPS line
    spectrum (`/gps/ene/type Arb` or several `/gps/source/add`).
  - It also needs a metric for the depth of the valley between the lines.
- **A direct test of the fluorescence explanation (design change):**
  FTFP_BERT with `/process/em/fluo true` added to the run macro.  If the
  explanation is right, FTFP_BERT's peak efficiency for BGO should drop to
  the EMZ/LIV value.
  - This needs a way to attach extra macro commands to a physics setting
    in `study.toml`.
- **One variant:**

```toml
[[variants]]   # the common 2-inch LaBr3: efficiency vs resolution at size
name = "LaBr3_2in"
material = "LaBr3"
radius_mm = 25.4
length_mm = 50.8
note = "LaBr3 at the size of BGO_2in and LYSO_2in"
```

## Limitations

- **Resolution:** a published FWHM applied in the analysis with a
  √E scaling.  No light collection, non-proportionality or electronics
  are simulated, and the FWHM values are typical, not measured for these
  crystals.
- **Intrinsic activity:** LYSO's Lu-176 and LaBr₃'s La-138 are not
  simulated.  Both add background that matters for spectroscopy, less for
  a strong Cs-137 source.
- **Source:** one distance (100 mm), one energy and a 30° cone.
- **Housing:** 1 mm aluminium only, with no reflector, window or
  photomultiplier.
