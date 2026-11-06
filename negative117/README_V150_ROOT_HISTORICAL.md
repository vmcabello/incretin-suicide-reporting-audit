# Incretin therapy suicide-related outcome reporting audit

Data and code for **Public reconstructibility of suicide-related outcomes in a historical corpus of trials of GLP-1 receptor agonists and tirzepatide**.

Vitor Motta Cabello dos Santos ([ORCID 0000-0002-0667-7288](https://orcid.org/0000-0002-0667-7288)) and Guilherme Keltke ([ORCID 0009-0007-5415-0572](https://orcid.org/0009-0007-5415-0572)). Both are unaffiliated, Campinas, São Paulo, Brazil.

## Public support release v1.5.0

This is the versioned [v1.5.0 public support release](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.5.0), containing author-owned data and analysis code. Publication of this support is not a manuscript preprint, approval of revised manuscript files or journal submission. `CURRENT_STATUS_INDEX.json` distinguishes current analysis, preserved snapshots and version-specific author conference.

The corpus remains fixed: 182 operational units, 159 in the post-hoc whole-population stratum and 170 with supported populations including subgroups. Its 5,096 positions distinguish component, modality, cumulative source layer, reference population and window; a position is not a trial. No exhaustive trial universe or clinical treatment effect is claimed.

**Current reconciled results are in `source_review109_reconciled/`.** `source_review109/` remains the byte-exact published v1.4.0 export and analysis. Its old current-status, 109/109-agreement and pending-author-conference labels describe that historical snapshot. `current_input/` and `current_analysis/` also retain historical names and bytes; those names do not make them the newly reconciled analysis.

The corrected R2 differs from R1 in raw ratings and source scope. These are **separate internal assessments, as declared by the authors**, with prior project exposure. Narrative identity in earlier exports cannot prove or refute declared separation. Neither identical nor divergent exports independently certify reading, memory blinding or external validation. Agreement is calculated on raw paired classifications before technical reconciliation; it does not estimate accuracy.

The user-authorized AI-assisted technical conciliation retains discrepant raw votes and records separate analytical dispositions. It is not human adjudication or a third human vote. Incomplete relevant examination remains unknown unless compatible evidence resolves that exact target. Positive proofs can be reused only where all indispensable source hashes are already admissible, with the same reference, modality and window. No later registry or regulatory source is imported into an earlier article-only layer. Technical deductions are separately logged.

The 109 follow-up positions in 59 dossiers are nested in the earlier 663-position frame; they are not 772 distinct independent observations. The new module supplies raw paired cross-tabulations, scope coverage, reconciliation decisions, results by modality, secondary unions, direct-only sensitivity and scenarios. Consult its machine-readable editor summary for the reconciled numerical results rather than carrying forward the earlier agreement or unknown counts.

Direct and derived proofs remain distinct. The death union increased in the v1.4.0 comparison through STEP 1 and AWARD-10; NCT02160990 added an AE proof but was already death-complete through mortality derivation. SURMOUNT-2 supplied the additional attempt unit. These four positions were not four additional complete union units. Newly recognized examination gaps can increase unknowns independently of confirmed positive proofs. The revised reconciliation also examines STEP UP fatal-AE zero within its own AE modality and preserves derived rather than direct labeling for pooled SURMOUNT-2 death evidence.

Corpus-conditional identification intervals hold the admitted corpus, reference and coding fixed. They are not confidence intervals, clinical risks or bounds for all trials. They do not encompass missed trials, selection or classification error. Source versions at 19 October 2026 are not uniformly certified, and a zero report does not establish complete vital-status follow-up.

### Current secondary union at B3 (N=159)

| Outcome | Complete units | Unknown units | Corpus-conditional interval |
|---|---:|---:|---:|
| Ideation | 1 (1 direct; 0 derived) | 37 | 0.63%–23.90% |
| Attempt | 2 (1 direct; 1 derived) | 33 | 1.26%–22.01% |
| Death | 17 (0 direct; 17 derived) | 39 | 10.69%–35.22% |

The principal presentation remains modality-specific; this secondary union combines non-equivalent modalities. Death has four AE-derived and fifteen mortality-derived units, with two overlaps. Relative to v1.4.0, the complete union counts are unchanged while unknowns increase from newly preserved examination gaps. Raw cumulative-label agreement is 85/109 and source-scoped-label agreement 79/109 before AI technical conciliation. These are descriptive internal agreements, not accuracy estimates.

## Reproduce current and historical results

Python 3.10 or newer, standard library only; no network or package installation is required.

```sh
python reproduce.py --check
```

The command verifies root and module manifests, reproduces every preserved historical analysis and the new corrected-return reconciliation, checks expected result bytes and regenerates omitted large integrated inputs by hash. The inherited tests, search-subset crosswalk checks, fixed sampling-design replay and historical positive-only sensitivity remain enabled. The immutable v1.4.0 search-subset validator runs on the same saved search bytes in a temporary view with the exact frozen v1.4.0 chronology; a separate current guard checks the seventeen-event prefix and new dated additions. Frozen chronology JSON and HTML are distributed, so replay requires no git history. GitHub Actions uses the same command on Python 3.10 and 3.12. The existing `--out` argument continues to export the historical result, not the new reconciliation.

## Current and historical map

| Path | Role |
|---|---|
| `source_review109_reconciled/` | Current corrected-R2 ratings, paired disagreements, AI technical conciliation, code and expected results |
| `source_review109/` | Immutable v1.4.0 paired export and integration, including its then-current statuses and numerical results |
| `current_analysis/`, `current_input/`, `input_snapshot/` | Preserved historical inputs, rules and expected results |
| `validation/`, `validation_protocol/` | Earlier 663-position exercise and fixed protocol |
| `validation_sensitivity/` | Historical v1.3.0 positive-only scenario, not current findings |
| `linked_review_protocol/` | Original fixed 109-position protocol, seed, neutral roster and probabilities |
| `reason_inventory/` | Historical coverage-limited code inventory, not regenerated as current mechanism frequencies |
| `search_trace/` | Record-level update decisions, nominal new-identifier subsets and reproducible crosswalks |
| `corpus/` | Families, blocks, units, population strata and additive chronology |
| `corpus/PUBLIC_TRANSITION_121_TO_122.json` | Retrospective 5 November verification of the prior EXSCEL roster-propagation correction |
| `CURRENT_STATUS_INDEX.json` | Current-versus-historical labels and version-specific author status |
| `MANIFEST.json` | Exact integrity inventory |

The original seventeen chronology events remain unchanged. Later entries record corrected-R2 receipt, authorized AI conciliation, the 121-to-122 clarification, preparation of this version and authorization to publish the data/code support, without backdating new verification. The prior 121 units and 3,388 positions were unchanged when EXSCEL was added with 28 pending positions; this was not a new search hit or a new human inclusion vote.

The authors conferred the exact earlier v1.4.0 documents on 5 November 2026. That dated conference remains valid for its pinned files and hashes. It does not approve new corrected-R2 results or subsequently changed manuscript/submission files. The new scientific revision has not been recorded as author-conferred. Historical pending build receipts are preserved as creation-time history, not current instructions. No journal submission or payment is recorded.

Full third-party texts, quoted clinical passages, licensed native exports, personal raw returns, private local paths and coordinator keys are not included in the new projection. Source identifiers and hashes identify bytes, not a certificate of reading. Historical source data and tags remain available. No archival DOI is claimed.

## Reuse and citation

Author-owned software is MIT licensed; author-owned classifications and documentation are CC BY 4.0, subject to third-party rights. Retain attribution and describe modifications. Use `CITATION.cff` or the [v1.5.0 release](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.5.0) to cite this data/code version. The [v1.4.0 release](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.4.0) remains available for that exact historical snapshot.
