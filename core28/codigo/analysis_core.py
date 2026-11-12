"""Documentary audit calculations. Standard library only; no clinical pooling."""
from collections import Counter, defaultdict
from itertools import product, combinations
import hashlib, json

REFS = ['REF_HISTORICAL_TREATED','REF_ITT','REF_SAFETY_SOURCE','REF_ON_TREATMENT']
COMPS = ['suicidal_ideation','suicide_attempt','suicide_death']
MODS = ['adverse_event_reports','suicidality_specific_structured_assessment','all_cause_mortality_derivation']
STATES = ['complete','bounded_not_complete','unknown']
SOURCE_HASH = '9214d5de3565b49c127c4c414e02edecc88a9f15588112344a573871dbb431f7'
CORE_HASH = 'c6632aaca797c46a540552e56be239afb2ac1b3725dad42cae728df8e44bc36f'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def key(r):
    return tuple(r[k] for k in ['unit_id','reference_id','component','modality'])

def applicable(c, m):
    return m != MODS[2] or c == COMPS[2]

def validate(rows, core):
    units = {r['unit_id'] for r in core}
    assert len(core) == len(units) == 28
    assert len({r['registry_id'] for r in core}) == 27
    expected = set(product(units, REFS, COMPS, MODS))
    assert len(rows) == len(expected) == 1008
    assert len({key(r) for r in rows}) == len(rows), 'duplicate analytical cell'
    assert {key(r) for r in rows} == expected, 'missing/unexpected analytical cell'
    for r in rows:
        a = applicable(r['component'], r['modality'])
        s, t, v = r['analytical_state'], r['source_scoped_status'], r['documentary_indicator']
        assert r['source_scope_id'] == 'CORE28_CURRENT_CUMULATIVE_20261111'
        if not a:
            assert s == t == 'not_applicable' and v is None
        elif s == 'complete':
            assert t in ['complete_direct','complete_derived'] and v == 1
            assert r.get('arm_facts') and r.get('target_population') and r.get('target_window')
            assert not r.get('unresolved_dimensions')
        elif s == 'bounded_not_complete':
            assert v == 0 and (r.get('examined_scope_closed') or r.get('source_scope_closure'))
        else:
            assert s == 'unknown' and v is None and r.get('unresolved_dimensions')

def compact(r, metadata, withdraw_derived=False):
    s = r['analytical_state']
    withheld = withdraw_derived and r['source_scoped_status'] == 'complete_derived'
    if withheld:
        s = 'unknown'
    return dict(unit_id=r['unit_id'], registry_id=metadata['registry_id'], trial=metadata['trial'],
        program=metadata['program'], reference_id=r['reference_id'], component=r['component'],
        modality=r['modality'], state=s,
        proof_kind=('direct' if r['source_scoped_status']=='complete_direct' else 'derived') if s=='complete' else None,
        judgment_ids=[r['judgment_id']], original_state=r['analytical_state'], baseline_state=r['analytical_state'],
        original_source_scoped_status=r['source_scoped_status'], derived_proof_withheld=bool(withheld),
        technical_not_new_human_vote=True)

def aggregate_logic(cells, logic):
    """Three-valued OR for modalities; AND for all populations in a registry."""
    cells = [r for r in cells if r['state'] != 'not_applicable']
    if not cells:
        return 'not_applicable', None
    states = [r['state'] for r in cells]
    assert set(states) <= set(STATES)
    if logic == 'any':
        state = 'complete' if 'complete' in states else 'unknown' if 'unknown' in states else 'bounded_not_complete'
    elif logic == 'all':
        state = 'bounded_not_complete' if 'bounded_not_complete' in states else 'unknown' if 'unknown' in states else 'complete'
    else:
        raise ValueError(logic)
    kind = None
    if state == 'complete':
        kinds = [r['proof_kind'] for r in cells if r['state']=='complete']
        kind = ('direct' if 'direct' in kinds else 'derived') if logic=='any' else ('direct' if all(k=='direct' for k in kinds) else 'derived')
    return state, kind

