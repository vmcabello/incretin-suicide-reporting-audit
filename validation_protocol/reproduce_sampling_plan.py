"""Replay sampling only, without human judgments or clinical-risk analysis."""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,math
HERE=Path(__file__).resolve().parent
KEY=['unit_id','component','stage','modality','reference_id','window_id']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def hs(s):return hashlib.sha256(s.encode()).hexdigest()
def key(r):return '|'.join(r[k] for k in KEY)

def run(repo):
    plan=read(HERE/'PROTOCOL.json');distributed=read(HERE/'SAMPLING_ROSTER.json')['records']
    script=repo/'input_snapshot/codigo/analise_final.py'
    spec=importlib.util.spec_from_file_location('sampling_source_indicator',script)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    rows={key(r):r for r in read(repo/'current_input/documental_entrada_reconciliada.json')['assessments']}
    values={k:mod.indicator([r]) for k,r in rows.items()}
    assert collections.Counter(values.values())=={0:4030,None:1009,1:57}
    expected={}
    for k,v in values.items():
        if v==1:expected[k]={'design_group':'all_complete','stratum_id':'positive_census','N_h':57,'n_h':57,'selection_probability':1.0,'weight':1.0}
    strata=collections.defaultdict(list)
    for k,r in rows.items():
        if values[k]==0:strata[(r['component'],r['modality'],r['stage'],r['status'])].append(k)
    for st,ks in sorted(strata.items()):
        n=math.ceil(.1*len(ks));chosen=sorted(ks,key=lambda k:hs('EJCP-P4-20261104-VALIDATION-v1|'+k))[:n]
        for k in chosen:expected[k]={'design_group':'retained_probability_sample_not_complete','stratum_id':'STR-'+hs('|'.join(st))[:12],
          'N_h':len(ks),'n_h':n,'selection_probability':n/len(ks),'weight':len(ks)/n}
    strata=collections.defaultdict(list)
    for k,r in rows.items():
        if values[k] is None:strata[(r['component'],r['modality'],r['stage'])].append(k)
    alloc={st:min(len(ks),max(2,math.floor(180*len(ks)/1009))) for st,ks in strata.items()}
    while sum(alloc.values())<180:
        st=sorted([st for st in strata if alloc[st]<len(strata[st])],key=lambda st:(-(180*len(strata[st])/1009-alloc[st]),st))[0]
        alloc[st]+=1
    for st,ks in sorted(strata.items()):
        chosen=sorted(ks,key=lambda k:hs(plan['unknown_sample']['seed']+'|'+k))[:alloc[st]]
        for k in chosen:expected[k]={'design_group':'sampled_unknown','stratum_id':'UNKNOWN-'+hs('|'.join(st))[:12],
          'N_h':len(ks),'n_h':alloc[st],'selection_probability':alloc[st]/len(ks),'weight':len(ks)/alloc[st]}
    got={key(r):r for r in distributed}
    assert len(got)==663 and set(got)==set(expected),'Selected keys differ'
    for k,record in expected.items():
        assert got[k]['position_id']=='POS-'+hs(k)[:20]
        for f,v in record.items():assert got[k][f]==v,(k,f,got[k][f],v)
    frame=read(HERE/'PILOT_LOCAL_SOURCE_FRAME.json')['records']
    eligibility={r['unit_id']:r['eligible_positions'] for r in frame}
    assert len(eligibility)==136
    for uid,ps in eligibility.items():
        for r in ps:
            assert r['position_key'] in got and rows[r['position_key']]['unit_id']==uid
            for s in r['registry_source_identifiers']:
                assert s['registry_id_in_original_payload']==uid.split(':')[0] and len(s['sha256'])==64
    seed=plan['nested_alternative_reference_pilot']['pilot_seed']
    chosen=sorted(eligibility,key=lambda u:hs(seed+'|'+u))[:30]
    pilot=set()
    for uid in chosen:
        ks=[r['position_key'] for r in eligibility[uid]]
        k=sorted(ks,key=lambda k:(-['A','B1','B2','B3'].index(rows[k]['stage']),hs(seed+'|'+k)))[0]
        pilot.add(k)
    assert {k for k,r in got.items() if r['nested_alternative_reference_pilot']}==pilot
    return {'sampling_design_reproduced':True,'positions':663,'all_complete':57,'reused_not_complete_sample':426,
      'sampled_unknown':180,'unknown_strata':len(strata),'conditional_pilot_frame_units':136,'nested_pilot_units':30,
      'genuine_new_human_returns':0,'agreement_computed':False,'accuracy_validated':False,'clinical_risk_estimated':False,
      'note':'The finite conditional source frame is provided as source identifiers, not reverified local files on this machine.'}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--repo',type=Path,required=True);args=a.parse_args()
    print(json.dumps(run(args.repo),indent=2))
