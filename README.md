# Incretin therapy suicide-related outcome reporting audit

Data and code accompanying **Public reconstructibility of suicide-related outcomes in a historical corpus of trials of GLP-1 receptor agonists and tirzepatide**.

Vitor Motta Cabello dos Santos (ORCID [0000-0002-0667-7288](https://orcid.org/0000-0002-0667-7288)) and Guilherme Keltke (ORCID [0009-0007-5415-0572](https://orcid.org/0009-0007-5415-0572)). Both authors are unaffiliated, Campinas, São Paulo, Brazil.

## Current supporting revision: v1.4.0

This is an exploratory documentary audit of a fixed historical corpus: 182 operational units, including 159 in a post-hoc whole-population stratum and 170 with supported populations including subgroups. Its 5,096 positions distinguish outcome, modality, cumulative source layer, reference population and observation window. A position is not a separate trial.

**Current integrated results are in `source_review109/`.** The directories named `current_input/` and `current_analysis/` retain the historical v1.3.0 snapshots and expected results; they are not overwritten or relabelled as the new analysis. Both versions and the earlier positive-only sensitivity remain exactly reproducible.

The new material integrates the source-linked follow-up of 109 positions in 59 dossiers. The authors declare separate human assessments before discussion, no substantive AI judgment in their final decisions and prior project exposure. This internal retrospective exercise is not external or memory-blinded validation. The 109 positions are a subset of the preceding 663-position reassessment: **there are not 772 distinct independently assessed positions**.

In the preceding source-limited exercise, 20 of 57 historical positive positions were confirmed and 37 were indeterminate. The follow-up confirms those 37 exact positions, giving 57 historical positives confirmed across the two exercises. The two-stage sample of 72 historical not-complete positions contains four new complete-derived judgments, 42 not-reconstructible judgments, 25 partial references and one unverifiable reference. None is a new complete-direct judgment. Exact paired cumulative-label agreement is 109/109; agreement does not establish accuracy.

Thirteen positions have incomplete pertinent source coverage. Their raw partial/unverifiable judgments are preserved, and their integrated indicators remain unknown. The principal integration preserves pertinent unresolved gaps cumulatively within the same outcome, modality, reference and window. A targeted integration without forward scope-gap propagation is retained as a sensitivity. Both models use the same admissibility guards for positive-proof reuse. Positive witness reuse is allowed only in source layers admitting all required sources; no registry or regulatory evidence is imported into an article-only proof. Derived updates on keys not directly rated are labelled technical deductions, not additional human votes. The sample is not extrapolated to unreviewed positions, and four of 72 is not reported as a corpus error rate.

### Current B3 secondary union, whole-population stratum (N=159)

The principal presentation is modality-specific. This secondary union combines non-equivalent modalities and is shown here as an orientation to the current version.

| Outcome | Confirmed reconstructions | Unknown units | Corpus-conditional identification interval |
|---|---:|---:|---:|
| Ideation | 1 (1 direct; 0 derived) | 32 | 0.63%-20.75% |
| Attempt | 2 (1 direct; 1 derived) | 27 | 1.26%-18.24% |
| Death | 17 (0 direct; 17 derived) | 28 | 10.69%-28.30% |

These intervals vary coded unknowns within the admitted corpus. They do not cover missed studies or selection/coding error and are not confidence intervals, clinical risks or treatment effects. All death reconstructions remain derived; no direct suicide-death reconstruction is established. Structured assessments remain separate from adverse-event reports. A compatible zero-mortality report does not prove complete vital follow-up or clinical absence of suicide-related events.

Technical checks retain the STEP 1 source inconsistency: its table gives one placebo participant and three fatal events, while the footnote attributes three non-suicide causes to “one participant each.” This audit does not repair the total-person count; the limited cause-enumeration derivation and discrepancy are both disclosed. AWARD-10 uses the supplied corrected 23 May 2018 version. Source versions and access at the historical 19 October 2026 search date are **not uniformly certified**. Reading records cover specified pages and sections, not full extraction of every original source. The 13 incompletely examined scopes are not silently closed.

No renewed author approval of the revised manuscript, journal submission or payment is inferred from these returns. The manuscript package is maintained separately; no manuscript preprint, third-party full text or identifiable raw reviewer return is distributed here.

## Reproduce current and historical results

Python **3.10 or newer**, standard library only; no network or package installation is required.

```sh
git clone https://github.com/vmcabello/incretin-suicide-reporting-audit.git
cd incretin-suicide-reporting-audit
python reproduce.py --check
```

The command checks the root and supporting manifests; runs the inherited analysis tests; reproduces historical modality results, coverage-limited annotation counts and paired agreement; replays the marked search subsets and 109-position sampling design; reproduces the historical positive-only sensitivity; and reproduces the new source-linked integration and its sensitivity without forward scope-gap propagation. The GitHub Actions workflow performs the same check with Python 3.10 and 3.12. `--out` continues to export the preserved historical primary result, as documented in the earlier interface.

The new integration includes reversible changes, minimal paired ratings, exact study/modality/layer links, preserved unknowns, source-acceptance provenance and a standalone reproducer. Technical audit projections include source identifiers, hashes and locators without redistributing licensed sources or private file paths.

The two approximately 25 MB generated integrated-input files are not duplicated in the public repository. `OMITTED_REGENERABLE_OUTPUTS.json` records their expected hashes; the replay regenerates both from the preserved historical data and the minimal follow-up inputs and checks their exact SHA256 values. All other generated result files must match the distributed bytes.

## Preserved history and provenance

- **v1.3.0:** `validation_sensitivity/` retains the positive-only scenario in which the 37 then-unconfirmed historical positives were set to unknown and all other 5,059 codes stayed fixed. In its N=159 B3 death union, k/u moved from 15/26 to 5/36. This is now a dated historical sensitivity, not the outcome of the completed follow-up.
- **v1.2.0:** `validation/` retains the preceding 663-position paired returns, descriptive agreement and source-scope limits. Primary-source examination was recorded for 333/663 positions per assessor. Its 20/57 confirmation and 37 unknowns remain valid descriptions of that exercise, not current verification status.
- `linked_review_protocol/` and `validation_protocol/` preserve their dated, pre-return design snapshots. Statements that readings were pending describe those historical documents. Current execution extent is documented separately; their fixed protocols, seeds and rosters are not retroactively edited.
- `search_trace/` links 2,558 saved database representations to 745 screening cases and 1,717 reused prior-library groups. Nominal subset flags reproduce Table S1 and distinguish 14 PubMed export differences already known to the master library. Identifier matching does not create an eligibility or classification vote. Twelve historical group rationales remain unrecovered; unestablished links remain explicit.
- `reason_inventory/` reproduces 5,096 structural annotation positions. These code inventories do not estimate corpus-wide mechanism prevalence or instrument non-use.
- `corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_EN.json` appends the 109-return receipt and integration, preserving all first 15 v1.3.0 events and the earlier eight-event prefix.

## File map

| Path | Role |
|---|---|
| `source_review109/` | Current integrated results, scope-gap propagation sensitivity, minimal paired follow-up ratings, code, changes and technical source checks |
| `current_analysis/`, `current_input/` | Preserved historical primary analysis and technically reconciled input |
| `input_snapshot/` | Historical coded data and inherited aggregation rules |
| `validation_sensitivity/` | Preserved v1.3.0 source-limited positive-only scenario and exact bridges |
| `validation/`, `validation_protocol/` | Earlier paired exercise, source-scope limits, pilot and fixed design |
| `linked_review_protocol/` | Original source-linked follow-up protocol and neutral selection roster |
| `corpus/`, `CORPUS_UNITS_182.csv` | Families, blocks, operational units, population strata and amendment chronology |
| `search_trace/` | Record-level search-update routes, nominal subset flags and validators |
| `reason_inventory/` | Coverage-limited code inventory and reproducer |
| `EVIDENCE_SOURCE_IDENTIFIERS.json` | Source identifiers, original content hashes and available public retrieval pointers |
| `DATA_DICTIONARY.md` | Essential scientific and integrated-data definitions |
| `MANIFEST.json`, `update_manifest.py` | Integrity inventory and local regeneration; no commit or publication action |

Native licensed bibliographic exports, full third-party articles, raw identifiable reviewer returns, coordinator answer keys and conversation logs remain outside this public projection. Some source IDs denote internal receipts. Original hashes identify source bytes, not a new reading certificate or proof that a source was public at the historical cutoff. Author-owned code and classifications have separate licenses below.

## Version and citation

The current supporting-data release is **v1.4.0**, released on **5 November 2026**. Use the immutable tagged release and its `CITATION.cff` rather than the moving branch. Earlier tagged versions remain available. No DOI is claimed.

Citation: Santos VMC, Keltke G (2026). Incretin therapy suicide-related outcome reporting audit: data and code. Version v1.4.0. GitHub. https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.4.0.

## Reuse

Author-owned software is **MIT licensed** (`LICENSE`); author-owned classifications, compilation and documentation are **CC BY 4.0** (`DATA_LICENSE.md`). These licenses do not relicense source publications or other third-party material. Preserve attribution and identify modifications.
