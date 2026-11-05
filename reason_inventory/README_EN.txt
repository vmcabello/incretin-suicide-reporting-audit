RECORDED DOCUMENTARY SIGNAL INVENTORY
Version: EJCP-MAJOR-REASONS-20261104

Scope
This is an administrative inventory of explicit codes retained in historical authorial annotations, linked to current frozen documentary statuses. It does not quantify the prevalence of reporting defects, trial-level causes of non-reconstruction or actual use/non-use of instruments. All historical annotation rows explicitly disallow corpus-frequency inference.

Reproduce with Python 3.10 or later (standard library only), from the repository root:
    python reason_inventory/quantify_recorded_reasons.py --repository . --out reason_inventory/generated

The source annotation input is supplied in REASON_ANNOTATION_INPUT_5096.jsonl.gz. It is a minimal projection of authorial codes, preserving the fields used in these counts. REASON_ANNOTATION_PROVENANCE.json identifies its parent artifact and the projection. Original public analysis inputs/code remain unchanged.

Key files
- TABLE_S8_CANDIDATE_ADMINISTRATIVE_SIGNAL_INVENTORY.json/.tsv: illustrative supplementary table with absolute recorded-position counts and current complete/unknown/not-complete groups.
- POSITION_REASON_LEDGER_5096.jsonl.gz: one uniquely keyed row per existing documentary position, including source-scope limitations, coded signals and current cumulative access-gap IDs.
- RECORDED_SIGNAL_COUNTS.json/.tsv: count breakdown for full and post-hoc strata/layers.
- DIMENSION_SUBCODE_COUNTS.json/.tsv: six dimension-code counts in historical 5,096 and technical 426 batches. These overlapping batches must not be added or called independent reviews.
- COVERAGE_AND_INFERENCE_LIMITS.json: inferential limits and explicit unestimable categories.
- EXPLICIT_INCOMPATIBILITY_EVIDENCE_INDEX.json: retained positive incompatibility codes, with original source-scoped evidence text.
- ALTERNATIVE_REFERENCE_PILOT_FEASIBILITY.json: five illustrative post-hoc candidates; no clinical or documentary sensitivity estimate was computed.
- QA_RECORDED_REASONS.json: structural checks only, not scientific validation.

Denominators
The full frame is 5,096 positions = 182 units x 28 component/layer/modality cells. The post-hoc 159-unit B3 frame is 1,113 positions = 159 units x 7 component/modality cells. Units, source information and judgments repeat across these cells. Multiple signals coexist; rows must not be summed. Distinct unit identifiers are descriptive only, not independent observations.

Interpretation
A zero recorded count means there is no positive code in that field, not proof that the underlying mechanism was absent. DO_NOT_INFER_STRUCTURED_ASSESSMENT is not a code for confirmed instrument non-use. POOLED_OUTPUT_NOT_UNIT_ATTRIBUTABLE does not separately identify between-arm versus between-trial pooling. Current access-gap bindings and historical reason annotations have different scopes and can coexist with a valid complete witness.

Validation
No new primary reading, human scientific judgment, independent inter-rater agreement or reclassification is claimed. This inventory cannot determine the relative contributions of reference choice and public-reporting limitations. That requires source-based independently coded reference-specific extraction.
