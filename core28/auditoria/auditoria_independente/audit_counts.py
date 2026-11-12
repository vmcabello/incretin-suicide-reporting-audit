"""Independent count implementation; no shared root analysis functions.

Counts documentary trial-population judgments, never clinical events or people.
Writes only this audit folder. All frozen inputs remain read-only.
"""
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
INPUT = ROOT / 'outputs/julgamentos_nucleo28_referencias_modalidades_2026-11-11/JULGAMENTOS_FECHADOS_28_QUATRO_REFERENCIAS.json'
FREEZE = INPUT.with_name('CONGELAMENTO_TECNICO.json')
CORE = ROOT / 'outputs/integracao_nucleo28_2026-11-11/NUCLEO_CONGELADO_28.json'
DOC = json.loads(INPUT.read_text(encoding='utf-8-sig'))
FROZEN = json.loads(FREEZE.read_text(encoding='utf-8-sig'))
ROWS = DOC['records']
assert hashlib.sha256(INPUT.read_bytes()).hexdigest() == FROZEN['sha256']
assert hashlib.sha256(CORE.read_bytes()).hexdigest() == FROZEN['core_sha256']
assert len(ROWS) == 1008
KEY = lambda r: (r['unit_id'], r['reference_id'], r['component'], r['modality'])
assert len(set(map(KEY, ROWS))) == 1008
REFS = ['REF_HISTORICAL_TREATED', 'REF_ITT', 'REF_SAFETY_SOURCE', 'REF_ON_TREATMENT']
COMPS = ['suicidal_ideation', 'suicide_attempt', 'suicide_death']
MODS = ['adverse_event_reports', 'suicidality_specific_structured_assessment', 'all_cause_mortality_derivation']
UNITS = sorted({r['unit_id'] for r in ROWS})
assert len(UNITS) == 28
assert len({u.split(':')[0] for u in UNITS}) == 27
for r in ROWS:
    s, t, ind = r['analytical_state'], r['source_scoped_status'], r['documentary_indicator']
    assert s in {'complete', 'unknown', 'bounded_not_complete', 'not_applicable'}
    assert ind == ({'complete':1, 'bounded_not_complete':0}.get(s))
    assert (s == 'not_applicable') == (r['modality'] == MODS[2] and r['component'] != COMPS[2])
    assert (s == 'complete') == (t in ['complete_direct', 'complete_derived'])

def counts(records):
    states = Counter(r['analytical_state'] for r in records)
    kinds = Counter(r['source_scoped_status'] for r in records)
    n = len(records) - states['not_applicable']
    c, u, b = states['complete'], states['unknown'], states['bounded_not_complete']
    assert c + u + b == n
    return {'N':n, 'C_direct':kinds['complete_direct'], 'C_derived':kinds['complete_derived'],
            'C':c, 'U':u, 'B':b, 'NA':states['not_applicable'],
            'lower_numerator':c, 'upper_numerator':c+u,
            'lower_pct':100*c/n if n else None, 'upper_pct':100*(c+u)/n if n else None}

def union_state(records):
    applicable = [r for r in records if r['analytical_state'] != 'not_applicable']
    assert applicable
    if any(r['analytical_state'] == 'complete' for r in applicable):
        return 'complete'
    if any(r['analytical_state'] == 'unknown' for r in applicable):
        return 'unknown'
    assert all(r['analytical_state'] == 'bounded_not_complete' for r in applicable)
    return 'bounded_not_complete'

strata = []
union_cells = []
for ref in REFS:
    for comp in COMPS:
        for mod in MODS:
            rs = [r for r in ROWS if (r['reference_id'],r['component'],r['modality']) == (ref,comp,mod)]
            assert len(rs) == 28
            strata.append({'reference':ref,'component':comp,'modality':mod,**counts(rs)})
        for unit in UNITS:
            rs = [r for r in ROWS if (r['reference_id'],r['component'],r['unit_id']) == (ref,comp,unit)]
            state = union_state(rs)
            direct = any(r['source_scoped_status']=='complete_direct' for r in rs)
            union_cells.append({'unit_id':unit,'trial':rs[0]['trial'], 'program':rs[0]['program'],
                                'reference_id':ref,'component':comp,
                                'analytical_state':state,
                                'source_scoped_status':('complete_direct' if direct else 'complete_derived') if state=='complete' else state})
