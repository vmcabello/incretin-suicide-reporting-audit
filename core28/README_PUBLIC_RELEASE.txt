CURRENT 28-POPULATION DATA AND CODE — v2.0.0

This is Online Resource 2 data/code support for the current 28-population documentary audit, involving 27 registry identifiers. It is different from the historical 182/159-unit corpus retained under release v1.6.1.

Run from this extracted folder with Python 3.10 or newer (standard library only):
  python reproduce.py --check

This verifies the public file manifest, reproduces RESULTADOS_COMPLETOS.json byte for byte from the frozen judgments and core, and runs 28 synthetic tests. The original analysis commands remain available:
  python codigo/run_analysis.py --output reproduced.json
  python -m unittest discover -s codigo -p test_analysis.py -v

Primary results keep four population/window references and ascertainment modalities separate. Unknowns stay in denominators. Direct reports and derived proofs are distinguished. Conditional identification intervals do not estimate clinical suicide risk, and this retrospectively enumerated core is not an exhaustive trial census.

All frozen scientific inputs, evidence locators, analysis code and expected numerical results are unchanged from the author-approved submission support. The editorial JSON containing full manuscript prose is omitted from this public data/code projection; no full manuscript or preprint is being deposited. The source archive hash and original submission manifest remain recorded in PUBLIC_RELEASE.json and provenance/. ESM2_MANIFEST.json describes the actual files included in this public ZIP.

Original publisher documents, identifiable participant data, private raw reviewer exports and licensed bibliographic libraries are not redistributed. Third-party rights are retained; licences apply only to author-owned material.

Earlier creation-stage status fields remain historical. This release adds no new judgments, human review or statistical analysis and does not perform a journal submission.

Versioned download: https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/download/v2.0.0/ESM_2.zip
