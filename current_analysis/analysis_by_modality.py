"""Descriptive re-expression of the fixed documentary audit by modality.

Standard library only. Inherited classifications are not new human assessments.
No clinical effect model or confidence interval is calculated.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import importlib.util
import json

def load(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(source, reconciled_data=None):
    source=Path(source)
    script=source/'codigo/analise_final.py'
    spec=importlib.util.spec_from_file_location('inherited_audit_analysis',script)
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    data=load(reconciled_data or source/'dados/documental_entrada_final.json')
    pop=load(source/'dados/populacoes_final.json')
    residual=load(source/'dados/selecao_residual_final.json')
    gaps=load(source/'dados/lacunas_cumulativas.json')
    earlier=load(source/'resultados/RESULTADO_DOCUMENTAL_FINAL.json')
    replay=legacy.analyse(data,pop,residual,gaps)
    assert all(earlier[k]==v for k,v in replay.items()),'Inherited results do not reproduce'
    ids=sorted(u['unit_id'] for u in data['units'])
    strata={p['unit_id']:p['designed_eligibility_stratum'] for p in pop['records']}
    rosters={
        'whole_population_posthoc_exploratory':[u for u in ids if strata[u]==legacy.PRIMARY_STRATUM],
        'supported_including_subgroups_complementary':[u for u in ids if strata[u] in {legacy.PRIMARY_STRATUM,legacy.SUBPOPULATION_STRATUM}],
        'operational_historical_complementary':ids,
    }
    groups=collections.defaultdict(list)
    for r in data['assessments']:
        groups[(r['unit_id'],r['component'],r['stage'],r['modality'])].append(r)
    def summary(roster,component,stage,modalities):
        counts=collections.Counter();direct_ids=[];derived_ids=[];unknown_ids=[]
        for uid in roster:
            rows=[r for modality in modalities for r in groups[(uid,component,stage,modality)]]
            value=legacy.indicator(rows)
            if value==1:
                if any(r['status']=='complete_direct' and legacy.valid_complete(r) for r in rows):
                    counts['direct_confirmed']+=1;direct_ids.append(uid)
                else:
                    counts['derived_confirmed']+=1;derived_ids.append(uid)
            elif value is None: counts['unknown']+=1;unknown_ids.append(uid)
            else: counts['not_complete_in_examined_scope']+=1
        n=len(roster);k=counts['direct_confirmed']+counts['derived_confirmed'];u=counts['unknown']
        assert k+u+counts['not_complete_in_examined_scope']==n
        return {'N':n,'direct_confirmed':counts['direct_confirmed'],'derived_confirmed':counts['derived_confirmed'],
                'confirmed_total':k,'unknown':u,'not_complete_in_examined_scope':counts['not_complete_in_examined_scope'],
                'corpus_conditional_identification_interval':[k/n,(k+u)/n] if n else None,
                'direct_unit_ids':direct_ids,'derived_only_unit_ids':derived_ids,'unknown_unit_ids':unknown_ids}
    catalog=data['expected_modality_plan']['catalog']
    specific=[];union=[]
    for label,roster in rosters.items():
        for cell in catalog:
            comp,stage=cell['component'],cell['stage']
            for modality in cell['modalities']:
                specific.append({'analysis_set':label,'component':comp,'stage':stage,'modality':modality,
                                 **summary(roster,comp,stage,[modality])})
            union.append({'analysis_set':label,'component':comp,'stage':stage,'interpretation':'secondary_union_of_non_equivalent_modalities',
                          **summary(roster,comp,stage,cell['modalities'])})
    # Check every cell that was already distributed, including unknowns.
    for old in earlier['modality_results']:
        label={'primary_whole_population':'whole_population_posthoc_exploratory','complementary_operational':'operational_historical_complementary'}[old['analysis_set']]
        new=next(r for r in specific if all(r[k]==v for k,v in [('analysis_set',label),('component',old['component']),('stage',old['stage']),('modality',old['modality'])]))
        assert (new['N'],new['confirmed_total'],new['unknown'],new['corpus_conditional_identification_interval'])==(old['N'],old['complete'],old['unknown'],old['logical_bounds'])
    illustrative=[]
    additions=[('additional_12_population_unresolved',12),('additional_35_membership_unknown',35),
               ('additional_2_identity_unresolved',2),('additional_49_combined_disjoint_uncertainties',49)]
    for r in union:
        if r['analysis_set']!='whole_population_posthoc_exploratory' or r['stage']!='B3':continue
        for scenario,m in additions:
            n=r['N']+m;k=r['confirmed_total'];u=r['unknown']+m
            illustrative.append({'scenario':scenario,'component':r['component'],'assumed_additional_distinct_fully_eligible_units':m,
                'N_hypothetical':n,'known_confirmed_carried_forward':k,'unknown_hypothetical':u,
                'corpus_conditional_identification_interval':[k/n,(k+u)/n],
                'assumption':'Every added block is a distinct fully eligible unit and its reconstruction status is unknown. This is not an admission decision or a bound on unlocated trials.'})
    direct_sensitivity=[]
    for label,roster in rosters.items():
        for comp in legacy.COMPONENTS:
            vals=[]
            for uid in roster:
                rows=[r for (u,c,s,m),rs in groups.items() if u==uid and c==comp and s=='B3' for r in rs]
                vals.append(legacy.indicator(rows,allow_derivations=False))
            old=legacy.summarize(vals)
            direct_sensitivity.append({'analysis_set':label,'component':comp,'stage':'B3','N':old['N'],
                'direct_complete':old['complete'],'unknown':old['unknown'],
                'not_complete_in_examined_scope':old['not_complete_in_examined_scope'],
                'corpus_conditional_identification_interval':old['logical_bounds']})
    inputs={str(p.relative_to(source)).replace('\\','/'):sha(p) for p in [script,source/'dados/documental_entrada_final.json',source/'dados/populacoes_final.json',source/'dados/selecao_residual_final.json',source/'dados/lacunas_cumulativas.json',source/'resultados/RESULTADO_DOCUMENTAL_FINAL.json']}
    return {'schema':'exploratory_modality_audit_20261104','source_snapshot':'FINAL-20261101',
            'revised_presentation_date':'2026-11-04','scope':'Fixed historically assembled corpus; no exhaustive trial-universe claim',
            'posthoc_analysis_hierarchy':True,'new_source_or_human_classifications':False,
            'primary_presentation':'Separate modality-specific counts; absolute counts before conditional percentages',
            'original_union_is_secondary':True,'legacy_replay_matches_distributed_results':True,
            'roster_sizes':{k:len(v) for k,v in rosters.items()},'modality_results':specific,
            'secondary_union_results':union,'without_derived_completeness':direct_sensitivity,
            'illustrative_membership_scenarios':illustrative,
            'interval_limitations':['Conditional on admitted units and inherited classifications','Not sampling confidence intervals','Do not cover unlocated trials, selection error, coding error or missed updates','Illustrative added-block scenarios do not make the search exhaustive'],
            'alternative_reference_sensitivities':{'ITT':'Not estimated: different arm-level denominators and windows require scope-specific re-extraction',
                'safety_population':'Not relabelled automatically as treated reference',
                'on_treatment':'Not estimated from fixed full-target classifications',
                'known_vital_status_followup':'Not estimated without explicit complete follow-up information'},
            'human_validation_status':'Independent assessments reported by authors; correction426 supplied as a shared technical reconsolidation. No new reliability statistic estimated',
            'technical_reconciliation':'426 negative scoped statuses retained; 57 positive primary witnesses technically checked; no classification-value change',
            'clinical_effect_estimates_computed':False,'input_sha256':inputs,
            'reconciled_input_sha256':sha(reconciled_data) if reconciled_data else None}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--data');args=p.parse_args()
    result=run(args.source,args.data);target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'legacy_reproduced':True,'rosters':result['roster_sizes'],'modality_cells':len(result['modality_results']),'union_cells':len(result['secondary_union_results']),'new_human_classifications':False},ensure_ascii=False))

if __name__=='__main__':main()
