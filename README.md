# Public reconstruction of suicide-related trial outcomes

Current data/code support: **v2.0.0**, 11 November 2026 — **28 randomized populations, 27 trial registry identifiers**. The current module is [core28](core28/README_PUBLIC_RELEASE.txt).

- [Download the current Online Resource 2 ZIP](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/download/v2.0.0/ESM_2.zip)
- [Versioned release](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v2.0.0)
- [Frozen roster](core28/dados/NUCLEO_CONGELADO_28.json), [coded judgments](core28/dados/JULGAMENTOS_CONGELADOS.json), [source catalogue](core28/evidencias/CATALOGO_FONTES_VERIFICADAS.json) and [complete results](core28/RESULTADOS_COMPLETOS.json)
- [Current-versus-historical status](CURRENT_STATUS_INDEX.json) and [public projection record](core28/PUBLIC_RELEASE.json)

## Reproduce

Python 3.10 or newer; standard library only:

```console
python core28/reproduce.py --check
```

The current check verifies the public file manifest, reproduces the frozen CORE28 results byte for byte, and runs 28 synthetic tests. To check current and historical versions together:

```console
python reproduce.py --check
```

## Scope and interpretation

Four population/window references and three ascertainment modalities are kept separate. Mortality derivation is applicable only to death, leaving 784 applicable positions. Unknowns remain in denominators; direct reports and derived proofs remain distinct. Modality-specific tables are primary; any-modality unions are secondary. The historical-treated secondary unions are ideation 3 complete/25 unknown, attempt 5/23 and death 20/8. Nineteen of those 20 death confirmations require derivation; one has direct support. All applicable identification intervals have a conditional upper endpoint of 100%.

These are documentary reconstruction results, not patients with events, clinical suicide risks or treatment effects. The core was enumerated retrospectively and is not an exhaustive trial census. No new source classifications or statistical analyses were added for this release.

## Historical releases

The earlier [v1.6.1 release](https://github.com/vmcabello/incretin-suicide-reporting-audit/releases/tag/v1.6.1) concerns a different 182/159-unit historical corpus. Its inputs, decisions, result files and tags remain unchanged. The dated root README, status, citation and release metadata are preserved in [history/v1.6.1](history/v1.6.1/). Existing directories such as `current_input`, `current_analysis` and `negative117` remain historical; they do not define the current 28-population dataset. `reproduce_v1_6_1.py` retains the previous root replay and is also run by the combined check.

## Availability and rights

This release distributes author-owned data and code, not a manuscript preprint. The editorial source file containing full manuscript prose is excluded from the public projection; all frozen scientific data, locators and numerical results are unchanged. The projection, original archive hash and retained source manifest are recorded in [core28/PUBLIC_RELEASE.json](core28/PUBLIC_RELEASE.json).

Author-owned software uses MIT; original documentary classifications and documentation use CC BY 4.0. Third-party rights remain with their owners. Original publisher full texts, raw personal reviewer returns and licensed native bibliographic exports are excluded. No archival DOI has been assigned. This release does not perform a journal submission.
