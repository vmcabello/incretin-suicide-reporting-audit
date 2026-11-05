# Incretin therapy suicide-related outcome reporting audit

Data and code accompanying **Public reconstructibility of suicide-related outcomes in a historical corpus of trials of GLP-1 receptor agonists and tirzepatide**.

Vitor Motta Cabello dos Santos (ORCID [0000-0002-0667-7288](https://orcid.org/0000-0002-0667-7288)) and Guilherme Keltke (ORCID [0009-0007-5415-0572](https://orcid.org/0009-0007-5415-0572)). Both authors are unaffiliated, Campinas, São Paulo, Brazil.

## Scope

This is an exploratory documentary audit of a fixed historical corpus. It asks whether public reporting supports arm-specific reconstruction for an explicit population and observation window. It does not estimate a clinical suicide risk or a treatment effect, and does not claim exhaustive trial ascertainment.

- 182 operational units; 159 in the post-hoc whole-population stratum; 170 with supported populations including subgroups.
- 5,096 documentary positions across outcomes, source layers and modalities.
- 57 complete positions, 1,009 unknown positions and 4,030 not-complete positions. Positions are not distinct trials.
- In the 159-unit B3 secondary union, confirmed reconstructions are 1 for ideation, 1 for attempt and 15 for death, with 26 unknown units per outcome. The death reconstructions are derived proofs. Main results keep modalities and direct/derived proofs separate.

Corpus-conditional identification intervals vary coded unknowns within the admitted corpus; they do not cover missed trials or selection/coding error. Full vital ascertainment is not established by a compatible zero-mortality report. Shared technical correction copies are not a new independent reliability experiment.

## Additions in v1.1.1

The preceding v1.1.0 support release is retained. This patch fixes cross-platform comparison of gzip containers: the ledger is compared byte for byte after decompression, while the release manifest verifies the published compressed bytes. Scientific ledger content is unchanged.

This version adds an individual search-update trail and a coverage-limited inventory of recorded documentary reason codes. The coded reconstruction inputs and the numerical results from v1.0.0 are unchanged. It also publishes a protocol for a new independent reassessment; that reassessment has **not been completed**. No new human agreement or classification-accuracy result is claimed.

- `search_trace/`: 2,558 saved database representations, 745 screening cases, recorded decisions and rationales, 1,717 reused prior-library groups, supported corpus links and itemised missing information. An identifier route is not scientific closure. Twelve prior-group rationales remain unrecovered; unestablished final links remain explicit.
- `reason_inventory/`: position-level code inventory and portable reproducer. All historical annotations prohibit corpus-frequency inference. Code counts are not prevalence estimates of trial-level causes or of instrument non-use.
- `validation_protocol/`: the new 663-position reassessment design (57 complete positions, the preserved 426-position not-complete sample and 180 sampled unknowns), plus a nested 30-unit alternative-reference pilot. Separate unfilled reviewer instruments remain in the local author package; no returned ratings are published here.

Run `python reproduce.py --check` to verify integrity, reproduce the original numerical results and validate the added supporting exports. This is research support material, not a journal major-revision decision or a manuscript preprint.

## Reproduce the results

Python **3.10 or newer** is sufficient. The analysis uses only the standard library and needs no network access or package installation.

```sh
git clone https://github.com/vmcabello/incretin-suicide-reporting-audit.git
cd incretin-suicide-reporting-audit
python reproduce.py --check
```

This verifies the public file manifest, runs the 34 inherited analysis regression checks, recomputes all results and requires a byte-for-byte match to `current_analysis/RESULTS_BY_MODALITY.json`. To retain an output file:

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

Full third-party articles, licensed native bibliographic exports, raw identifiable reviewer returns, coordinator answer keys and conversation logs are not distributed. Source metadata and original source hashes are provenance pointers; they do not imply that the underlying full text is included or newly read. Some source identifiers denote internal receipts. Private routes are omitted from public corpus metadata. The original private working records remain preserved by the authors.

## Version and citation

The first public version was v1.0.0. The current supporting-data version is **v1.1.1**, released on **4 November 2026**. Use the tagged release rather than the moving main branch for a versioned citation: [v1.1.1](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.1.1). `CITATION.cff` supplies author and version metadata. No DOI is claimed. A future archival deposit may add a DOI without changing the reported results.

Santos VMC, Keltke G (2026). Incretin therapy suicide-related outcome reporting audit: data and code. Version v1.1.1. GitHub. https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.1.1.

The repository contains supporting data and code; it does not contain a manuscript preprint. The journal submission package is prepared separately.

## Reuse

Author-owned analysis code is released under the **MIT License** (`LICENSE`). Author-owned documentary classifications, compilation and documentation are released under **CC BY 4.0** (`DATA_LICENSE.md`). These permissions do not relicense source publications, registry-origin text or any third-party material. Preserve source attribution and identify modifications.