union_summary = []
for ref in REFS:
    for comp in COMPS:
        rs = [r for r in union_cells if (r['reference_id'],r['component']) == (ref,comp)]
        union_summary.append({'reference':ref,'component':comp,**counts(rs)})

positive_lists = []
for s in strata:
    positives=[{'unit_id':r['unit_id'],'trial':r['trial'],'status':r['source_scoped_status']} for r in ROWS
               if (r['reference_id'],r['component'],r['modality'])==(s['reference'],s['component'],s['modality'])
               and r['analytical_state']=='complete']
    positive_lists.append({k:s[k] for k in ['reference','component','modality']} | {'complete_units':positives})

osa = [u for u in UNITS if sum(v.split(':')[0]==u.split(':')[0] for v in UNITS)>1]
assert len(osa) == 2
osa_rows = [r for r in union_cells if r['unit_id'] in osa]
audit = {'input_sha256':FROZEN['sha256'], 'auditor':'AI computational audit, not human validation',
         'grid_checks_passed':True,'trial_populations':28,'registry_ids':27,
         'by_reference_component_modality':strata,'secondary_union':union_summary,
         'secondary_union_cells':union_cells,'positive_membership':positive_lists,
         'osa_population_ids':osa,'osa_union_cells':osa_rows}
(OUT/'INDEPENDENT_COUNTS.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# Alternative evidence restrictions retain all 28 units and original unknowns.
# Derived-only completeness becomes unknown when the derivation is withheld;
# we have no separate frozen direct-examination negative disposition.
scenarios = {}
amended = {'NCT00781937','NCT04657016','NCT05024032','NCT04920903'}
core_doc = json.loads(CORE.read_text(encoding='utf-8-sig'))
amended_actual = {r['registry_id'] for r in core_doc['records'] if r['status']=='included_by_author_ratified_population_amendment'}
assert len(amended_actual)==4
amended = amended_actual
runin = {'NCT00781937','NCT04657016'}
for label in ['exclude_allcause_modality', 'direct_witness_only', 'omit_population_amendments', 'omit_dietary_runin']:
    scenario_rows=[]
    for ref in REFS:
        for comp in COMPS:
            chosen=[]
            for unit in UNITS:
                if label=='omit_population_amendments' and unit.split(':')[0] in amended: continue
                if label=='omit_dietary_runin' and unit.split(':')[0] in runin: continue
                rs=[dict(r) for r in ROWS if (r['reference_id'],r['component'],r['unit_id'])==(ref,comp,unit)]
                if label=='exclude_allcause_modality': rs=[r for r in rs if r['modality']!=MODS[2]]
                if label=='direct_witness_only':
                    for r in rs:
                        if r['source_scoped_status']=='complete_derived':
                            r['source_scoped_status']='derived_witness_withheld'
                            r['analytical_state']='unknown'
                state=union_state(rs)
                direct=any(r['source_scoped_status']=='complete_direct' for r in rs)
                chosen.append({'analytical_state':state,'source_scoped_status':('complete_direct' if direct else 'complete_derived') if state=='complete' else state})
            scenario_rows.append({'reference':ref,'component':comp,**counts(chosen)})
    scenarios[label]=scenario_rows

# A registry-level target requires complete reconstruction of EVERY independently
# randomized population under that NCT; this changes the estimand, not membership.
registry_rows=[]
for ref in REFS:
    for comp in COMPS:
        nested=[]
        for reg in sorted({u.split(':')[0] for u in UNITS}):
            xs=[r for r in union_cells if r['unit_id'].split(':')[0]==reg and (r['reference_id'],r['component'])==(ref,comp)]
            if all(x['analytical_state']=='complete' for x in xs): state='complete'
            elif any(x['analytical_state']=='bounded_not_complete' for x in xs): state='bounded_not_complete'
            else: state='unknown'
            direct=all(x['source_scoped_status']=='complete_direct' for x in xs)
            nested.append({'analytical_state':state,'source_scoped_status':('complete_direct' if direct else 'complete_derived') if state=='complete' else state})
        registry_rows.append({'reference':ref,'component':comp,**counts(nested)})
scenarios['registry_target_all_nested_populations_complete']=registry_rows
(OUT/'INDEPENDENT_SENSITIVITIES.json').write_text(json.dumps({'derived_only_becomes_unknown':True,'amended_registry_ids':sorted(amended),'results':scenarios},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'grid_checks_passed':True,'input_sha256':FROZEN['sha256'],'union_counts':union_summary,'amended':sorted(amended)},indent=2))