def union_cells(rows, modalities=MODS):
    groups = defaultdict(list)
    for r in rows:
        if r['modality'] in modalities:
            groups[(r['unit_id'],r['reference_id'],r['component'])].append(r)
    out=[]
    for _, cells in sorted(groups.items()):
        s,kind=aggregate_logic(cells,'any'); x=cells[0]
        base,_=aggregate_logic([dict(c,state=c.get('baseline_state',c['state'])) for c in cells],'any')
        out.append({k:x[k] for k in ['unit_id','registry_id','trial','program','reference_id','component']} |
            dict(modality='secondary_any_modality', state=s, proof_kind=kind, baseline_state=base,
                judgment_ids=[j for c in cells for j in c['judgment_ids']],
                complete_modalities=[c['modality'] for c in cells if c['state']=='complete'],
                unknown_modalities=[c['modality'] for c in cells if c['state']=='unknown'],
                all_applicable_modalities_bounded_negative=all(c['state']=='bounded_not_complete' for c in cells if c['state']!='not_applicable')))
    return out

def registry_conjunction(rows):
    groups=defaultdict(list)
    for r in rows:
        groups[(r['registry_id'],r['reference_id'],r['component'],r['modality'])].append(r)
    out=[]
    for _,cells in sorted(groups.items()):
        s,kind=aggregate_logic(cells,'all');x=cells[0]
        base,_=aggregate_logic([dict(c,state=c.get('baseline_state',c['state'])) for c in cells],'all')
        out.append({k:x[k] for k in ['registry_id','reference_id','component','modality','program']} |
            dict(unit_id=x['registry_id'], trial=x['registry_id'], state=s, proof_kind=kind, baseline_state=base,
                 member_population_ids=[c['unit_id'] for c in cells],
                 judgment_ids=[j for c in cells for j in c['judgment_ids']]))
    return out

def summarize(rows, scenario_id, analysis_level='modality_primary', denominator_unit='randomized_population'):
    groups=defaultdict(list)
    for r in rows:
        groups[(r['reference_id'],r['component'],r['modality'])].append(r)
    out=[]
    for (ref,comp,mod),cells in sorted(groups.items()):
        eligible=[r for r in cells if r['state']!='not_applicable']
        assert len({r['unit_id'] for r in cells}) == len(cells)
        ct=Counter(r['state'] for r in eligible)
        n=len(eligible); c=ct['complete'];u=ct['unknown'];b=ct['bounded_not_complete']
        d=sum(r['state']=='complete' and r['proof_kind']=='direct' for r in eligible)
        v=c-d
        assert d+v+b+u == n
        out.append(dict(scenario_id=scenario_id, analysis_level=analysis_level, denominator_unit=denominator_unit,
            reference_id=ref, component=comp, modality=mod, N=n,
            complete=c, complete_direct_supported=d, complete_requires_derivation=v,
            bounded_not_complete=b, unknown=u, not_applicable=len(cells)-n,
            unknown_introduced_by_proof_withholding=sum(r['state']=='unknown' and r.get('baseline_state')=='complete' for r in eligible),
            identification_lower=c/n if n else None, identification_upper=(c+u)/n if n else None,
            lower_numerator=c if n else None, upper_numerator=c+u if n else None,
            interval_type='conditional_identification_not_confidence' if n else 'not_applicable',
            complete_ids=[r['unit_id'] for r in eligible if r['state']=='complete'],
            direct_supported_ids=[r['unit_id'] for r in eligible if r['state']=='complete' and r['proof_kind']=='direct'],
            derived_required_ids=[r['unit_id'] for r in eligible if r['state']=='complete' and r['proof_kind']=='derived'],
            unknown_ids=[r['unit_id'] for r in eligible if r['state']=='unknown'],
            bounded_not_complete_ids=[r['unit_id'] for r in eligible if r['state']=='bounded_not_complete']))
    return out

def transitions(rows):
    lookup={(r['unit_id'],r['reference_id'],r['component'],r['modality']):r for r in rows}
    units=sorted({r['unit_id'] for r in rows});out=[]
    for a,b in combinations(REFS,2):
        for c,m in product(COMPS,MODS):
            if not applicable(c,m):continue
            cells=[]
            for sa,sb in product(STATES,STATES):
                members=[u for u in units if lookup[u,a,c,m]['state']==sa and lookup[u,b,c,m]['state']==sb]
                cells.append(dict(from_state=sa,to_state=sb,n=len(members),unit_ids=members))
            out.append(dict(reference_from=a,reference_to=b,component=c,modality=m,N=len(units),cells=cells,
                causal_interpretation=False, significance_test_performed=False))
    return out

