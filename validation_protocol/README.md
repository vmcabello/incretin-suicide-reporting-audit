# Protocol for the new separately retained documentary reassessment

Status: **REQUIRES_REVIEWER_VALIDATION**. No new paired human assessments, agreement values or adjudicated corrections are reported here.

The protocol was fixed before this new sampling and reassessment, after the original results were known. It retains exactly the preceding 426-position probability sample, includes all 57 complete positions and selects 180 of 1,009 cumulatively unknown positions. All 663 position keys and selection probabilities are supplied. The 829 unselected unknown positions are not reclassified by extrapolation.

Thirty positions already selected, in thirty distinct units, form an alternative-reference pilot. Its finite conditional frame requires an exact SHA256-matched original structured registry payload with the unit's own registry identifier. The published pilot frame contains only registry/source identifiers and eligible position keys. Local paths, source text and reviewer decisions are excluded. The frame's availability condition does not establish complete endpoint reporting or universal representativeness.

The separate private forms hide current coded answers and rationales. The assessors' prior participation and exposure remain relevant. The earlier author declaration of independent assessments is preserved, while the transmitted technical reconsolidation did not retain two separately traceable corrected decision sets for estimating reliability. The new exercise is not external or memory-blinded validation.

`SAMPLING_ROSTER.json` and `.csv` contain design information, not human judgments. The design groups identify the sampling frame and should not be mistaken for newly validated outcomes. `PILOT_LOCAL_SOURCE_FRAME.json` makes the nested allocation reproducible. `PROTOCOL.json` defines assessment, mechanism coding, alternative-reference extraction and post-return comparison/adjudication.

Run the standard-library-only sampling replay against the preserved public source release:

```
python -B reproduce_sampling_plan.py --repo /path/to/v1.0.0/repository
```

The replay verifies design selection only; it does not fill human forms or calculate agreement, accuracy or clinical risk. Findings from the enriched set must be described by sampling stratum and modality. Agreement does not establish accuracy, and an adjudicated consensus is not an external gold standard.

Reporting guidance: Kottner J, Audigé L, Brorson S, et al. Guidelines for Reporting Reliability and Agreement Studies (GRRAS) were proposed. J Clin Epidemiol. 2011;64:96–106. doi:10.1016/j.jclinepi.2010.03.002. The guidance does not validate this particular design or its judgments.
