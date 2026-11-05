# Locked paired ratings and source-limited validation

The corrected R1 and R2 sets each contain 663 positions in 176 trial units. The authors report that the sets were formed separately before discussion. Prior project exposure is disclosed throughout. Matching answers are not used to infer either non-independence or scientific accuracy.

The source-scoped and cumulative labels match across the two sets at 663/663 positions. The descriptive kappa is 1 where margins contain more than one category; it is **undefined**, represented as JSON `null`, when both margins are degenerate. The set deliberately enriches complete and unknown positions. Repeated positions occur within trials. Neither the unweighted nor design-weighted agreement estimates a trial-level error rate, external validity, or classification accuracy. No confidence intervals or clinical effects are calculated.

## Limits of the returned examination

- Each reviewer declares original primary-source examination for 333/663 positions; 330 do not establish such examination.
- The returned labels mark 20 positions complete. Directed AI technical reconciliation preserves the 57 historical complete witnesses, including 37 whose new source-limited labels are unknown. This does not replace the raw human labels or constitute a new human vote.
- The 462 raw indicator differences from the historical scope are not 462 demonstrated scientific errors. Historical coded inputs and numerical results remain unchanged; the integration log records the retained historical action separately.
- No new irreducible primary-content conflict or new reviewer case was identified in this integration. This does not mean all methodological limitations are resolved or full independent source re-extraction is complete.
- The 30-unit alternative-reference pilot found source-specific flow/exposure metadata but no compatible target-outcome numerators. `STARTED` is not automatically an ITT outcome denominator, an exposed/safety total does not establish the exact on-treatment observation window, and unknown numerators are not zero events. No numerical ITT/on-treatment outcome sensitivity was completed.
- Source routes recovered after the returned forms were locked establish availability of hash-matched bytes, not subsequent human reading or scientific resolution. Named inventory slots are not automatically separate clinical reports. Read `SOURCE_ROUTE_RECONCILIATION.json` and its delta with these distinctions.

The protocol under `../validation_protocol/` is the preserved, dated design snapshot. Its pending-return status describes the state **before** the new locked returns. The current state is `VALIDATION_STATUS.json`; the earlier protocol files have not been rewritten to simulate a different chronology.

## Files and reproduction

| File | Purpose |
|---|---|
| `PAIRED_RATINGS_663.json` | Minimal paired labels, six-part position keys, design strata/weights, source IDs and private-input hashes; no raw personal response prose |
| `AGREEMENT_RESULTS.json` | Expected descriptive agreement, cross-tabulations, subgroup and design-weighted results |
| `AGREEMENT_REPORT_METADATA.json` | Report wording and extra reported coverage aggregates not derivable from the minimised paired labels |
| `VALIDATION_STATUS.json` | Current integration state and unresolved limits |
| `INTEGRATION_DECISION_LOG_663.json` | Historical action versus raw returned labels; no scientific input substitution |
| `TECHNICAL_WITNESS_RECONCILIATION_57.json` | AI technical witness reconciliation, source hashes and limited scopes |
| `PILOT_SUMMARY.json` and `ALTERNATIVE_REFERENCE_SEMANTIC_LIMITS.json` | Partial alternative-reference feasibility and denominator/window cautions |
| `MECHANISMS_AND_SOURCE_SCOPE.json`, `RETURNED_DIMENSION_SUBCODES_AND_COVERAGE.json`, `DIMENSION_INTERPRETATION_GUARDS.json` | Nonexclusive, coverage-limited administrative and documentary signals; not trial-level cause prevalence |
| `SOURCE_ROUTE_RECONCILIATION.json` and `SOURCE_ROUTE_RECONCILIATION_DELTA.json` | Sanitised current access routes and change from the earlier access audit; availability does not certify examination |

Run with Python 3.10 or newer, standard library only:

```sh
python validation/reproduce_agreement.py --check
python validation/reproduce_agreement.py --check --out replay/AGREEMENT_RESULTS.json
```

The script computes all agreement cells, margins, kappa values, modality/layer subgroups and design-weighted point estimates from the paired labels. Rational design weights use exact fractions before final JSON conversion. It validates selected-stratum counts and label/indicator consistency. It also recomputes paired label/source coverage. Report wording and additional raw-field aggregates (timestamps, count-field types, mechanism codes and pilot labels) are explicitly supplied as reported metadata because those private raw fields are not redistributed. They are not presented as newly calculated from the minimal pair. The generated report must equal the expected JSON structurally; metadata does not supply any agreement cells.

`../reproduce.py --check` runs this check after reproducing the unchanged scientific results. Reproduction verifies computational consistency; it does not replace source examination or certify the authors' human-provenance declarations.
