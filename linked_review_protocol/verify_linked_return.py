"""Structural/consistency checks only; never certify who read or scientific truth."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CLASSES={'complete_direct','complete_derived','partial_reference','not_reconstructible_in_examined_corpus','reference_unverifiable','public_source_unavailable'}
DIMS={'numerator','denominator','window','subpopulation','counting_unit','source_access'}
DIM_VALUES={'established_compatible','explicitly_incompatible','missing_after_examination','unknown_unexamined_or_unavailable','not_established'}
BINDINGS={'examined_relevant','unexamined_relevant','unavailable_relevant','not_relevant_for_this_target','auxiliary_not_primary_evidence'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def text(v):return isinstance(v,str) and bool(v.strip())
def flatten(x):return {p['position_id']:p for c in x['cases'] for p in c['positions']}

def verify(value, template, allow_draft=False):
    errors=[]
    for k in ('schema','protocol_id','protocol_sha256','reviewer'):
        if value.get(k)!=template[k]:errors.append('Immutable metadata mismatch: '+k)
    if value.get('external_or_memory_blinded_validation') is not False:errors.append('Prior exposure/validation scope not preserved')
    actual=flatten(value);expected=flatten(template)
    if set(actual)!=set(expected):errors.append('Exact 109-position set mismatch')
    if len(actual)!=109 or sum(len(c['positions']) for c in value['cases'])!=109:errors.append('Position count/duplicate mismatch')
    for pid,p in actual.items():
        ref=expected.get(pid)
        if not ref:continue
        for k in ('unit_id','component','stage','modality','reference_id','window_id','navigation_source_ids'):
            if p.get(k)!=ref[k]:errors.append(pid+': immutable target mismatch '+k)
        if {b['source_id'] for b in p['answer']['source_bindings']}!=set(ref['navigation_source_ids']):errors.append(pid+': source binding set changed')
    if allow_draft:
        return {'status':'STRUCTURE_CHECKED_DRAFT_NOT_A_HUMAN_RETURN','errors':errors,'positions':len(actual),'dossiers':len(value['cases']),'scientific_or_process_certification':False}
    if value.get('status')!='HUMAN_RETURN_LOCKED_FOR_COMPARISON':errors.append('Return not locked')
    if value.get('completed_by_human')!='yes':errors.append('Human completion declaration absent')
    for k in ('locked_at','separate_before_discussion','prior_exposure_declaration','AI_assistance_declaration'):
        if not text(value.get(k)):errors.append('Missing process declaration: '+k)
    for c in value['cases']:
        source_by_id={s['source_id']:s for s in c['source_examinations']}
        needed={sid for p in c['positions'] for sid in p['navigation_source_ids']}
        if set(source_by_id)!=needed:errors.append(c['unit_id']+': source-examination ledger set mismatch')
        for sid,s in source_by_id.items():
            for k in ('source_identity_verified','source_kind_verified','examination_status','examined_at'):
                if not text(s.get(k)):errors.append(sid+': missing '+k)
            if s.get('examination_status')=='examined':
                for k in ('version_observed','sections_actually_examined','examined_at'):
                    if not text(s.get(k)):errors.append(sid+': examined source missing '+k)
            elif not text(s.get('access_or_scope_limitation')):errors.append(sid+': explain unexamined/unavailable/auxiliary state')
        for p in c['positions']:
            a=p['answer'];pid=p['position_id']
            for k in ('source_scoped_classification','cumulative_classification'):
                if a.get(k) not in CLASSES:errors.append(pid+': missing/invalid '+k)
            for k in ('count_basis','targeted_scope_coverage','scope_comparability_rationale','evidence_and_rationale','prior_answer_exposure','formed_before_discussion','substantive_AI_judgment_used','assessed_at'):
                if not text(a.get(k)):errors.append(pid+': missing '+k)
            if set(a['six_dimensions'])!=DIMS:errors.append(pid+': six dimensions changed')
            for k,v in a['six_dimensions'].items():
                if v not in DIM_VALUES:errors.append(pid+': dimension unassessed '+k)
            for b in a['source_bindings']:
                if b.get('relevance_and_examination') not in BINDINGS or not text(b.get('rationale')):errors.append(pid+': source relevance/rationale missing '+b['source_id'])
                if b.get('relevance_and_examination')=='examined_relevant':
                    if not text(b.get('locator_for_this_target')):errors.append(pid+': target-specific locator missing '+b['source_id'])
                    if source_by_id.get(b['source_id'],{}).get('examination_status')!='examined':errors.append(pid+': source examination inconsistency '+b['source_id'])
            if a.get('cumulative_classification') in ('complete_direct','complete_derived'):
                if a.get('reported_or_derived_counts_by_arm') is None or a.get('denominators_by_arm') is None:errors.append(pid+': complete answer lacks count/denominator')
                if not any(b.get('relevance_and_examination')=='examined_relevant' for b in a['source_bindings']):errors.append(pid+': no examined relevant source')
                if any(v!='established_compatible' for v in a['six_dimensions'].values()):errors.append(pid+': complete with unresolved/incompatible dimension')
                basis='direct_report' if a['cumulative_classification']=='complete_direct' else 'derived_from_explicit_report'
                if a.get('count_basis')!=basis:errors.append(pid+': direct/derived mismatch')
            if a.get('cumulative_classification')=='not_reconstructible_in_examined_corpus':
                if any(b.get('relevance_and_examination') in ('unexamined_relevant','unavailable_relevant') for b in a['source_bindings']):errors.append(pid+': pertinent unresolved source precludes negative closure')
                if a.get('targeted_scope_coverage')!='comparable_relevant_source_union_examined':errors.append(pid+': pertinent source-union coverage not established')
    return {'status':'PASS' if not errors else 'FAIL','errors':errors,'positions':len(actual),'dossiers':len(value['cases']),'scientific_or_process_certification':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('return_json');ap.add_argument('--template',required=True);ap.add_argument('--allow-draft',action='store_true');a=ap.parse_args()
    result=verify(read(a.return_json),read(a.template),a.allow_draft)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['errors']))
