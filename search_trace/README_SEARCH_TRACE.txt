INDIVIDUAL SEARCH-UPDATE TRAIL

This directory supplies row-level links for 2,558 update representations and the 745 update-screening cards. It also distinguishes 55 separately exported registry representations and one query-absence notice.

Start with SEARCH_TRACE_README_EN.html or SEARCH_TRACE_SUMMARY_EN.json. The JSON files retain nested provenance; the TSV files expose the same records in spreadsheet-readable form.

The individual decisions and their author-written explanations are preserved as recorded. The original explanations are in Portuguese; English code and route descriptions are labels, not new study-specific decisions. Full database abstracts, verbatim source-evidence quotation fields, primary fulltexts, absolute local paths and contacts are excluded.

Validate with Python 3.10 or newer, without external packages:
  python validate_search_trace.py --root .

The validator checks data structure, counts, joins, TSV row identity, file hashes and sanitization. It does not assess clinical eligibility, error rates or independence.

Identifier matching is not scientific closure. A family-to-unit lookup does not establish that a particular report covers each unit or outcome. Source exclusions, context-only documents and planning records do not automatically require an admitted unit. Unknown trial identity or population membership stays explicit.

The published version1.0.0 and the frozen statistical input were not modified to produce these files.
