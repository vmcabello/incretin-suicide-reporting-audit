"""Replay the current NEG117 overlay against regenerated, preserved v1.5 inputs."""
from pathlib import Path
import argparse,collections,copy,hashlib,importlib.util,json,tempfile
KEY=('unit_id','component','stage','modality','reference_id','window_id')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def module(p,n):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def key(r):return tuple(r[k] for k in KEY)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(repo,out):
    repo=Path(repo).resolve();out=Path(out);base=repo/'negative117'
    legacy=module(repo/'input_snapshot/codigo/analise_final.py','legacy_neg117')
    summary=module(repo/'validation_sensitivity/reassessed_positive_sensitivity.py','summary_neg117')
    prior=module(repo/'source_review109_reconciled/reconcile_corrected_source_review109.py','prior_neg117')
    pop=load(repo/'input_snapshot/dados/populacoes_final.json');gaps=load(repo/'input_snapshot/dados/lacunas_cumulativas.json')
    patch=load(base/'EXACT_B3_OVERLAY_456.json')['records'];assert len(patch)==456
    updates={key(r):r for r in patch};assert len(updates)==456 and all(k[2]=='B3' for k in updates)
    with tempfile.TemporaryDirectory(prefix='neg117_parent_') as td:
        td=Path(td)
        prior.run(repo,repo/'source_review109_reconciled/MINIMAL_CORRECTED_PAIRED.json',repo/'source_review109_reconciled/TECHNICAL_PROOF_RULES.json',td)
        parent=load(td/'CURRENT_RECONCILED_INPUT.json');alt=load(td/'WITHOUT_SCOPE_GAP_PROPAGATION_INPUT.json')
        assert summary.summarize(parent,pop,legacy)==load(repo/'source_review109_reconciled/CURRENT_RECONCILIATION_RESULTS.json')['current']
        before={key(r):copy.deepcopy(r) for r in parent['assessments']}
        for data in [parent,alt]:
            keys={key(r) for r in data['assessments']};assert len(keys)==5096 and set(updates)<=keys
            for r in data['assessments']:
                k=key(r)
                if k not in updates:continue
                u=updates[k]
                for f in ['analysis_scope_closed_for_this_position','analysis_scope_closure_basis','negative117_review','negative117_unresolved_scope']:
                    if f in u:r[f]=copy.deepcopy(u[f])
                    else:r.pop(f,None)
            legacy.assert_structure(data,pop,gaps)
            data['analytical_release']=True
            data['integration_version']='NEG117_PUBLIC_v1.6.0'
        current=summary.summarize(parent,pop,legacy);alternate=summary.summarize(alt,pop,legacy)
        assert current==load(base/'expected/CURRENT_RESULTS.json')
        assert alternate==load(base/'expected/WITHOUT_PRIOR_FORWARD_PROPAGATION_RESULTS.json')
        after={key(r):r for r in parent['assessments']}
        assert all(before[k]==r for k,r in after.items() if k not in updates)
        assert all(before[k]['status']==r['status'] and before[k].get('status_scope')==r.get('status_scope') for k,r in after.items())
        assert all(before[k]==r for k,r in after.items() if legacy.valid_complete(before[k]))
        values=collections.Counter('complete' if legacy.indicator([r])==1 else 'unknown' if legacy.indicator([r]) is None else 'not_complete' for r in after.values())
        assert values=={'complete':72,'unknown':1282,'not_complete':3742}
        assert sum(legacy.indicator([after[k]]) is None for k in updates)==181
        assert sum(legacy.indicator([after[k]])==0 for k in updates)==275
        write(out/'CURRENT_RESULTS.json',current);write(out/'WITHOUT_PRIOR_FORWARD_PROPAGATION_RESULTS.json',alternate)
        write(out/'CURRENT_PUBLIC_INPUT.json',parent)
        result={'schema':'public-neg117-replay-v1','status':'PASS','exact_positions':456,'unit_dossiers':117,'component_contexts':194,
            'current_effective_position_counts':dict(values),'current_table_rows':sum(len(current[k]) for k in ['modality_results','secondary_union_results','without_derived_completeness','illustrative_membership_scenarios']),
            'earlier_layers_and_unselected_rows_unchanged':True,'historical_source_statuses_unchanged':True,
            'same_overlay_applied_to_both_models':True,'current_and_sensitivity_equal_approved_private_scientific_tables':True,
            'generated_public_input_sha256':digest(out/'CURRENT_PUBLIC_INPUT.json'),
            'public_hash_not_expected_to_equal_private_original_hash':True,'new_clinical_events_or_human_votes_created':False}
        write(out/'REPLAY_QA.json',result)
        return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.out:r=run(a.repository,a.out)
    else:
        with tempfile.TemporaryDirectory(prefix='neg117_replay_') as td:r=run(a.repository,Path(td))
    print(json.dumps(r,sort_keys=True))
