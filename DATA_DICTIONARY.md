# Essential data dictionary

An **operational unit** is a retained randomized drug/placebo contrast. Families, bibliographic records, clinical reports and documentary positions are separate levels. A position has six identity fields: `unit_id`, `component`, `stage`, `modality`, `reference_id`, `window_id`. Its target is baseline-eligible exposed participants under original allocation over the initial parallel phase plus applicable planned post-discontinuation observation.

Components are suicidal ideation, suicide attempt and suicide death. Layer A admits main articles and supplements; B1 adds secondary reports; B2 adds registry results; B3 adds compatible regulatory evidence. Modalities are adverse-event reporting, suicide-specific structured assessment and all-cause mortality derivation. Completeness in one modality cannot fill another.

`complete_direct` and `complete_derived` require a compatible witness for the exact target in both arms, including all required numerators, denominators, populations, counting units and windows. A derived proof additionally requires a valid operation. `partial_reference` and `not_reconstructible_in_examined_corpus` describe bounded examined scopes, not clinical zeros. `public_source_unavailable`, `reference_unverifiable`, conflicts and pertinent unresolved source/target dimensions yield unknown. An incompletely examined scope can therefore retain the raw label `partial_reference` while its **analytical indicator is unknown**.

The indicator is existential for an exact valid complete witness. Additional unread or inaccessible sources do not negate that witness without a material contradiction. Without such a witness, pertinent unresolved earlier gaps remain unknown in later cumulative layers. Positive witness reuse requires all sources needed for the proof to be admissible in the receiving layer; no B2/B3 source is imported backward into an article-only proof. Additional keys changed by this rule are technical deductions linked to their origin, not new human ratings.

## Current corrected-return reconciliation

`source_review109_reconciled/` contains current reconciled results. `source_review109/` is the preserved v1.4.0 snapshot; its old current/pending/agreement labels are historical. The same applies to earlier `current_input/`, `current_analysis/`, `validation/` and `validation_sensitivity/` files. Use `CURRENT_STATUS_INDEX.json` to resolve status by version.

The two raw corrected-return assessment sets remain separate from the analytical dispositions. Their process is described as **separate internal assessments, as declared by the authors**. Similarity of earlier exported prose cannot prove or refute that declaration. Raw current R2 classifications differ from R1. Pairwise agreement is measured before AI-assisted technical conciliation and is not accuracy, an error-rate estimate or external validation.

| Concept | Meaning |
|---|---|
| Raw human classification | Supplied R1 or corrected R2 rating; retained without rewriting divergent votes |
| Source-scope coverage | Declared sufficient positive witness, comparable relevant examination or incomplete relevant examination; distinct from access to bytes |
| Technical analytical disposition | Separately documented application of the retained instrument and source evidence after disagreement; not a third human vote |
| Conservative current indicator | Complete only with a compatible admissible proof; unknown for unresolved pertinent scope; bounded not-complete status only within established examined scope |
| Positive-proof reuse | Same exact reference/component/modality/window, with every required source hash already admissible in the receiving layer |
| Sensitivity without scope-gap propagation | Retains accepted proofs but does not automatically carry a new incomplete scope into later cells |
| Historical annotations | Recorded mechanism/status inventory before corrected-return reconciliation; not fresh prevalence estimates |
| Author conference | Version-specific review of exact files; does not automatically extend to later corrected-return analyses |

The 109 positions in 59 dossiers are a subset of the earlier 663-position frame, not 772 independent positions. Counts of positions, units, episodes, participants and positive assessments are different. An explicit zero of fatal adverse events can support a within-AE derived proof; omission of a suicide row cannot. Pooled zero suicides require a subset derivation for identified own-trial arms and are not directly tabulated arm-specific counts.

STEP UP preserves 1004/201/201 treated versus 1005/201/201 randomized. OASIS 4 preserves 204/102 exposed rather than 205/102 randomized. STEP 1 retains the fatal-event/person discrepancy in its source. AWARD-10 uses the corrected 23 May 2018 article and the planned 24-week protocol window, not passive related-SAE notification indefinitely after discharge. These distinctions do not certify complete vital-status follow-up.

For N admitted units, k complete and u unknown, the identification interval is k/N to (k+u)/N, conditional on corpus, reference and coding. It is not a confidence interval, clinical risk, treatment effect or protection against missed studies and selection/classification errors. The analysis hierarchy remains post hoc. Source versions at 19 October 2026 are not uniformly certified.
