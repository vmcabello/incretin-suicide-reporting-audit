"""Reproduce descriptive paired-label agreement without third-party packages.

This is internal, retrospective, source-limited agreement, not an accuracy
estimate, an external validation, or an independent full-source re-extraction.
No confidence intervals, population error rates, or clinical effects are fitted.
"""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import json

KEY = ("unit_id", "component", "stage", "modality", "reference_id", "window_id")
FIELDS = ("source_scoped_classification", "cumulative_classification", "cumulative_indicator")
COUNTER_FIELDS = {
    "cumulative_labels": "cumulative_classification",
    "source_scoped_labels": "source_scoped_classification",
    "primary_source_examined": "primary_source_examined",
    "source_access": "source_access",
    "declared_separate_before_discussion": "formed_before_discussion",
    "declared_prior_exposure": "prior_answer_exposure",
    "declared_substantive_AI": "substantive_AI_judgment_used",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def indicator(label):
    if label in ("complete_direct", "complete_derived"):
        return 1
    if label in ("partial_reference", "not_reconstructible_in_examined_corpus"):
        return 0
    if label in ("reference_unverifiable", "public_source_unavailable"):
        return None
    raise ValueError("Unknown cumulative label: " + str(label))


def agreement(rows, field, weighted=False):
    if not rows:
        raise ValueError("Agreement is not defined for an empty group")
    table, first, second = defaultdict(Fraction), defaultdict(Fraction), defaultdict(Fraction)
    for row in rows:
        weight = Fraction(row["N_h"], row["n_h"]) if weighted else Fraction(1)
        x, y = row["R1"][field], row["R2"][field]
        table[x, y] += weight
        first[x] += weight
        second[y] += weight
    total = sum(table.values())
    observed = sum(w for (x, y), w in table.items() if x == y) / total
    expected = sum(first[x] * second[x] for x in set(first) | set(second)) / total**2
    kappa = (observed - expected) / (1 - expected) if expected != 1 else None
    same = sum(row["R1"][field] == row["R2"][field] for row in rows)
    return {
        "positions": len(rows), "distinct_units": len({r["unit_id"] for r in rows}),
        "weighted": weighted, "sum_weights": float(total),
        "exact_agreement": float(observed), "agreeing_positions": same,
        "disagreeing_positions": len(rows) - same,
        "expected_agreement_from_margins": float(expected),
        "cohen_kappa": None if kappa is None else float(kappa),
        "kappa_undefined_reason": "Single-category degenerate margins" if kappa is None else None,
        "cross_tabulation": [
            {"R1": x, "R2": y, "count_or_weight": float(w) if weighted else int(w)}
            for (x, y), w in sorted(table.items(), key=lambda item: repr(item[0]))
        ],
    }


def validate_rows(rows):
    ids, keys = set(), set()
    strata = {}
    for row in rows:
        pid, key = row["position_id"], tuple(row[k] for k in KEY)
        if pid in ids or key in keys:
            raise ValueError("Duplicate position identifier or six-part position key")
        ids.add(pid)
        keys.add(key)
        n_h, N_h = row["n_h"], row["N_h"]
        if not isinstance(n_h, int) or not isinstance(N_h, int) or not 0 < n_h <= N_h:
            raise ValueError("Invalid sampling stratum size")
        if abs(row["weight"] - float(Fraction(N_h, n_h))) > 1e-12:
            raise ValueError("Declared weight does not equal N_h/n_h")
        if abs(row["selection_probability"] - float(Fraction(n_h, N_h))) > 1e-12:
            raise ValueError("Selection probability does not equal n_h/N_h")
        sid = (row["design_group"], row["stratum_id"])
        design = (N_h, n_h)
        if sid in strata and strata[sid] != design:
            raise ValueError("Stratum sizes differ within a stratum")
        strata[sid] = design
        for reviewer in ("R1", "R2"):
            if row[reviewer]["cumulative_indicator"] != indicator(row[reviewer]["cumulative_classification"]):
                raise ValueError("Cumulative indicator disagrees with label")
        if row["paired_cumulative_labels_agree"] != (row["R1"]["cumulative_classification"] == row["R2"]["cumulative_classification"]):
            raise ValueError("Incorrect paired agreement flag")
        if row["paired_source_scoped_labels_agree"] != (row["R1"]["source_scoped_classification"] == row["R2"]["source_scoped_classification"]):
            raise ValueError("Incorrect source-scoped agreement flag")
        if row["raw_cumulative_indicator_differs_from_historical"] != (row["R1"]["cumulative_indicator"] != row["historical_cumulative_indicator"]):
            raise ValueError("Incorrect historical difference flag")
    actual = Counter((r["design_group"], r["stratum_id"]) for r in rows)
    if any(actual[sid] != sizes[1] for sid, sizes in strata.items()):
        raise ValueError("Published selected stratum counts do not equal n_h")


def reproduce(root):
    minimal = read(root / "PAIRED_RATINGS_663.json")
    metadata = read(root / "AGREEMENT_REPORT_METADATA.json")
    rows = minimal["rows"]
    validate_rows(rows)
    report = {k: metadata[k] for k in ("schema", "date", "protocol_id")}
    report.update(rating_pairs=len(rows), distinct_units=len({r["unit_id"] for r in rows}),
                  design_groups={}, overall_descriptive_enriched_sample={}, by_modality={}, by_layer={},
                  interpretation=metadata["interpretation"])
    report["overall_descriptive_enriched_sample"] = {f: agreement(rows, f) for f in FIELDS}
    for group in sorted({r["design_group"] for r in rows}):
        selected = [r for r in rows if r["design_group"] == group]
        report["design_groups"][group] = {
            "unweighted": {f: agreement(selected, f) for f in FIELDS},
            "weighted_descriptive_only": {f: agreement(selected, f, True) for f in FIELDS},
            "historical_frame_size": sum({r["stratum_id"]: r["N_h"] for r in selected}.values()),
            "current_primary_source_examination_per_reviewer": {
                reviewer: dict(Counter(r[reviewer]["primary_source_examined"] for r in selected))
                for reviewer in ("R1", "R2")
            },
            "raw_indicator_changes_from_historical": sum(r["raw_cumulative_indicator_differs_from_historical"] for r in selected),
            "changes_are_not_certified_errors": True,
        }
    for field, outkey in (("modality", "by_modality"), ("stage", "by_layer")):
        for group in sorted({r[field] for r in rows}):
            selected = [r for r in rows if r[field] == group]
            report[outkey][group] = {f: agreement(selected, f) for f in FIELDS[:2]}
    report["coverage_per_reviewer"] = {}
    for reviewer in ("R1", "R2"):
        coverage = {
            "dossiers": len({r["unit_id"] for r in rows}), "positions": len(rows),
            "pilot_positions": sum(r["nested_alternative_reference_pilot"] for r in rows),
        }
        for output, field in COUNTER_FIELDS.items():
            coverage[output] = dict(Counter(r[reviewer][field] for r in rows))
        # These summary inputs were produced from private returned fields and are
        # explicitly reported metadata, NOT calculations recoverable from the
        # privacy-minimised paired labels. No private response prose is published.
        extras = metadata["reported_coverage_not_derivable_from_minimal_pair"][reviewer]
        if set(extras) & set(coverage):
            raise ValueError("Reported metadata would overwrite computed coverage")
        coverage.update(extras)
        report["coverage_per_reviewer"][reviewer] = coverage
    return report


def selftest():
    def row(x, y, N_h=1, n_h=1):
        return {"unit_id": "test", "R1": {"label": x}, "R2": {"label": y}, "N_h": N_h, "n_h": n_h}
    constant = agreement([row("same", "same")], "label")
    assert constant["cohen_kappa"] is None and constant["exact_agreement"] == 1.0
    assert constant["kappa_undefined_reason"] == "Single-category degenerate margins"
    opposite = agreement([row("a", "b"), row("b", "a")], "label")
    assert opposite["cohen_kappa"] == -1.0 and opposite["exact_agreement"] == 0.0
    mixture = agreement([row("a", "a"), row("b", "b")], "label")
    assert mixture["cohen_kappa"] == 1.0
    weights = agreement([row("a", "a", 3, 1), row("b", "a")], "label", True)
    assert weights["sum_weights"] == 4.0 and weights["exact_agreement"] == 0.75
    assert weights["cohen_kappa"] == 0.0
    unknown = agreement([row(None, None), row(1, 1)], "label")
    assert unknown["cohen_kappa"] == 1.0
    try:
        agreement([], "label")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty input must not yield an agreement estimate")
    return 6


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tests = selftest()
    actual = reproduce(args.root)
    if args.check and actual != read(args.root / "AGREEMENT_RESULTS.json"):
        raise SystemExit("Descriptive agreement differs from the distributed expected report")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"rating_pairs": actual["rating_pairs"], "distinct_units": actual["distinct_units"],
                      "agreement_report_matches": args.check, "selftests": tests,
                      "coverage_extras_are_reported_metadata": True, "full_source_revalidation": False}))


if __name__ == "__main__":
    main()
