"""Reproduce technical AI conciliation of corrected, discordant human returns.

Standard library only. Raw labels are never changed and technical decisions are
never represented as human consensus or extra human assessments. The previous
historical and v1.4.0 analyses remain immutable comparison versions.
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re

KEY = ("unit_id", "component", "stage", "modality", "reference_id", "window_id")
STAGES = ("A", "B1", "B2", "B3")
COMPLETE = {"complete_direct", "complete_derived"}
UNKNOWN = {"reference_unverifiable", "public_source_unavailable", "pending_decision"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def key(row):
    return tuple(row[f] for f in KEY)


def target(row):
    return tuple(row[f] for f in KEY if f != "stage")


def kappa(left, right, weights=None):
    assert len(left) == len(right) and left
    weights = weights if weights is not None else [1.0] * len(left)
    total = sum(weights)
    lc, rc, table = collections.Counter(), collections.Counter(), collections.Counter()
    for a, b, w in zip(left, right, weights):
        lc[a] += w; rc[b] += w; table[a, b] += w
    observed = sum(w for a, b, w in zip(left, right, weights) if a == b) / total
    expected = sum(lc[c] * rc[c] for c in set(lc) | set(rc)) / (total * total)
    value = (observed - expected) / (1 - expected) if expected < 1 - 1e-14 else None
    return {"positions": len(left), "weight_total": total, "exact_agreement_positions": sum(a == b for a, b in zip(left, right)),
        "observed_agreement": observed, "expected_marginal_agreement": expected, "cohen_kappa": value,
        "kappa_undefined_if_degenerate_margins": value is None,
        "R1_marginal": dict(sorted(lc.items())), "R2_marginal": dict(sorted(rc.items())),
        "cross_tabulation": [{"R1": a, "R2": b, "weight_or_count": w} for (a, b), w in sorted(table.items())],
        "confidence_interval": None, "accuracy_or_external_error_rate_estimated": False}


def coverage(answer):
    unresolved = sorted({b["source_id"] for b in answer["source_bindings"] if b["relevance_and_examination"] in {"unexamined_relevant", "unavailable_relevant"}})
    incomplete = answer["targeted_scope_coverage"] == "incomplete_relevant_scope" or answer["cumulative_classification"] in UNKNOWN
    dimension_unknown = any(v == "unknown_unexamined_or_unavailable" for v in answer["six_dimensions"].values())
    return {"incomplete": incomplete or bool(unresolved) or dimension_unknown,
        "named_unresolved_source_ids": unresolved, "declared_scope": answer["targeted_scope_coverage"],
        "explicit_unknown_dimension": dimension_unknown}


def exact_projection(answer):
    if answer["cumulative_classification"] in COMPLETE:
        return "complete"
    return "unknown" if coverage(answer)["incomplete"] else "not_complete"


def agreement(paired, source_ledger):
    result = {"scope": "Descriptive internal paired ratings before technical AI conciliation. No naïve independent-position CI, external accuracy claim or extrapolated corpus error rate.",
        "followup_109_is_subset_of_previous663_not772": True, "by_group": [], "source_examination": {}}
    groups = [("all109", paired)] + [(g, [p for p in paired if p["design_group"] == g]) for g in sorted({p["design_group"] for p in paired})]
    for group, rows in groups:
        entry = {"group": group}
        for field in ("cumulative_classification", "source_scoped_classification"):
            entry[field] = kappa([p["R1"][field] for p in rows], [p["R2"][field] for p in rows])
        entry["three_state_exact_key_projection"] = kappa([exact_projection(p["R1"]) for p in rows], [exact_projection(p["R2"]) for p in rows])
        if group == "phase2_original_negative_probability_sample":
            weights = [p["sampling_design"]["weight"] for p in rows]
            entry["design_weighted_cumulative_label_agreement"] = kappa([p["R1"]["cumulative_classification"] for p in rows], [p["R2"]["cumulative_classification"] for p in rows], weights)
            entry["weighted_scope"] = "Standardized to the retained 4,030-position historical-negative frame only; not a population error estimate or all-corpus reliability. Incomplete source scopes remain part of reported ratings."
        entry["coverage_by_reviewer"] = {r: dict(collections.Counter(p[r]["targeted_scope_coverage"] for p in rows)) for r in ("R1", "R2")}
        result["by_group"].append(entry)
    for reviewer in ("R1", "R2"):
        entries = [s for c in source_ledger[reviewer]["cases"] for s in c["source_examinations"]]
        result["source_examination"][reviewer] = {"ledger_entries": len(entries),
            "states": dict(collections.Counter(s["examination_status"] for s in entries)),
            "unique_source_ids_declared_examined": len({s["source_id"] for s in entries if s["examination_status"] == "examined"}),
            "ledger_is_reported_scope_not_reading_certificate": True}
    return result


def source_inventory(baseline, paired):
    """Exact source hashes admitted in each target/layer, not proof of reading."""
    raw = collections.defaultdict(dict)
    for row in baseline["assessments"]:
        group = target(row), row["stage"]
        for ref in row.get("assessment_evidence_refs", []):
            match = re.match(r"^(SRC-[^#]+)#sha256=([0-9a-f]{64})[;#]", ref)
            if match:
                sid, value = match.groups()
                assert sid not in raw[group] or raw[group][sid] == value
                raw[group][sid] = value
    for pair in paired:
        group = target(pair), pair["stage"]
        for reviewer in ("R1", "R2"):
            for binding in pair[reviewer]["source_bindings"]:
                sid, value = binding["source_id"], binding["source_content_sha256"]
                assert sid not in raw[group] or raw[group][sid] == value
                raw[group][sid] = value
    result = {}
    for tgt, _ in raw:
        cumulative = {}
        for stage in STAGES:
            for sid, value in raw.get((tgt, stage), {}).items():
                assert sid not in cumulative or cumulative[sid] == value
                cumulative[sid] = value
            result[tgt, stage] = copy.deepcopy(cumulative)
    return result


def apply_reconciliation(baseline, paired, rules, historical_proofs, legacy, propagate_scope_gaps=True):
    revised = copy.deepcopy(baseline)
    by_key = {key(r): r for r in revised["assessments"]}
    original = {key(r): r for r in baseline["assessments"]}
    inventory = source_inventory(baseline, paired)
    rule_by_id = {r["position_id"]: r for r in rules["positive_witness_rules"]}
    old_proofs = {key(r): r for r in historical_proofs["rows"]}
    decisions, pending, accepted_proofs, gaps = [], [], [], []
    for pair in paired:
        row = by_key[key(pair)]
        a, b = pair["R1"], pair["R2"]
        ca, cb = coverage(a), coverage(b)
        union_ids = sorted(set(ca["named_unresolved_source_ids"]) | set(cb["named_unresolved_source_ids"]))
        rule = rule_by_id.get(pair["position_id"])
        proof = None
        if rule:
            proof = copy.deepcopy(rule)
        elif key(pair) in old_proofs:
            prior = old_proofs[key(pair)]["technical_reconciliation"]
            wanted = prior["sufficient_witness_source_ids_within_this_row_layer"]
            proof = {"position_id": pair["position_id"], "classification": prior["classification"],
                "minimum_stage": pair["stage"], "required_sources": [
                    {"source_id": s["source_id"], "sha256": s["sha256"], "locator": s["locator"]}
                    for s in prior["source_original_scopes"] if s["source_id"] in wanted],
                "technical_reason": "Exact historical positive witness remains supported by the preceding technical source audit; current assessor labels and source scopes are preserved separately.",
                "basis": "preserved_exact_historical_primary_witness", "technical_review_is_not_a_new_human_vote": True}
        has_positive_vote = a["cumulative_classification"] in COMPLETE or b["cumulative_classification"] in COMPLETE
        accepted = proof is not None
        if accepted:
            assert proof["classification"] in COMPLETE
            assert STAGES.index(row["stage"]) >= STAGES.index(proof["minimum_stage"])
            admitted = inventory[target(row), row["stage"]]
            assert proof["required_sources"] and all(admitted.get(s["source_id"]) == s["sha256"] for s in proof["required_sources"]), pair["position_id"]
            selected = "R1" if a["cumulative_classification"] in COMPLETE else "R2"
            facts = pair[selected]
            assert facts["reported_or_derived_counts_by_arm"] is not None and facts["denominators_by_arm"] is not None
            proof.update({**{f: pair[f] for f in KEY}, "counts_from_received_reviewer": selected,
                "reported_counts_by_arm": copy.deepcopy(facts["reported_or_derived_counts_by_arm"]),
                "denominators_by_arm": copy.deepcopy(facts["denominators_by_arm"]),
                "R1_cumulative_classification": a["cumulative_classification"], "R2_cumulative_classification": b["cumulative_classification"],
                "both_reviewers_source_examination_not_assumed": True})
            row.update({"status": proof["classification"], "complete_fixed_reference_verified": True,
                "both_eligible_arms_reconstructed": True, "derivation_validated": proof["classification"] == "complete_derived",
                "analysis_scope_closed_for_this_position": True, "AI_technical_exact_positive_witness": copy.deepcopy(proof)})
            # Existing formal gaps and unexamined-source records are not deleted;
            # an exact valid positive witness has existential analytical priority.
            if ca["incomplete"] or cb["incomplete"]:
                row["analysis_scope_closed_for_this_position"] = False
                row["unexamined_relevant_source_ids"] = sorted(set(row.get("unexamined_relevant_source_ids", [])) | set(union_ids))
                gap = {**{f: pair[f] for f in KEY}, "origin_position_id": pair["position_id"],
                    "reported_unresolved_source_ids_union": union_ids, "R1_incomplete": ca["incomplete"], "R2_incomplete": cb["incomplete"],
                    "kind": "AI_technical_pertinent_scope_gap_retained_beside_sufficient_positive_witness_not_a_new_human_vote"}
                row["AI_technical_unresolved_source_union"] = copy.deepcopy(gap)
                gaps.append(gap)
            accepted_proofs.append(proof)
            disposition = "technically_supported_exact_positive_witness"
            reason = proof["technical_reason"]
        else:
            incomplete = ca["incomplete"] or cb["incomplete"] or has_positive_vote
            negative_labels = [x["source_scoped_classification"] for x in (a, b) if x["source_scoped_classification"] not in COMPLETE | UNKNOWN]
            row["status"] = "partial_reference" if "partial_reference" in negative_labels or incomplete else "not_reconstructible_in_examined_corpus"
            row.update({"complete_fixed_reference_verified": False, "both_eligible_arms_reconstructed": False, "derivation_validated": False})
            if incomplete:
                row["analysis_scope_closed_for_this_position"] = False
                row["unexamined_relevant_source_ids"] = sorted(set(row.get("unexamined_relevant_source_ids", [])) | set(union_ids))
                gap = {**{f: pair[f] for f in KEY}, "origin_position_id": pair["position_id"],
                    "reported_unresolved_source_ids_union": union_ids, "R1_incomplete": ca["incomplete"], "R2_incomplete": cb["incomplete"],
                    "kind": "AI_technical_union_of_reported_pertinent_scope_gaps_not_a_new_human_vote"}
                row["AI_technical_unresolved_source_union"] = copy.deepcopy(gap)
                gaps.append(gap)
                disposition = "preserve_unknown_due_to_union_of_unresolved_pertinent_scopes"
                reason = "At least one assessor reports unresolved pertinent source coverage or a target dimension; another assessor's examined-source claim does not silently erase that scope gap. No accepted exact positive witness resolves it."
                if has_positive_vote:
                    pending.append(pair["position_id"])
            else:
                row["analysis_scope_closed_for_this_position"] = True
                disposition = "analytically_equivalent_closed_negative_scope"
                reason = "Both assessors have an examined closed scope without a compatible complete reconstruction. Partial-reference versus not-reconstructible labels remain separate raw judgments; the effective non-complete state is equivalent. Existing formal gaps are not deleted."
        row["AI_technical_reconciliation_current"] = {"position_id": pair["position_id"], "disposition": disposition,
            "R1_source_scoped": a["source_scoped_classification"], "R2_source_scoped": b["source_scoped_classification"],
            "R1_cumulative": a["cumulative_classification"], "R2_cumulative": b["cumulative_classification"],
            "reported_unknown_scope_union": union_ids, "new_human_consensus_inferred": False}
        decisions.append({**{f: pair[f] for f in KEY}, "position_id": pair["position_id"], "decision": disposition,
            "technical_reason": reason, "R1": {f: a[f] for f in ("source_scoped_classification", "cumulative_classification", "targeted_scope_coverage")},
            "R2": {f: b[f] for f in ("source_scoped_classification", "cumulative_classification", "targeted_scope_coverage")},
            "scope_union": {"R1": ca, "R2": cb}, "after_effective_indicator": legacy.indicator([row]),
            "after_analytical_status": row["status"], "technical_AI_judgment_not_a_human_vote": True})

    reuse = []
    for proof in accepted_proofs:
        for row in revised["assessments"]:
            if target(row) != target(proof) or key(row) == key(proof) or legacy.valid_complete(row):
                continue
            if STAGES.index(row["stage"]) < STAGES.index(proof["minimum_stage"]):
                continue
            admitted = inventory.get((target(row), row["stage"]), {})
            if not all(admitted.get(s["source_id"]) == s["sha256"] for s in proof["required_sources"]):
                continue
            before = legacy.indicator([row])
            row.update({"status": proof["classification"], "complete_fixed_reference_verified": True,
                "both_eligible_arms_reconstructed": True, "derivation_validated": proof["classification"] == "complete_derived",
                "analysis_scope_closed_for_this_position": True, "AI_technical_admissible_positive_reuse": copy.deepcopy(proof)})
            reuse.append({**{f: row[f] for f in KEY}, "origin_position_id": proof["position_id"], "origin_stage": proof["stage"],
                "minimum_admissible_stage": proof["minimum_stage"], "required_source_hashes": {s["source_id"]: s["sha256"] for s in proof["required_sources"]},
                "before_indicator": before, "after_indicator": legacy.indicator([row]), "technical_deduction_not_a_new_human_vote": True})
    propagated = []
    if propagate_scope_gaps:
        for gap in gaps:
            for row in revised["assessments"]:
                if target(row) != target(gap) or STAGES.index(row["stage"]) <= STAGES.index(gap["stage"]):
                    continue
                before = legacy.indicator([row])
                marker = {"origin_position_id": gap["origin_position_id"], "origin_stage": gap["stage"],
                    "reported_unresolved_source_ids_union": gap["reported_unresolved_source_ids_union"],
                    "technical_deduction_not_a_new_human_vote": True}
                row.setdefault("AI_technical_cumulative_scope_gap_union", []).append(marker)
                # Keep the gap flag even beside an existential positive proof:
                # removing derivations must not erase its unknown source scope.
                row["analysis_scope_closed_for_this_position"] = False
                row["unexamined_relevant_source_ids"] = sorted(set(row.get("unexamined_relevant_source_ids", [])) | set(gap["reported_unresolved_source_ids_union"]))
                propagated.append({**{f: row[f] for f in KEY}, **marker, "before_indicator": before,
                    "after_indicator": legacy.indicator([row]), "valid_positive_witness_has_priority": legacy.valid_complete(row)})
    # Immutable pre-existing formal gaps must survive every analytical projection.
    for row in revised["assessments"]:
        assert original[key(row)].get("cumulative_unresolved_gap_ids", []) == row.get("cumulative_unresolved_gap_ids", [])
    return revised, {"decisions": decisions, "positive_reuse": reuse, "scope_gap_forward": propagated, "pending_positive_proofs": sorted(pending)}


def direct_only_unit_states(data, pop, legacy):
    """Expose per-unit states omitted from the immutable legacy summary table."""
    ids = sorted(r["unit_id"] for r in data["units"])
    strata = {r["unit_id"]: r["designed_eligibility_stratum"] for r in pop["records"]}
    rosters = {
        "whole_population_posthoc_exploratory": [u for u in ids if strata[u] == legacy.PRIMARY_STRATUM],
        "supported_including_subgroups_complementary": [u for u in ids if strata[u] in {legacy.PRIMARY_STRATUM, legacy.SUBPOPULATION_STRATUM}],
        "operational_historical_complementary": ids,
    }
    grouped = collections.defaultdict(list)
    for row in data["assessments"]:
        grouped[row["unit_id"], row["component"], row["stage"], row["modality"]].append(row)
    result = {}
    for label, roster in rosters.items():
        for plan in data["expected_modality_plan"]["catalog"]:
            if plan["stage"] != "B3":
                continue
            states = {}
            for uid in roster:
                rows = [r for modality in plan["modalities"] for r in grouped[uid, plan["component"], "B3", modality]]
                value = legacy.indicator(rows, allow_derivations=False)
                states[uid] = "complete_direct" if value == 1 else "unknown" if value is None else "not_complete"
            result[label, plan["component"], "B3"] = states
    return result


def unit_deltas(before, after, direct_before, direct_after):
    results = {}
    for family in ("modality_results", "secondary_union_results", "without_derived_completeness"):
        fields = ("analysis_set", "component", "stage", "modality") if family == "modality_results" else ("analysis_set", "component", "stage")
        left = {tuple(r.get(f) for f in fields): r for r in before[family]}
        changes = []
        for b in after[family]:
            a = left[tuple(b.get(f) for f in fields)]
            def states(row):
                out = {uid: "complete_direct" for uid in row.get("direct_unit_ids", [])}
                out.update({uid: "complete_derived" for uid in row.get("derived_only_unit_ids", [])})
                out.update({uid: "unknown" for uid in row.get("unknown_unit_ids", [])})
                return out
            if family == "without_derived_completeness":
                identity = tuple(b.get(f) for f in fields)
                x, y = direct_before[identity], direct_after[identity]
                for values, counts in ((x, a), (y, b)):
                    assert sum(v == "complete_direct" for v in values.values()) == counts["direct_complete"]
                    assert sum(v == "unknown" for v in values.values()) == counts["unknown"]
            else:
                x, y = states(a), states(b)
            moved = [{"unit_id": uid, "before": x.get(uid, "not_complete"), "after": y.get(uid, "not_complete")} for uid in sorted(set(x) | set(y)) if x.get(uid, "not_complete") != y.get(uid, "not_complete")]
            if moved:
                changes.append({**{f: b.get(f) for f in fields}, "before_counts": {f: a[f] for f in ("N", "confirmed_total", "direct_complete", "direct_confirmed", "derived_confirmed", "unknown") if f in a},
                    "after_counts": {f: b[f] for f in ("N", "confirmed_total", "direct_complete", "direct_confirmed", "derived_confirmed", "unknown") if f in b}, "unit_transitions": moved})
        results[family] = changes
    return results


def selftest(legacy):
    count = 0
    def check(value, expected):
        nonlocal count
        assert value == expected, (value, expected); count += 1
    def answer(status="partial_reference", state="comparable_relevant_source_union_examined", binding="examined_relevant"):
        return {"cumulative_classification": status, "targeted_scope_coverage": state,
            "source_bindings": [{"source_id": "SRC-x", "relevance_and_examination": binding}],
            "six_dimensions": {"source_access": "established_compatible"}}
    check(coverage(answer())["incomplete"], False)
    check(coverage(answer(state="incomplete_relevant_scope"))["incomplete"], True)
    check(coverage(answer(binding="unexamined_relevant"))["incomplete"], True)
    check(coverage(answer(binding="unavailable_relevant"))["incomplete"], True)
    check(coverage(answer(status="reference_unverifiable"))["incomplete"], True)
    check(exact_projection(answer()), "not_complete")
    check(exact_projection(answer(status="not_reconstructible_in_examined_corpus")), "not_complete")
    check(exact_projection(answer(state="incomplete_relevant_scope")), "unknown")
    check(exact_projection(answer(status="complete_derived", binding="unexamined_relevant")), "complete")
    check(kappa(["a", "b"], ["a", "b"])["cohen_kappa"], 1.0)
    check(kappa(["a", "a"], ["a", "a"])["cohen_kappa"], None)
    check(kappa(["a", "b"], ["b", "a"])["cohen_kappa"], -1.0)
    check(kappa(["a", "b"], ["a", "a"])["observed_agreement"], .5)
    def row(stage, status="not_reconstructible_in_examined_corpus", **kw):
        return {"unit_id": "U", "component": "suicide_death", "modality": "adverse_event_reports", "reference_id": "R", "window_id": "W", "stage": stage,
            "status": status, "unresolved_conflict_hold": False, "complete_fixed_reference_verified": False, "both_eligible_arms_reconstructed": False,
            "derivation_validated": False, "analysis_scope_closed_for_this_position": True, "cumulative_unresolved_gap_ids": [],
            "assessment_evidence_refs": ["SRC-x#sha256=" + "a" * 64 + ";proof"], **kw}
    # A simple artificial positive rule exercises the same real reconciliation path.
    def pair(status1, status2, stage="A", cov1=None, cov2=None):
        def a(status, cov):
            value = answer(status, cov or ("sufficient_positive_witness_examined" if status in COMPLETE else "comparable_relevant_source_union_examined"))
            value.update({"source_scoped_classification": status, "reported_or_derived_counts_by_arm": {"drug": 0, "placebo": 0}, "denominators_by_arm": {"drug": 10, "placebo": 10}, "count_basis": "derived_from_explicit_report" if status == "complete_derived" else "not_reconstructed"})
            value["source_bindings"][0]["source_content_sha256"] = "a" * 64
            return value
        return {**{f: row(stage)[f] for f in KEY}, "position_id": "P", "R1": a(status1, cov1), "R2": a(status2, cov2)}
    base = {"units": [{"unit_id": "U"}], "assessments": [row(stage) for stage in STAGES]}
    proof = {"position_id": "P", "classification": "complete_derived", "minimum_stage": "A", "required_sources": [{"source_id": "SRC-x", "sha256": "a" * 64, "locator": "test"}], "technical_reason": "test"}
    rules = {"positive_witness_rules": [proof]}; historical = {"rows": []}
    positive, log = apply_reconciliation(base, [pair("complete_derived", "partial_reference", cov2="incomplete_relevant_scope")], rules, historical, legacy)
    check([legacy.indicator([r]) for r in positive["assessments"]], [1, 1, 1, 1])
    check([legacy.indicator([r], allow_derivations=False) for r in positive["assessments"]], [None, None, None, None])
    check([r["analysis_scope_closed_for_this_position"] for r in positive["assessments"]], [False, False, False, False])
    check(len(log["positive_reuse"]), 3)
    check(base["assessments"][0]["status"], "not_reconstructible_in_examined_corpus")
    unknown, _ = apply_reconciliation(base, [pair("partial_reference", "partial_reference", cov2="incomplete_relevant_scope")], {"positive_witness_rules": []}, historical, legacy)
    check([legacy.indicator([r]) for r in unknown["assessments"]], [None, None, None, None])
    exact, _ = apply_reconciliation(base, [pair("partial_reference", "partial_reference", cov2="incomplete_relevant_scope")], {"positive_witness_rules": []}, historical, legacy, False)
    check([legacy.indicator([r]) for r in exact["assessments"]], [None, 0, 0, 0])
    negative, _ = apply_reconciliation(base, [pair("partial_reference", "not_reconstructible_in_examined_corpus")], {"positive_witness_rules": []}, historical, legacy)
    check([legacy.indicator([r]) for r in negative["assessments"]], [0, 0, 0, 0])
    late = copy.deepcopy(proof); late["minimum_stage"] = "B3"
    later, _ = apply_reconciliation(base, [pair("complete_derived", "complete_direct", "B3")], {"positive_witness_rules": [late]}, historical, legacy)
    check([legacy.indicator([r]) for r in later["assessments"]], [0, 0, 0, 1])
    check(later["assessments"][-1]["status"], "complete_derived")
    minimum_b2 = copy.deepcopy(proof); minimum_b2["minimum_stage"] = "B2"
    guarded, _ = apply_reconciliation(base, [pair("complete_derived", "complete_derived", "B3")], {"positive_witness_rules": [minimum_b2]}, historical, legacy)
    check([legacy.indicator([r]) for r in guarded["assessments"]], [0, 0, 1, 1])
    separate = copy.deepcopy(base); separate["assessments"] += [row("B3", component="suicidal_ideation"), row("B3", modality="suicidality_specific_structured_assessment"), row("B3", reference_id="R2"), row("B3", window_id="W2")]
    only_target, _ = apply_reconciliation(separate, [pair("complete_derived", "complete_derived")], rules, historical, legacy)
    check([legacy.indicator([r]) for r in only_target["assessments"][-4:]], [0, 0, 0, 0])
    formal = copy.deepcopy(base); formal["assessments"][0]["cumulative_unresolved_gap_ids"] = ["FORMAL"]
    preserved, _ = apply_reconciliation(formal, [pair("partial_reference", "not_reconstructible_in_examined_corpus")], {"positive_witness_rules": []}, historical, legacy)
    check(preserved["assessments"][0]["cumulative_unresolved_gap_ids"], ["FORMAL"])
    check(legacy.indicator([preserved["assessments"][0]]), None)
    preserved_positive, _ = apply_reconciliation(formal, [pair("complete_derived", "complete_derived")], rules, historical, legacy)
    check(legacy.indicator([preserved_positive["assessments"][0]]), 1)
    check(legacy.indicator([preserved_positive["assessments"][0]], allow_derivations=False), None)
    return {"passed": count, "all_passed": True, "synthetic_only": True}


def run(repository, paired_path, rules_path, out):
    repository, out = Path(repository).resolve(), Path(out).resolve()
    legacy = module(repository / "input_snapshot/codigo/analise_final.py", "reconciliation_legacy")
    sensitivity = module(repository / "validation_sensitivity/reassessed_positive_sensitivity.py", "reconciliation_summary")
    base_path = repository / "current_input/documental_entrada_reconciliada.json"
    base = load(base_path); pop = load(repository / "input_snapshot/dados/populacoes_final.json")
    paired_input = load(paired_path); paired = paired_input["rows"]; rules = load(rules_path)
    historical_proofs = load(repository / "validation/TECHNICAL_WITNESS_RECONCILIATION_57.json")
    roster = load(repository / "linked_review_protocol/SELECTION_ROSTER.json")["rows"]
    assert {key(p) for p in paired} == {key(p) for p in roster} and len(paired) == 109
    assert len({p["position_id"] for p in paired}) == 109
    historical = sensitivity.summarize(base, pop, legacy)
    v14 = load(repository / "source_review109/SOURCE_REVIEW109_INTEGRATION_RESULTS.json")["accepted_conservative_cumulative_integration"]
    # Replay immutable v1.4 inputs to obtain proper direct-only per-unit deltas;
    # its published summary deliberately did not contain those unit lists.
    prior = module(repository / "source_review109/integrate_source_review109.py", "reconciliation_prior_v14")
    prior_pairs = load(repository / "source_review109/HUMAN_SOURCE_REVIEW109_PAIRED.json")["rows"]
    acceptance = load(repository / "source_review109/ACCEPTANCE_FOUR_POSITIVE_WITNESSES.json")
    prior_minimum = {r["positive_position_id_verified"]: r["earliest_admissible_stage_if_guard_passes"] for r in acceptance.get("minimal_source_sets", [])}
    v14_input, _ = prior.apply_pairs(base, prior_pairs, set(acceptance["accepted_position_ids"]), legacy,
        propagate_incomplete=True, proof_reuse_sets=acceptance.get("required_original_source_ids_by_position", {}),
        proof_reuse_min_stages=prior_minimum)
    assert sensitivity.summarize(v14_input, pop, legacy) == v14, "Immutable v1.4 comparison did not reproduce"
    current_input, technical = apply_reconciliation(base, paired, rules, historical_proofs, legacy, True)
    exact_input, exact_technical = apply_reconciliation(base, paired, rules, historical_proofs, legacy, False)
    current = sensitivity.summarize(current_input, pop, legacy)
    exact = sensitivity.summarize(exact_input, pop, legacy)
    current_direct = direct_only_unit_states(current_input, pop, legacy)
    exact_direct = direct_only_unit_states(exact_input, pop, legacy)
    v14_direct = direct_only_unit_states(v14_input, pop, legacy)
    agree = agreement(paired, paired_input["source_examination_ledger"])
    tests = selftest(legacy)
    changed = []
    before_rows = {key(r): r for r in base["assessments"]}
    for r in current_input["assessments"]:
        before = before_rows[key(r)]
        if before != r:
            changed.append({**{f: r[f] for f in KEY}, "before_status": before["status"], "after_status": r["status"],
                "before_effective_indicator": legacy.indicator([before]), "after_effective_indicator": legacy.indicator([r]),
                "changed_fields": [f for f in sorted(set(before) | set(r)) if before.get(f) != r.get(f)],
                "old_row_sha256": hashlib.sha256(json.dumps(before, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()})
    summary = {"exact_paired_positions": 109, "not772_independent_positions": True,
        "decisions_by_kind": dict(collections.Counter(d["decision"] for d in technical["decisions"])),
        "positive_reuse_deductions": len(technical["positive_reuse"]),
        "scope_gap_forward_annotations": len(technical["scope_gap_forward"]),
        "scope_gap_forward_distinct_keys": len({key(r) for r in technical["scope_gap_forward"]}),
        "pending_positive_proof_cases": technical["pending_positive_proofs"],
        "changed_input_keys_vs_historical": len(changed),
        "changed_effective_keys_vs_historical": sum(r["before_effective_indicator"] != r["after_effective_indicator"] for r in changed),
        "AI_technical_decisions_are_not_human_consensus_or_extra_votes": True,
        "raw_human_classifications_preserved": True, "formal_historical_gap_IDs_preserved": True,
        "unknowns_not_clinical_zeros": True, "historical_cutoff_versions_not_uniformly_certified": True}
    assert not technical["pending_positive_proofs"], technical["pending_positive_proofs"]
    report = {"schema": "corrected-source-review109-ai-technical-conciliation-v1", "date": "2026-11-05",
        "historical": historical, "v1_4": v14, "current": current, "without_scope_gap_propagation": exact,
        "agreement": agree, "decision_summary": summary, "decisions": technical["decisions"],
        "technical_deductions": {"positive_reuse": technical["positive_reuse"], "cumulative_scope_gap_union": technical["scope_gap_forward"]},
        "unit_deltas_v1_4_to_current": unit_deltas(v14, current, v14_direct, current_direct),
        "unit_deltas_no_forward_to_current": unit_deltas(exact, current, exact_direct, current_direct),
        "comparison_historical_to_current": sensitivity.compare_tables(historical, current),
        "comparison_v1_4_to_current": sensitivity.compare_tables(v14, current),
        "synthetic_tests": tests, "input_sha256": {"historical_input": sha(base_path), "minimal_paired": sha(paired_path), "technical_source_rules": sha(rules_path),
            "historical_positive_witnesses": sha(repository / "validation/TECHNICAL_WITNESS_RECONCILIATION_57.json"),
            "v1_4_results": sha(repository / "source_review109/SOURCE_REVIEW109_INTEGRATION_RESULTS.json")},
        "limitations": ["Technical AI conciliation explicitly authorized by the user; it is not a third human review or fabricated paired agreement.",
            "Incomplete pertinent source coverage from either assessor is preserved, including at later cumulative layers, unless an independently technically verified exact positive witness resolves that reference.",
            "Negative source-scoped label differences can be analytically equivalent without being rewritten as assessor consensus.",
            "Cohen kappa is descriptive internal label agreement. Positions repeat trials and sources; no naïve independent-position confidence interval or accuracy estimate is provided.",
            "Source versions at the historical cutoff are not uniformly certified; full vital ascertainment and clinical event risks are not established."],
        "clinical_effect_estimates_computed": False, "historical_inputs_and_result_bytes_overwritten": False}
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "MINIMAL_CORRECTED_PAIRED.json", paired_input)
    dump(out / "TECHNICAL_PROOF_RULES.json", rules)
    dump(out / "CURRENT_RECONCILED_INPUT.json", current_input)
    dump(out / "WITHOUT_SCOPE_GAP_PROPAGATION_INPUT.json", exact_input)
    dump(out / "CURRENT_RECONCILIATION_RESULTS.json", report)
    dump(out / "CURRENT_AGREEMENT.json", agree)
    dump(out / "CURRENT_TECHNICAL_DECISIONS.json", technical)
    dump(out / "CURRENT_POSITION_CHANGE_LOG.json", {"rows": changed, "historical_input_sha256": sha(base_path), "full_raw_votes_unchanged": True})
    dump(out / "CURRENT_EDITOR_SUMMARY.json", {"decision_summary": summary,
        "current_B3_whole_population_union": [r for r in current["secondary_union_results"] if r["analysis_set"] == "whole_population_posthoc_exploratory" and r["stage"] == "B3"],
        "current_B3_whole_population_modalities": [r for r in current["modality_results"] if r["analysis_set"] == "whole_population_posthoc_exploratory" and r["stage"] == "B3"],
        "v1_4_B3_whole_population_union": [r for r in v14["secondary_union_results"] if r["analysis_set"] == "whole_population_posthoc_exploratory" and r["stage"] == "B3"],
        "agreement_all109": agree["by_group"][0], "synthetic_tests": tests})
    table_rows = []
    for label, tables in (("historical", historical), ("v1_4", v14), ("current", current), ("without_scope_gap_propagation", exact)):
        for family in ("modality_results", "secondary_union_results", "without_derived_completeness"):
            for row in tables[family]:
                table_rows.append({"model": label, "family": family, **{f: row.get(f) for f in ("analysis_set", "component", "stage", "modality", "N", "confirmed_total", "direct_confirmed", "derived_confirmed", "unknown", "not_complete_in_examined_scope", "corpus_conditional_identification_interval")}})
    with (out / "CURRENT_RESULT_TABLES.csv").open("w", encoding="utf-8", newline="") as f:
        fields = list(table_rows[0]); writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); writer.writeheader()
        for row in table_rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in row.items()})
    manifest = {"algorithm": "sha256", "files": {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "REPRODUCTION_MANIFEST.json"}}
    dump(out / "REPRODUCTION_MANIFEST.json", manifest)
    print(json.dumps({"status": "PASS", "decision_summary": summary, "synthetic_tests": tests,
        "B3_whole": [(r["component"], r["confirmed_total"], r["unknown"]) for r in report["current"]["secondary_union_results"] if r["analysis_set"] == "whole_population_posthoc_exploratory" and r["stage"] == "B3"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--paired", required=True, type=Path)
    parser.add_argument("--rules", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.paired, args.rules, args.out)
