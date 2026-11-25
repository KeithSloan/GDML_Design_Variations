# Review guide (stage 5)

How an AI reviewer (or a person) turns `results/<study>/review_input.md`
into `results/<study>/REVIEW.md`.  The analysis script has already made
every mechanical check; the review interprets them and answers the study's
objective.

## Inputs

- `results/<study>/review_input.md`: the objective, variants, run status,
  flags, reference checks, ranking, physics-list differences, metric tables
- `results/<study>/plots/*.png` and `render/*.png`
- `results/<study>/metrics.csv`, `flags.json` for exact values
- `studies/<study>/study.toml` and `metrics.py` for what each metric means
- for a problem run: `runs/<run>/g4.log`, `summary.json`, `gdml/<variant>.json`

## Steps

1. **Validity first.**  Read the Flags section.
   - Failed or missing runs: list them; conclusions must not rely on them.
   - Overlaps (`geometry` flags): the geometry is wrong; results for that
     variant are invalid until the design is fixed.
   - Reference mismatches: a disagreement with an analytic or tabulated
     value (e.g. uncollided fraction vs NIST attenuation) means the
     geometry, a material or the physics is not what was intended.  Treat
     it as a defect to investigate, not as a property of the design.  Say
     which runs are affected.
   If validity problems affect the answer, say so at the top and stop
   short of a recommendation that depends on them.

2. **Statistics.**  Two values whose difference is within about 3 combined
   standard errors are not different.  If the ranking for the primary
   metric depends on such differences, say so and say how many more events
   would separate them (errors scale as 1/sqrt(events)).

3. **Physics-list dependence.**  For each significant difference between
   physics lists: is it large enough to change the ranking or the
   recommendation?  Electromagnetic options (EMZ, LIV) mostly matter at low
   energy; hadronic models (FTFP_BERT vs QGSP_BIC) matter for hadron
   showers.  A conclusion that holds for all lists is robust; one that does
   not is model-dependent and must be reported as such.

4. **Answer the objective.**  Rank the variants on the primary metric and
   give the trade-offs named in the objective (mass, depth, cost of
   material, peak-to-total...).  Where two quantities trade off (e.g. dose
   vs areal density), name the variants that are best for each, and those
   that are worse on both.

5. **Look at the pictures.**  Check that the geometry in the material
   panels is what the design intended, that the beam hits what it should,
   and that energy is not deposited where there is no material.  Report
   anything odd, with the file name.

6. **Propose the next round.**  Suggest at most a handful of new or changed
   variants as `[[variants]]` entries for `study.toml`, each with the
   question it answers (e.g. narrow down an optimum, test a model-dependent
   conclusion).  Suggest more events where statistics limited the answer.
   These are proposals for approval; do not edit `study.toml` or start runs.

## REVIEW.md layout

```markdown
# Review: <study title>
Reviewed: <date>, from review_input.md generated <date>, <N> runs.

## Summary            three to five sentences: the answer and how sure it is
## Validity           failed runs, overlaps, reference checks (pass/fail counts)
## Results            ranking and trade-offs, values with errors
## Physics-list dependence
## Recommendation
## Proposed next variants   (TOML block + one line of reason each)
## Limitations        what this study cannot tell you
```

## Rules

- Every number comes from the inputs above, with its error, and names the
  run or metric it belongs to.  No numbers from memory; no estimates
  presented as results.
- Deposited energy is not a detector signal: no resolution, light
  collection or electronics are simulated.  Say so where it matters (e.g.
  peak efficiencies are upper limits).
- Keep the review to what the study measured.
