# Round 1 results (25 November 2026)

The first full-statistics run of the three sample studies, and the AI
reviews of it (stage 5 in [docs/WORKFLOW.md](../../WORKFLOW.md)).

| Study | Runs | Reference checks | Review |
|---|---|---|---|
| shield | 30/30 ok | 29/30 pass | [shield/REVIEW.md](shield/REVIEW.md) |
| calorimeter | 36/36 ok | 18/18 pass | [calorimeter/REVIEW.md](calorimeter/REVIEW.md) |
| detector | 36/36 ok | 17/18 pass | [detector/REVIEW.md](detector/REVIEW.md) |

No run reported a geometry overlap.  The two failed reference checks
(`W_10mm` and `CsI_1p5in`, both with FTFP_BERT) have the same cause.
FTFP_BERT, with the standard EM option 0, gives uncollided photon
fractions 0.3–2.9 % below the NIST tables in all 15 shielded cases, while
FTFP_BERT_EMZ and FTFP_BERT_LIV agree with them.  It is a physics-model
effect, not a geometry or material error (see the shield and detector
reviews).

## Setup

| | |
|---|---|
| Machine | MacBook Air, macOS 26.1, arm64 |
| GDML | FreeCAD 1.1.4, GDML workbench 2.2.16 (commit 2d7a5776), studies at commit 6465bcd |
| Simulation | Geant4 11.4.3 (conda-forge), `gdmlvar` 0.1.0 at commit 1cfcd00 |
| Statistics | shield 100 000 photons; detector 100 000 (cone) and 50 000 (pencil); calorimeter 2000 e⁻ and 500 π⁺ per run |

## Contents of each study folder

| File | |
|---|---|
| `REVIEW.md` | the review: validity, results, physics-list dependence, recommendation, proposed next variants |
| `review_input.md` | the packet the review was written from (`pipeline/analyse.py`) |
| `metrics.csv`, `flags.json` | every metric with its error; every check and flag |
| `plots/` | metric plots, one series per physics list |
| `render/` | selected x–z slices of material and energy deposit (FTFP_BERT runs) |

`review_input.md` lists every render; only a selection is kept here.
The full results, including `mesh.vti` for every mesh run, stay in
`results/`, which is not committed.

## Follow-up

The variants proposed in the reviews were approved for round 2:
- **shield:** W_12mm, Fe_29mm, Pb_40mm;
- **calorimeter:** W0p7_Sc2_x120, Pb1_LAr2_x120;
- **detector:** BGO_2in, BGO_eqmass_NaI3in, LYSO_2in.

The hadron-calorimeter study and the detector-resolution metric proposed
in the calorimeter and detector reviews are separate pieces of design
work.