def run(rows, core):
    validate(rows,core);meta={x['unit_id']:x for x in core}
    flat=[compact(r,meta[r['unit_id']]) for r in rows]
    primary=summarize(flat,'FULL28')
    union=union_cells(flat)
    secondary=summarize(union,'FULL28','union_secondary')
    sensitivity=[];scenarios=[]
    def add(sid,cells,description,denom='randomized_population',union_override=None):
        scenarios.append(dict(scenario_id=sid,definition=description,denominator_unit=denom,
            unit_ids=sorted({x['unit_id'] for x in cells}),source_judgments_changed=False))
        sensitivity.extend(summarize(cells,sid,denominator_unit=denom))
        u=union_cells(cells) if union_override is None else union_override
        sensitivity.extend(summarize(u,sid,'union_secondary',denom))
    withdrawn=[compact(r,meta[r['unit_id']],True) for r in rows]
    add('WITHHOLD_DERIVED_PROOFS',withdrawn,'Evidence-withholding stress test. Frozen derived positives become unknown in this scenario only; original unknowns remain unknown. This does not establish that direct evidence is absent.')
    nomort=[r for r in flat if r['modality']!=MODS[2]]
    add('NO_MORTALITY_MODALITY',nomort,'Omit all-cause mortality derivation modality. AE derivations remain admissible. This is not a direct-only scenario.')
    subset=[r for r in flat if not meta[r['unit_id']].get('membership_amendment')]
    assert len({r['unit_id'] for r in subset})==24
    add('WITHOUT_FOUR_MEMBERSHIP_AMENDMENTS',subset,'Composition sensitivity excluding the four ratified amendment populations. Not a claim of ineligibility; the authorized main core remains28.')
    for p in ['SCALE','STEP','SURMOUNT']:
        add('PROGRAM_'+p,[r for r in flat if r['program']==p],'Descriptive programme stratum; no randomized comparison between programmes.')
        add('LEAVE_OUT_'+p,[r for r in flat if r['program']!=p],'Composition sensitivity removing '+p+'; no inference of a drug or programme effect.')
    # Per-modality conjunction across populations; secondary registry union must
    # first union modalities WITHIN each population, then require ALL populations.
    reg=registry_conjunction(flat)
    reg_union=registry_conjunction(union)
    add('REGISTRY27_ALL_POPULATIONS',reg,'Different estimand: each registry is complete only if every member randomized population is complete. Secondary: AND across population-specific ORs, not OR of registry-level ANDs. No patient counts are pooled.', 'registry_all_populations',reg_union)
    overlap=[]
    for ref,c in product(REFS,COMPS):
        uu=[r for r in union if r['reference_id']==ref and r['component']==c]
        signatures=defaultdict(list)
        for r in uu:
            if r['state']=='complete':signatures[' + '.join(sorted(r['complete_modalities']))].append(r['unit_id'])
        overlap.append(dict(reference_id=ref,component=c,complete_union=sum(len(v) for v in signatures.values()),
            modality_memberships=sum(len(r['complete_modalities']) for r in uu),
            mutually_exclusive_patterns=[dict(complete_modalities=k.split(' + '),n=len(v),unit_ids=v) for k,v in sorted(signatures.items())]))
    return dict(version='CORE28-DOCUMENTARY-ANALYSIS-v1',date='2026-11-11',
        source_sha256=SOURCE_HASH,core_sha256=CORE_HASH,
        primary_modality_tables=primary,secondary_union_tables=secondary,
        sensitivity_definitions=scenarios,sensitivity_tables=sensitivity,
        reference_transitions=transitions(flat),overlap_audit=overlap,
        population_states=flat,secondary_population_states=union,
        clinical_events_or_patients_pooled=False,new_ratings_generated=False,
        historical_source_layers_recomputed=False,inferential_tests_performed=False)
