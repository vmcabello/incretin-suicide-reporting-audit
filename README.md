# Incretin therapy suicide-related reporting audit data and code

Current support version **v1.6.1**, 6 November 2026. This repository provides the coded data and deterministic analysis for an exploratory documentary audit of a fixed historical corpus. It is not a manuscript preprint or an estimate of clinical suicide risk.

The current analysis is in [negative117](negative117/README_EN.txt). It integrates 117 returned unit dossiers, 194 component contexts and 456 new exact B3 modality judgments. Both authors approved the recalculated manuscript and submission, as reported by the corresponding author; journal submission has not been sent by this release.

## Reproduce

Python 3.10 or later, standard library only:

```console
python reproduce.py --check
```

This checks every manifest file, replays the preserved historical analyses and then reproduces the current NEG117 results. For the current module alone:

```console
python negative117/reproduce_neg117.py --repository . --out replay_neg117
```

## Current findings and interpretation

Modality-specific results are primary. The secondary union among 159 whole-population units contains 1 confirmed/59 unknown ideation results, 2/46 attempt results and 17/76 death results. These are documentary units, not people with events. No new complete reconstruction was added by NEG117; 72 selected component contexts became unknown. The death reconstruction interval is 10.69%–58.49%, conditional on this admitted corpus and retained classifications. The follow-up does not validate every historical negative or bound unidentified trials.

See [current tables](negative117/expected/CURRENT_RESULTS.json), the [status index](CURRENT_STATUS_INDEX.json), [source identifiers](negative117/EVIDENCE_IDENTIFIERS_596.json), [coded data dictionary](negative117/DATA_DICTIONARY_NEG117_EN.json), [procedure and approval](negative117/AUTHOR_PROCEDURE_AND_APPROVAL_EN.json) and [AI disclosure](negative117/AI_USAGE_CURRENT_ROUND_EN.json).

## Historical material

All original scientific files from v1.5.0 remain byte-identical. Directory names such as current_input and current_analysis and old pending-author labels refer to their dated historical versions. The old root reproduction code is retained as reproduce_v1_5_0.py and the prior root README is in negative117/README_V150_ROOT_HISTORICAL.md. The frozen corpus chronology remains unchanged; [the current continuation](negative117/CHRONOLOGY_CURRENT_EN.json) identifies later source checking and approval.

Author-owned coding and documentation use CC-BY-4.0; software uses MIT. Original third-party full texts, personal raw returns, licensed native libraries, local routes and runtime transcripts are excluded. Artifact hashes identify privately archived source versions; sanitized public file hashes are separate. No archival DOI has been assigned. Read DATA_LICENSE.md for third-party rights and CURRENT_STATUS_INDEX.json for current scope.

## v1.6.1 documentary maintenance

LIPER2 supplement locators and LIPER2/GRAVITAS bibliographic metadata have been reconciled against identified source versions. See [the correction ledger](minor161/DOCUMENTARY_CORRECTION_LEDGER.json) and [references](minor161/BIBLIOGRAPHIC_REFERENCES_EN.json). Numerical results and scientific classifications are unchanged. Raw reviewer returns remain historical; normalized locators do not represent new human votes.

The [Table S2 note](minor161/TABLE_S2_NOTE_EN.json) clarifies that A-B2 preserve earlier assessments, whereas B3 includes later targeted checking. Layer differences combine additional sources with differences in verification timing and intensity; they do not isolate source-category effects.
