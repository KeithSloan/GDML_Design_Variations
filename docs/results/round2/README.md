# Round 2 results (25 November 2026)

Round 2 adds the variants proposed in the round-1 reviews and approved for
this round.  It also adds a detector energy-resolution metric.  The AI
reviews are stage 5 in [docs/WORKFLOW.md](../../WORKFLOW.md).  The round-1
runs were reused unchanged, and their metrics are identical to
[round 1](../round1/README.md).

| Study | New variants | Runs | Reference checks | Review |
|---|---|---|---|---|
| shield | W_12mm, Fe_29mm, Pb_40mm | 39/39 ok | 38/39 pass | [shield/REVIEW.md](shield/REVIEW.md) |
| calorimeter | W0p7_Sc2_x120, Pb1_LAr2_x120 | 48/48 ok | 24/24 pass | [calorimeter/REVIEW.md](calorimeter/REVIEW.md) |
| detector | BGO_2in, BGO_eqmass_NaI3in, LYSO_2in | 54/54 ok | 25/27 pass | [detector/REVIEW.md](detector/REVIEW.md) |

No run reported a geometry overlap or a Geant4 warning.  The three failed
reference checks are FTFP_BERT uncollided fractions: `W_10mm` and
`CsI_1p5in` from round 1, and the new `LYSO_2in`.  They have the round-1
cause, the standard EM option attenuating 662 keV photons slightly more
than the NIST tables.  FTFP_BERT is below NIST in all 21 shield and crystal
cases, while EMZ and LIV scatter around it.

## Findings

- **Shield:** at equal mass (22.7 g/cm²), lead gives 18–27 % less dose than
  tungsten and about half that of iron or concrete.  At 40 mm of lead the
  build-up factor reaches 2.4–2.5.
- **Calorimeter:** 1 mm lead with 2 mm active layers gives the best
  electron resolution.  Liquid argon is best of all (σ/E 0.055–0.058 at
  1 GeV).  Fine tungsten sampling comes within 3–7 % of it in 10 % less
  depth.  Halving the layer thicknesses improves σ/E by 20–27 % for every
  absorber/active pair.
- **Detector:** at the mass of a 3 × 3 inch NaI, BGO gives 27–30 % more
  full-energy-peak efficiency.  With resolution applied, LaBr₃ has the
  purest peak and BGO the highest peak-to-Compton.
- **Physics lists:**
  - FTFP_BERT simulates no X-ray escape in the crystals, while EMZ and LIV
    do.  This explains part of FTFP_BERT's higher high-Z peak efficiency,
    which round 1 attributed to attenuation alone.
  - In the calorimeter, QGSP_BIC and FTFP_BERT differ by about 1 % in the
    sampling fraction of two designs, for a reason not yet understood.

## Setup

| | |
|---|---|
| Machine | MacBook Air, macOS 26.1, arm64 |
| GDML | FreeCAD 1.1.4, GDML workbench 2.2.16 (commit 2d7a5776), studies at commit 3fc0a90 |
| Simulation | Geant4 11.4.3 (conda-forge) |
| Analysis | shield and calorimeter at 3fc0a90; detector re-analysed at 3124427 (energy resolution) |
| Statistics | as round 1: shield 100 000 photons; detector 100 000 (cone) and 50 000 (pencil); calorimeter 2000 e⁻ and 500 π⁺ per run |

## Contents of each study folder

As in round 1: `REVIEW.md`, `review_input.md`, `metrics.csv`,
`flags.json`, `plots/`, and a selection of `render/` slices of the new
variants.  The full results stay in `results/`, which is not committed.

## Follow-up

The reviews propose the following, for approval:
- **shield:** no new geometry.  A second photon energy (needs per-source
  reference μ/ρ).  4× photons if the Pb_40mm dose matters.
- **calorimeter:** W0p7_LAr2_x120 and Pb0p5_Sc1_x240.  8000 electrons per
  run.  A tail-insensitive resolution metric.
- **detector:** LaBr3_2in.  A multi-line source (e.g. Ba-133 356/384 keV)
  to test resolution.  An FTFP_BERT run with fluorescence switched on,
  to test the X-ray-escape explanation.

The `hcal` study (three variants approved) has not been run yet.
