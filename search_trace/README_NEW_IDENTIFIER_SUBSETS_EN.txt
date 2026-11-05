NOMINAL NEW-IDENTIFIER SUBSETS FOR TABLE S1

SEARCH_UPDATE_REPRESENTATIONS_2558_EN.json adds the field
new_identifier_subset_membership to every existing public row. All earlier
screening routes, classifications and original row fields are preserved.

TABLE_S1_REPRODUCED_FROM_MARKED_SUBSETS_EN.json is calculated from those flags:
PubMed 357 = 352 update-card representations + 5 prior-master representations;
Embase 429 = 347 + 82; PsycINFO 15 = 10 + 5; CENTRAL 97 = 43 + 54.
These are overlapping representations, not independent eligible studies.

Definitions are source-specific. PubMed uses the saved nominal list of 357
new-to-master candidates. There are 371 PubMed IDs absent from the historical
PubMed export; the other 14 already have same-publication PMID links in the
cross-database master and are itemised separately. Embase and PsycINFO use
same-database native-ID differences. CENTRAL uses the complete-query difference;
its 95 filtered additions form a nested subset of 97 complete-query additions.

No subset flag was inferred from file rank or assigned to force aggregate totals.
The local build checked physical identifier/ordinal/file-hash bindings for all
2,558 representations, read all four historical exports, and preserved explicit
native file hashes and locators. Licensed abstracts are not redistributed.

Run the public, standard-library projection check:
  python validate_marked_subsets.py --root .

This reproduces Table S1 and checks joins, preserved original fields, TSV parity,
the 14 PubMed exceptions and the dated chronology. It does not independently
re-read licensed native exports or validate clinical eligibility or accuracy.
