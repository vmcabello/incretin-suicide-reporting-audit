# Essential data dictionary

An **operational unit** is a retained randomized drug/placebo contrast. Families, bibliographic records, clinical reports and documentary positions are separate levels. A position has six identity fields: `unit_id`, `component`, `stage`, `modality`, `reference_id`, `window_id`. Its target is baseline-eligible exposed participants under original allocation over the initial parallel phase plus applicable planned post-discontinuation observation.

Components are suicidal ideation, suicide attempt and suicide death. Layer A admits main articles and supplements; B1 adds secondary reports; B2 adds registry results; B3 adds compatible regulatory evidence. Modalities are adverse-event reporting, suicide-specific structured assessment and all-cause mortality derivation. Completeness in one modality cannot fill another.

`complete_direct` and `complete_derived` require a compatible witness for the exact target in both arms, including all required numerators, denominators, populations, counting units and windows. A derived proof additionally requires a valid operation. `partial_reference` and `not_reconstructible_in_examined_corpus` describe bounded examined scopes, not clinical zeros. `public_source_unavailable`, `reference_unverifiable`, conflicts and pertinent unresolved source/target dimensions yield unknown. An incompletely examined scope can therefore retain the raw label `partial_reference` while its **analytical indicator is unknown**.

The indicator is existential for an exact valid complete witness. Additional unread or inaccessible sources do not negate that witness without a material contradiction. Without such a witness, pertinent unresolved earlier gaps remain unknown in later cumulative layers. Positive witness reuse requires all sources needed for the proof to be admissible in the receiving layer; no B2/B3 source is imported backward into an article-only proof. Additional keys changed by this rule are technical deductions linked to their origin, not new human ratings.

## Current source-linked integration

`source_review109/` is the current integrated version. `current_input/`, `current_analysis/`, `input_snapshot/`, `validation/` and `validation_sensitivity/` are preserved historical snapshots; their previous counts and statuses are not overwritten.

The 109 follow-up positions in 59 dossiers are a subset of the preceding 663-position assessment frame. The 37 formerly indeterminate historical positives are confirmed in this follow-up; together with the preceding 20 confirmations, all 57 historical positives are confirmed across the two internal exercises. The sampled 72 historical negative positions yield four new derived-complete judgments; this is not a corpus error-rate estimate. The original two-phase probabilities and 56 strata remain available in `linked_review_protocol/`.

| Concept | Meaning |
|---|---|
| Raw source-scoped or cumulative classification | Received reviewer vote preserved as reported; scope differences are not automatically scientific errors |
| Source-scope coverage | `sufficient_positive_witness_examined`, `comparable_relevant_source_union_examined` or `incomplete_relevant_scope`; 13 follow-up scopes remain incomplete |
| Integrated effective indicator | 1 for a compatible complete proof; 0 only for an examined closed negative/partial scope; unknown for unresolved pertinent coverage or dimensions |
| Principal cumulative integration | Carries valid admissible proofs and unresolved pertinent source gaps across the exact component/modality/reference/window, retaining provenance |
| Exact-key sensitivity | Applies the follow-up judgments on their exact keys under its documented handling; unreviewed-key extrapolation is not performed |
| Technical deduction | A separately logged consequence on another admissible layer, never labelled an additional human vote |
| Historical positive-only scenario | v1.3.0 sensitivity setting the then-unconfirmed 37 positives to unknown; retained as a dated comparison, superseded as current follow-up status |

Exposure denominators, respondent denominators, ITT populations, people and episodes remain distinct. STEP UP has 1004/201/201 exposed versus 1005/201/201 randomized participants. OASIS 4 uses 204/102 exposed, not 205/102 randomized. STEP 1 retains its inconsistent fatal-person/event count and cause enumeration rather than inventing three unique deceased placebo participants. The attempt-zero proof for SURMOUNT-2 uses exhaustive AE case attribution, not mortality zero. AWARD-10 uses the corrected 23 May 2018 article version.

For admitted N units, k confirmed and u unknown, the corpus-conditional identification interval is k/N to (k+u)/N. It is not a confidence interval, clinical risk or treatment effect. It does not encompass unidentified trials, selection error or classification error. The 159-unit hierarchy and modality-first presentation are post hoc. No numerical clinical ITT/on-treatment outcome sensitivity can be inferred merely from the 30-unit source-metadata pilot.

Human independence and reading extent are author-reported process declarations, not externally certified attributes. Agreement within this internal exercise does not establish accuracy, and 109 follow-up positions must not be added to 663 as 772 independent positions. Source hashes and catalogue navigation fields certify neither reading nor historical cutoff availability. Source versions at 19 October 2026 are not uniformly established; no complete vital-status ascertainment or full uniform source extraction is claimed.
