SOURCE-LIMITED HUMAN POSITIVE-ONLY SENSITIVITY, 2026-11-05

This is an illustrative sensitivity of the historical documentary analysis,
not an adjudication, error correction, or replacement primary analysis.
The original historical result and all raw human labels remain unchanged.

Rule: all 57 historical complete positions were in the reassessment census.
Twenty positions remain complete in both returns. In this scenario alone,
the other 37 take their exact concordant current unknown label. The remaining
5,039 historical position codes stay fixed. References, windows, source records,
proof flags, units, populations, and modality/layer keys do not move.
In particular, the 425 sampled historical negatives now unknown are not recoded.
Therefore this scenario is not a wholesale analysis of the 663 current returns.

Main B3 union (whole-population N=159):
Ideation: historical k=1,u=26; scenario k=1,u=26; interval 0.63%-16.98%.
Attempt: historical k=1,u=26; scenario k=1,u=26; interval 0.63%-16.98%.
Death: historical k=15,u=26; scenario k=5,u=36; interval 3.14%-25.79%
(historical 9.43%-25.79%). All five current complete death units are derived.

Source-limited human indeterminacy does not demonstrate historical error.
The historical technical witness checks are not new human verification.
Intervals are conditional on the admitted corpus and this scenario, not
sampling confidence intervals, clinical risks, or exhaustive-trial-universe
bounds. Nothing is extrapolated to unreviewed positions or unlocated trials.

FILES
SOURCE_LIMITED_HUMAN_POSITIVE_SENSITIVITY.json: full descriptive scenario,
84 modality cells, 36 secondary union cells, 9 direct-only summaries,
12 illustrative added-block scenarios, and all corresponding historical tables.
TABLE_HUMAN_LINKED_SENSITIVITY_B3_WHOLE.json: compact three-component main table.
POSITIVE_WITNESS_BRIDGE_57.json/csv: every historical positive's exact key,
paired human labels, scenario status, and original source/hash/locator witness.
POSITION_BRIDGE_5096.json/csv: complete position ledger, keeping historical
source-scoped observations, paired human cumulative judgments, and scenario-
imposed analytic statuses distinct, and identifying the 37 sensitivity-only deltas.
*_COMPARISON.csv: table exports for all modalities, layers, and three rosters.
REPRODUCTION_MANIFEST.json: input and generated-file SHA-256 hashes.

REPRODUCE (Python standard library only)
python reassessed_positive_sensitivity.py --repository PATH_TO_PUBLIC_REPOSITORY --out OUTPUT_DIRECTORY
python reassessed_positive_sensitivity.py --repository PATH_TO_PUBLIC_REPOSITORY --selftest

The script first reproduces all historical distributed modality tables using
the inherited code, verifies an independent descriptive table implementation,
then runs the scenario and 14 targeted synthetic checks. No original input,
historical result, public repository file, or human decision is modified.
The --repository directory must contain the v1.2.0-or-later input_snapshot,
current_input, current_analysis, and validation files recorded by hash.
