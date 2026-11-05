# Incretin therapy suicide-related outcome reporting audit

Data and code accompanying **Public reconstructibility of suicide-related outcomes in a historical corpus of trials of GLP-1 receptor agonists and tirzepatide**.

Vitor Motta Cabello dos Santos (ORCID [0000-0002-0667-7288](https://orcid.org/0000-0002-0667-7288)) and Guilherme Keltke (ORCID [0009-0007-5415-0572](https://orcid.org/0009-0007-5415-0572)). Both authors are unaffiliated, Campinas, São Paulo, Brazil.

## Scope

This is an exploratory documentary audit of a fixed historical corpus. It asks whether public reporting supports arm-specific reconstruction for an explicit population and observation window. It does not estimate a clinical suicide risk or a treatment effect, and does not claim exhaustive trial ascertainment.

- 182 operational units; 159 in the post-hoc whole-population stratum; 170 with supported populations including subgroups.
- 5,096 documentary positions across outcomes, source layers and modalities.
- 57 complete positions, 1,009 unknown positions and 4,030 not-complete positions. Positions are not distinct trials.
- In the 159-unit B3 secondary union, confirmed reconstructions are 1 for ideation, 1 for attempt and 15 for death, with 26 unknown units per outcome. The death reconstructions are derived proofs. Main results keep modalities and direct/derived proofs separate.

Corpus-conditional identification intervals vary coded unknowns within the admitted corpus; they do not cover missed trials or selection/coding error. Full vital ascertainment is not established by a compatible zero-mortality report. Paired agreement is reported separately from technical witness reconciliation and does not establish accuracy.

## Additions in v1.3.0

This supporting revision links the source-limited human reassessment explicitly to a numerical sensitivity. It does not replace, correct, or re-adjudicate the historical primary analysis. Of 57 historical complete positions, 20 remained complete in both current human returns and 37 remained unknown within the current source coverage. The latter are not demonstrated errors. Verification of their original source packages remains pending. A public protocol and neutral roster now specify a targeted follow-up of those 37 positives plus a two-phase sample of 72 historical not-complete positions, covering 109 positions in 59 units. Those assessments have not been completed; no new human decisions are inferred.

`validation_sensitivity/` preserves a positive-only scenario: only those 37 exact position statuses become their concordant current unknown label; all other 5,059 position statuses remain unchanged, including the 20 currently confirmed positives. The 5,039 positions outside the historical complete census are held fixed. Human labels, source records, proof flags, populations, windows, references, and modality/layer keys remain unchanged. This is not a wholesale replacement with the 663 source-limited reassessments, an accuracy estimate, or an extrapolation to unreviewed positions.

In the whole-population B3 secondary union (N=159), ideation and attempt each remain one direct reconstruction and 26 unknowns (0.63%-16.98%). Death changes from 15 derived reconstructions and 26 unknowns (9.43%-25.79%) to five derived reconstructions and 36 unknowns (3.14%-25.79%). These intervals are conditional on the corpus and the illustrative coding scenario. The full unit/position bridge, 84 modality cells, 36 union cells, nine direct-only summaries, and 12 illustrative membership scenarios are reproducible separately from the primary results.

The search trail now marks nominal membership in the "new identifier" subsets directly on all 2,558 saved representations. The additional validator reproduces Table S1 from those flags and distinguishes the 14 PubMed native-export identifier differences already known to the master library. The protocol chronology now includes the November reassessment, author conference, and subsequent requested matched-source verification. Identifier subset membership creates no eligibility or classification vote.

Run `python reproduce.py --check` to reproduce the unchanged primary results, the existing coverage-limited code inventory and agreement analysis, the marked search subsets, and the new sensitivity. The additional 14 synthetic checks test the exact positive-only projection, valid-witness priority, unknown propagation, and separation of modalities and source layers. No manuscript preprint or full third-party report is distributed.

## Prior additions in v1.2.0

This version adds corrected locked paired returns and source-limited descriptive agreement. The earlier tagged versions remain available. No renewed final manuscript approval or journal submission is inferred.

The two 663-position sets are preserved as returned in a privacy-minimised paired dataset. The authors declare separate assessment before discussion and disclose prior project exposure. Descriptive paired-label agreement is 663/663; kappa is 1 for nondegenerate margins and undefined for single-category margins. Agreement does not establish accuracy or full source re-extraction. Each reviewer declares original primary-source examination for 333/663 positions; the remaining 330 do not establish such examination.

The new human labels identify 20 complete positions. AI technical reconciliation retains all 57 historical positive witnesses, including 37 whose new source-limited human labels are unknown. Raw labels are not overwritten; 462 scope differences are not treated as 462 errors. The v1.2.0 technical integration identified no irreducible primary-content conflict; this did not establish complete matched-source human verification. The subsequent targeted verification remains pending. The 30-unit alternative-reference pilot contains partial source metadata and no compatible target-outcome numerators, so it does not provide a numerical ITT/on-treatment outcome sensitivity.

All historical scientific input, classification and numerical reconstruction-result bytes are unchanged. The earlier search trail, coverage-limited code inventory and protocol are retained:

- `search_trace/`: 2,558 saved database representations, 745 screening cases, recorded decisions and rationales, 1,717 reused prior-library groups, supported corpus links and itemised missing information. An identifier route is not scientific closure. Twelve prior-group rationales remain unrecovered; unestablished final links remain explicit.
- `reason_inventory/`: position-level code inventory and portable reproducer. All historical annotations prohibit corpus-frequency inference. Code counts are not prevalence estimates of trial-level causes or of instrument non-use.
- `validation_protocol/`: the dated design snapshot (57 historical complete positions, the preserved 426-position not-complete sample and 180 sampled unknowns), plus a nested 30-unit alternative-reference pilot. Its pending-return status is historical and remains unedited. Separate unfilled reviewer instruments remain in the local author package.
- `validation/`: minimal locked paired ratings, descriptive cross-tabulations and agreement, source-scope limits, pilot, technical positive-witness reconciliation, integration actions, and sanitised source-route reconciliation. Recovery of 353 hash-matched file bindings establishes local availability, not new human reading. The remaining 135 bindings name 27 pre-existing inventory slots; they are not 135 distinct missing clinical reports. Current integration status is recorded here rather than retroactively changing the protocol.

Run `python reproduce.py --check` to verify integrity, reproduce the unchanged numerical results and the added descriptive agreement, and validate the supporting exports. Extra reported raw-field coverage aggregates are distinguished from calculations reproducible from the minimal pair. This is research support material, not a journal major-revision decision or a manuscript preprint.

## Reproduce the results

Python **3.10 or newer** is sufficient. The analysis uses only the standard library and needs no network access or package installation.

```sh
git clone https://github.com/vmcabello/incretin-suicide-reporting-audit.git
cd incretin-suicide-reporting-audit
python reproduce.py --check
```

This verifies the public file manifest, runs the 34 inherited analysis regression checks, recomputes the unchanged primary results and requires a byte-for-byte match to `current_analysis/RESULTS_BY_MODALITY.json`. It also reproduces the coverage-limited code inventory, checks the search trace and marked new-identifier subsets, recomputes descriptive paired agreement with subgroup/design weights, and exactly reproduces all 13 files of the positive-only sensitivity after 14 additional synthetic checks. To retain the historical primary output file:

```sh
python reproduce.py --check --out replay/RESULTS_BY_MODALITY.json
```

The result contains 84 modality-specific cells, 36 secondary-union cells, nine direct-only sensitivities and twelve illustrative membership scenarios. The GitHub Actions workflow runs the same check on Python 3.10 and 3.12.

## Files

| Path | Contents |
|---|---|
| `current_analysis/` | Current descriptive analysis and expected results |
| `current_input/` | Versioned input with technical reconciliation provenance |
| `input_snapshot/` | Required historical coded inputs and inherited aggregation rules |
| `CORPUS_UNITS_182.csv` | Readable operational-unit roster and population strata |
| `corpus/` | 479-family, 220-block and 182-unit crosswalks, protocol chronology and historical outputs |
| `reconciliation/` | One 426-position technical consolidation and directed evidence for 57 complete positions |
| `EVIDENCE_SOURCE_IDENTIFIERS.json` | Source IDs, original content hashes and available public retrieval pointers |
| `PUBLIC_PROJECTION_PROVENANCE.json` | Serialization, minimal redactions and semantic-equivalence record |
| `DATA_DICTIONARY.md` | Reference, classification and uncertainty definitions |
| `validation_protocol/` | Preserved pre-return design and sampling replay; dated historical status |
| `validation/` | Corrected locked paired labels, source-limited agreement, technical integration and pilot limits |
| `validation_sensitivity/` | Source-limited human positive-only sensitivity, exact 57-positive and 5,096-position bridges, comparisons, and standalone reproducer |
| `linked_review_protocol/` | Prepared targeted source-matched human verification protocol, neutral 109-position roster and empty-return schema; no completed assessments |
| `update_manifest.py` | Local manifest regeneration; does not commit, tag or publish |

Full third-party articles, licensed native bibliographic exports, raw identifiable reviewer returns, coordinator answer keys and conversation logs are not distributed. Source metadata and original source hashes are provenance pointers; they do not imply that the underlying full text is included or newly read. Some source identifiers denote internal receipts. Private routes are omitted from public corpus metadata. The original private working records remain preserved by the authors.

## Version and citation

The first public version was v1.0.0. The current supporting-data revision is **v1.3.0**, released on **5 November 2026**. Use the tagged release rather than the moving main branch for a versioned citation: [v1.3.0](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.3.0). `CITATION.cff` supplies author and version metadata. No DOI is claimed. A future archival deposit may add a DOI without changing the reported results.

Santos VMC, Keltke G (2026). Incretin therapy suicide-related outcome reporting audit: data and code. Version v1.3.0. GitHub. https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.3.0.

The repository contains supporting data and code; it does not contain a manuscript preprint. The journal submission package is prepared separately.

## Reuse

Author-owned analysis code is released under the **MIT License** (`LICENSE`). Author-owned documentary classifications, compilation and documentation are released under **CC BY 4.0** (`DATA_LICENSE.md`). These permissions do not relicense source publications, registry-origin text or any third-party material. Preserve source attribution and identify modifications.
