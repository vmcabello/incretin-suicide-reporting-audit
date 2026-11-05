"""Administrative inventory of existing documentary-reason annotations.

No source is reread, no clinical estimate is calculated, and no current
scientific classification is changed. Recorded tags are not a prevalence
estimate of reporting defects or causes of non-reconstructibility in trials.
"""
import collections
import csv
import gzip
import io
import hashlib
import html
import importlib.util
import json
import pathlib

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repository',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent.parent)
parser.add_argument('--annotations',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent/'REASON_ANNOTATION_INPUT_5096.jsonl.gz')
parser.add_argument('--out',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parent)
args=parser.parse_args()
REPO=args.repository.resolve()
ROOT=REPO
OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
ANNOTATION=args.annotations.resolve()
def relative_path(p):
    try:return str(pathlib.Path(p).relative_to(REPO)).replace('\\','/')
    except ValueError:return pathlib.Path(p).name
INPUTS=[]
KEY=('unit_id','component','stage','modality','reference_id','window_id')
DIMENSIONS=('numerator','denominator','window','subpopulation','counting_unit','source_access')

def load(p):
    p=pathlib.Path(p);b=p.read_bytes()
    INPUTS.append({'path':relative_path(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    return {'records':[json.loads(line) for line in gzip.decompress(b).decode('utf-8-sig').splitlines() if line.strip()]} if p.suffix=='.gz' else json.loads(b.decode('utf-8-sig'))

def save(n,d):
    (OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def tsv(n,rows,columns):
    with (OUT/n).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore',delimiter='\t',lineterminator='\n');w.writeheader()
        for r in rows:w.writerow({k:(json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else r.get(k,'')) for k in columns})

def key(r):return tuple(r[k] for k in KEY)

current=load(REPO/'current_input/documental_entrada_reconciliada.json')
annotations=load(ANNOTATION)
corrections=load(REPO/'reconciliation/TECHNICAL_CORRECTIONS426.json')
population=load(REPO/'input_snapshot/dados/populacoes_final.json')
gapledger=load(REPO/'input_snapshot/dados/lacunas_cumulativas.json')
source_results=load(REPO/'input_snapshot/resultados/RESULTADO_DOCUMENTAL_FINAL.json')
current_results=load(REPO/'current_analysis/RESULTS_BY_MODALITY.json')
step5=load(REPO/'reconciliation/STEP5.json')
groupa=load(REPO/'reconciliation/group_a.json')
legacy_script=REPO/'input_snapshot/codigo/analise_final.py'
spec=importlib.util.spec_from_file_location('unchanged_documentary_classifier',legacy_script)
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
INPUTS.append({'path':str(legacy_script.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(legacy_script.read_bytes()).hexdigest(),'bytes':legacy_script.stat().st_size})
bykey={key(r):r for r in current['assessments']}
annby={key(r['assessment_key']):r for r in annotations['records']}
assert len(bykey)==len(annby)==5096 and set(bykey)==set(annby)
pop={p['unit_id']:p['designed_eligibility_stratum'] for p in population['records']}
corrby={key(r):r for r in corrections['positions']}
old_effective={key(r):r['effective_modality_indicator'] for r in source_results['effective_position_indicators']}
events=[]

# These are labels for existing codes, not newly assigned scientific reasons.
labels={
 'NO_COMPONENT_OUTPUT_IN_EXAMINED_SCOPE':'No component output recorded in the named examined scope',
 'DO_NOT_INFER_STRUCTURED_ASSESSMENT':'Structured assessment use must not be inferred; NOT evidence of non-use',
 'OBSERVATION_COVERAGE_NOT_ESTABLISHED':'Observation coverage not established',
 'REPORTING_THRESHOLD':'Reporting threshold recorded',
 'POOLED_OUTPUT_NOT_UNIT_ATTRIBUTABLE':'Pooled output not attributable to the target unit',
 'REQUIRED_PRIMARY_SOURCE_NOT_OBTAINED':'Required primary source not obtained',
 'REQUIRED_SUPPLEMENT_NOT_OBTAINED':'Required supplement not obtained',
 'SOURCE_AVAILABLE_NOT_YET_ASSESSED':'Source available but not yet assessed',
 'RESPONDENT_SUBSET':'Respondent subset recorded',
 'DENOMINATOR_IDENTITY_NOT_ESTABLISHED':'Denominator identity not established',
 'EXTENSION_AGGREGATE':'Extension aggregate recorded',
 'RESTRICTED_TIME_WINDOW':'Restricted time window recorded',
 'SERIOUS_EVENT_ROW_ONLY':'Serious-event row only',
 'DIFFERENT_ASSESSMENT_CONSTRUCT':'Different assessment construct recorded',
 'CONTENT_CONFLICT':'Content conflict recorded',
 'DERIVED_RECEIPT_ONLY':'Derived receipt only',
}
ledger=[]
for k,r in bykey.items():
    a=annby[k];v=legacy.indicator([r]);assert old_effective[k]==v
    status={1:'complete',0:'not_complete_in_examined_scope',None:'unknown'}[v]
    dimcodes={d:a['dimensions'][d]['reason_subcode'] for d in DIMENSIONS}
    gates={d:x.get('finding') for d,x in a['additional_scope_gates'].items()}
    coded=a['coexisting_mechanisms']
    # Positive code signals are copied; a missing signal is not an absent mechanism.
    signals={}
    for code in coded:signals['mechanism:'+code]=labels.get(code,code.replace('_',' ').capitalize())
    for dimension,code in dimcodes.items():signals['dimension:'+dimension+':'+code]='Recorded '+dimension+' dimension: '+code
    for gate,state in gates.items():signals['gate:'+gate+':'+str(state)]='Recorded '+gate+' gate: '+str(state)
    if r.get('cumulative_unresolved_gap_ids'):signals['current_access:cumulative_unresolved_gap']='Current pertinent cumulative access gap'
    if r.get('unobtained_relevant_source_ids'):signals['current_access:unobtained_relevant_source_ids']='Current explicitly listed unobtained relevant source IDs'
    if r.get('unexamined_relevant_source_ids'):signals['current_access:unexamined_relevant_source_ids']='Current explicitly listed unexamined relevant source IDs'
    source_access={s['access_status'] for s in a['source_inventory']}
    for state in source_access:signals['source_inventory_access:'+state]='Recorded annotation source-inventory access: '+state
    item={**dict(zip(KEY,k)),
          'position_id':'POS-'+hashlib.sha256('|'.join(k).encode()).hexdigest()[:20],
          'current_source_scoped_status':r['status'],'current_effective_classification':status,
          'population_stratum':pop[r['unit_id']],
          'historical_annotation_classification':a['existing_classification'],
          'recorded_coexisting_mechanisms':coded,'recorded_dimension_reason_subcodes':dimcodes,
          'recorded_additional_scope_gates':gates,'recorded_signal_ids':sorted(signals),
          'coding_scope':a['coding_scope'],
          'provenance_limits':a['provenance_limits'],
          'annotation_record_locator':ANNOTATION.name+'#row['+str(len(ledger))+']',
          'current_assessment_evidence_refs':r.get('assessment_evidence_refs',[]),
          'current_cumulative_gap_ids':r.get('cumulative_unresolved_gap_ids',[]),
          'current_unobtained_relevant_source_ids':r.get('unobtained_relevant_source_ids',[]),
          'current_unexamined_relevant_source_ids':r.get('unexamined_relevant_source_ids',[]),
          'new_scientific_reason_assigned':False,'not_an_independent_observation':True,
          'current426_dimension_reason_subcodes':corrby[k].get('dimension_reason_subcodes') if k in corrby else None,
          'current426_subcodes_are_not_merged_as_new_human_adjudication':True}
    ledger.append(item)
    for code,label in signals.items():
        events.append({'signal_id':code,'signal_label':label,'unit_id':r['unit_id'],'component':r['component'],
                       'stage':r['stage'],'modality':r['modality'],'status':status,'population_stratum':pop[r['unit_id']],
                       'assessment_key':k})

ledger_bytes=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in ledger).encode('utf-8')
compressed=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=compressed,mtime=0) as stream:
    stream.write(ledger_bytes)
(OUT/'POSITION_REASON_LEDGER_5096.jsonl.gz').write_bytes(compressed.getvalue())

scope_filters={
 'all5096_recorded_positions':lambda x:True,
 'operational182_B3_recorded_positions':lambda x:x['stage']=='B3',
 'posthoc159_B3_recorded_positions':lambda x:x['stage']=='B3' and x['population_stratum']=='entire_population_eligible_by_entry_criteria',
 'posthoc159_all_layers_recorded_positions':lambda x:x['population_stratum']=='entire_population_eligible_by_entry_criteria',
}
counts=[]
for scope,include in scope_filters.items():
    members=[x for x in ledger if include(x)];selected=[x for x in events if include(x)]
    allcodes=sorted({x['signal_id'] for x in events})
    for code in allcodes:
        hit=[x for x in selected if x['signal_id']==code]
        for status in ['all_positions','complete','unknown','not_complete_in_examined_scope']:
            denominator=[x for x in members if status=='all_positions' or x['current_effective_classification']==status]
            h=[x for x in hit if status=='all_positions' or x['status']==status]
            counts.append({'scope':scope,'status_group':status,'signal_id':code,
                           'signal_label':next((x['signal_label'] for x in events if x['signal_id']==code),code),
                           'positions_in_administrative_frame':len(denominator),
                           'positions_with_recorded_signal':len(h),
                           'distinct_unit_identifiers_with_recorded_signal':len({x['unit_id'] for x in h}),
                           'not_recorded_as_positive_is_not_absent':True,
                           'trial_prevalence_or_causal_attribution_not_estimated':True})
save('RECORDED_SIGNAL_COUNTS.json',{'schema':'recorded-documentary-signal-inventory-v1','date':'2026-11-04','counts':counts,'descriptive_scope':'Counts of retained coded annotations and access-ledger bindings only, not frequencies of true mechanisms in trial populations or exhaustive public reporting inventories.','multi_reason_rows_cannot_be_summed':True,'no_trial_percentages_computed':True})
tsv('RECORDED_SIGNAL_COUNTS.tsv',counts,['scope','status_group','signal_id','signal_label','positions_in_administrative_frame','positions_with_recorded_signal','distinct_unit_identifiers_with_recorded_signal'])

breakdowns=[]
for grouping in ['stage','component','modality']:
    for level in sorted({x[grouping] for x in events}):
        for code in sorted({x['signal_id'] for x in events}):
            for status in ['complete','unknown','not_complete_in_examined_scope']:
                hits=[x for x in events if x[grouping]==level and x['signal_id']==code and x['status']==status]
                if hits:breakdowns.append({'grouping':grouping,'level':level,'status_group':status,'signal_id':code,'recorded_positions':len(hits),'distinct_unit_identifiers':len({x['unit_id'] for x in hits})})
tsv('RECORDED_SIGNALS_BY_LAYER_COMPONENT_MODALITY.tsv',breakdowns,['grouping','level','status_group','signal_id','recorded_positions','distinct_unit_identifiers'])

dimension_counts=[]
for batch,rs,extract in [
 ('historical_instrument5096',annotations['records'],lambda x,d:x['dimensions'][d]['reason_subcode']),
 ('technical426_existing_reconsolidation',corrections['positions'],lambda x,d:x['dimension_reason_subcodes'][d])]:
    for dimension in DIMENSIONS:
        c=collections.Counter(extract(x,dimension) for x in rs)
        for code,n in sorted(c.items()):dimension_counts.append({'batch':batch,'dimension':dimension,'reason_subcode':code,'recorded_positions':n,'batch_positions':len(rs),'independent_human_validation_not_established':True})
save('DIMENSION_SUBCODE_COUNTS.json',{'records':dimension_counts,'batches_not_independent_or_additive':True,'technical426_does_not_replace_historical_instrument_or_create_new_labels':True})
tsv('DIMENSION_SUBCODE_COUNTS.tsv',dimension_counts,['batch','dimension','reason_subcode','recorded_positions','batch_positions'])

explicit=[]
for record in annotations['records']:
    for d in DIMENSIONS:
        z=record['dimensions'][d]
        if z['reason_subcode']=='DOCUMENTED_INCOMPATIBILITY':
            rr=bykey[key(record['assessment_key'])]
            explicit.append({'assessment_key':record['assessment_key'],'dimension':d,'reason_subcode':z['reason_subcode'],
                             'retained_source_scope_statement':z.get('scope_observed_in_source'),
                             'retained_evidence':z.get('evidence',[]),'current_effective_classification':{1:'complete',0:'not_complete_in_examined_scope',None:'unknown'}[legacy.indicator([rr])],
                             'does_not_revalidate_or_generalize_this_code':True})
save('EXPLICIT_INCOMPATIBILITY_EVIDENCE_INDEX.json',{'records':explicit,'source_scope_only':True,'new_human_reading_claimed':False})

frame=collections.Counter(x['current_effective_classification'] for x in ledger)
coverage={
 'schema':'partial-recorded-reason-coverage-audit-v1','positions':len(ledger),'current_status_partition':dict(frame),
 'annotation_rows_explicitly_allowing_corpus_reason_frequencies':sum(x['coding_scope'].get('can_feed_corpus_frequencies') is True for x in ledger),
 'annotation_rows_explicitly_allowing_corpus_access_frequencies':sum(x['coding_scope'].get('can_feed_corpus_access_frequencies') is True for x in ledger),
 'annotation_rows_explicitly_allowing_examined_content_frequencies':sum(x['coding_scope'].get('can_feed_examined_content_frequencies') is True for x in ledger),
 'coding_scope_level_counts':dict(collections.Counter(x['coding_scope']['level'] for x in ledger)),
 'current_cumulative_access_gap_positions':sum(bool(x['current_cumulative_gap_ids']) for x in ledger),
 'current_explicit_unobtained_source_list_positions':sum(bool(x['current_unobtained_relevant_source_ids']) for x in ledger),
 'current_explicit_unexamined_source_list_positions':sum(bool(x['current_unexamined_relevant_source_ids']) for x in ledger),
 'confirmed_instrument_nonuse':'Not estimable: there is no dedicated validated non-use code in this retained annotation schema. DO_NOT_INFER_STRUCTURED_ASSESSMENT is not evidence of non-use.',
 'between_arm_aggregation':'Not separately estimable from a standardized code. POOLED_OUTPUT_NOT_UNIT_ATTRIBUTABLE records attribution problems; it must not be relabelled automatically as between-arm aggregation.',
 'no_signal_not_absence':'No recorded positive signal may mean unexamined, unspecified, stale or inapplicable documentation; it is not a negative scientific finding.',
 'classification_vs_reason':'Current cumulative status is linked separately from historical source-scoped reason annotations; coexisting limitations can occur even where another valid witness completes the reference.',
 'units_of_count':'A position is unit × component × source layer × modality × fixed reference/window. Positions repeat units and source information; distinct unit IDs are descriptive identifiers, not independent observations.',
 'coverage_verdict':'Valid partial administrative/code inventory. Insufficient for prevalence of causes of non-reconstruction across trials or for adjudicating whether a reason is modifiable by an alternative estimand.',
 'human_validation':'No new human review, independent agreement or primary re-extraction was performed.'}
save('COVERAGE_AND_INFERENCE_LIMITS.json',coverage)

feasibility=[
 {'unit_id':'NCT01144338:CANDIDATE_BLOCK','study':'EXSCEL','alternative':'ITT / reported classified suicide deaths',
  'retained_arm_data':{'randomized_ITT_denominators':[7356,7396],'deaths_classified_as_suicide':[0,1],'deaths_unknown_cause':[110,142],'registry_as_treated_SAE_denominators':[7344,7372]},
  'evidence_basis':'Retained source-scoped EXSCEL rationale and TechnicalCorrections426; Table S4 / own registry distinction already documented.',
  'feasibility':'Potential pilot candidate for reporting the explicitly classified cause-of-death category under ITT. Not complete ascertainment of all true suicide deaths and not interchangeable with treated-as-randomized reference.',
  'required_before_quantitative_sensitivity':'Verify exact source version, observation window, allocation convention and treatment of unclassified causes independently; then lock the alternative documentary outcome definition.',
  'new_estimate_computed':False},
 {'unit_id':'NCT03693430:CANDIDATE_BLOCK','study':'STEP 5','alternative':'Adverse-event safety population versus structured-assessment window',
  'retained_arm_data':step5['direct_counts_per_component'],
  'evidence_basis':'reconciliation/STEP5.json; source-specific eTable8 and footnote, existing technical reconciliation only.',
  'feasibility':'AE proof is already compatible with the retained safety specification; it is not a new alternative-reference sensitivity. Structured scales require respondent Ns and a104-week rather than111-week window.',
  'required_before_quantitative_sensitivity':'Extract structured-assessment person-level counting rule, relevant respondent Ns by arm, visit windows and overlap. AE zeros cannot be transferred to structured scales.',
  'new_estimate_computed':False},
 {'unit_id':'NCT01169779:CANDIDATE_BLOCK','study':'GetGoal-M-Asia','alternative':'Randomized versus exposed safety population / known vital-status follow-up',
  'retained_arm_data':{'exposed_safety':next(u['arms'] for u in groupa['units'] if u['unit_id']=='NCT01169779:CANDIDATE_BLOCK'),'randomized_placebo_N':195},
  'evidence_basis':'reconciliation/group_a.json; preserved own primary article Table1/Methods and limitations.',
  'feasibility':'The recorded safety Ns196/194 and randomized placebo N195 establish that reference conventions differ. Zero reported all-cause deaths does not certify complete follow-up of all randomized participants.',
  'required_before_quantitative_sensitivity':'Verify untreated/randomized participant outcome, allocation/receipt convention, exact window and follow-up completeness before ITT or vital-status claim.',
  'new_estimate_computed':False},
 {'unit_id':'NCT03548935:CANDIDATE_BLOCK','study':'STEP 1','alternative':'On-treatment or structured-assessment schedule',
  'retained_arm_data':None,
  'evidence_basis':'Recorded DOCUMENTED_INCOMPATIBILITY window annotation:7-week dose-gap convention and structured schedule68weeks versus initial follow-up75weeks.',
  'feasibility':'A positive window incompatibility is documented, but the retained reason records alone do not supply a complete alternative arm-specific dataset.',
  'required_before_quantitative_sensitivity':'Extract arm-specific numerators, exposed/randomized/respondent denominators, start/stop/rescue rules and post-withdrawal observations; do not turn a schedule into observed follow-up.',
  'new_estimate_computed':False},
 {'unit_id':'NCT02229396:CANDIDATE_BLOCK','study':'DURATION 8','alternative':'Initial phase versus104-week extension aggregate',
  'retained_arm_data':None,
  'evidence_basis':'Recorded window incompatibility and EXTENSION_AGGREGATE tag:28initial weeks plus24and52extension weeks.',
  'feasibility':'Cumulative extension aggregate cannot isolate the initial reference without additional period-specific data.',
  'required_before_quantitative_sensitivity':'Independently extract period-specific arms, exposed Ns and participant/event counts; preserve extension and original phase as different references.',
  'new_estimate_computed':False},
]
save('ALTERNATIVE_REFERENCE_PILOT_FEASIBILITY.json',{'records':feasibility,'pilot_selection_not_prespecified':'Illustrative feasibility assessment requested after the results were known; no representative sample or numerical sensitivity is claimed.','new_clinical_analysis':False,'new_primary_reextraction':False,'source_scoped_counts_not_promoted_to_complete_reference':True})

# Candidate table for the supplement: absolute annotation counts, not trial rates.
codes=['mechanism:NO_COMPONENT_OUTPUT_IN_EXAMINED_SCOPE','mechanism:DO_NOT_INFER_STRUCTURED_ASSESSMENT',
       'dimension:denominator:DOCUMENTED_INCOMPATIBILITY','dimension:window:DOCUMENTED_INCOMPATIBILITY',
       'dimension:subpopulation:DOCUMENTED_INCOMPATIBILITY','mechanism:POOLED_OUTPUT_NOT_UNIT_ATTRIBUTABLE',
       'mechanism:RESTRICTED_TIME_WINDOW','mechanism:EXTENSION_AGGREGATE','mechanism:REPORTING_THRESHOLD',
       'mechanism:SERIOUS_EVENT_ROW_ONLY','current_access:cumulative_unresolved_gap',
       'dimension:source_access:SOURCE_NOT_OBTAINED','dimension:source_access:SOURCE_NOT_EXAMINED']
table=[]
for code in codes:
    scope='posthoc159_B3_recorded_positions'
    def get(status):
        return next((x for x in counts if x['scope']==scope and x['signal_id']==code and x['status_group']==status),None)
    allr=get('all_positions')
    table.append({'recorded_signal':next((x['signal_label'] for x in counts if x['signal_id']==code),'Explicit source-not-examined code (none recorded)' if code=='dimension:source_access:SOURCE_NOT_EXAMINED' else code),
                  'signal_id':code,'recorded_positions_all5096':next((x['positions_with_recorded_signal'] for x in counts if x['scope']=='all5096_recorded_positions' and x['signal_id']==code and x['status_group']=='all_positions'),0),
                  'recorded_positions_primary_B3':allr['positions_with_recorded_signal'] if allr else 0,
                  'complete':get('complete')['positions_with_recorded_signal'] if get('complete') else 0,
                  'unknown':get('unknown')['positions_with_recorded_signal'] if get('unknown') else 0,
                  'not_complete':get('not_complete_in_examined_scope')['positions_with_recorded_signal'] if get('not_complete_in_examined_scope') else 0,
                  'not_recorded_does_not_mean_absent':True})
save('TABLE_S8_CANDIDATE_ADMINISTRATIVE_SIGNAL_INVENTORY.json',{'caption':'Partial inventory of recorded documentary signals; no trial-level prevalence is estimated','rows':table,
 'note':'Counts refer to coded positions, not independent trials or demonstrated causes. Several signals may coexist and source information repeats across components, modalities and cumulative layers. The primary-B3 frame contains1113positions (159×7) and the full frame5096positions (182×28); these are administrative frames, not estimators of mechanism prevalence. All historical annotation rows explicitly disallow corpus-frequency inference. Zero means no positive code in this field, not proof that an instrument was used or that the barrier was absent. The non-inference code for structured assessment must never be read as confirmed instrument non-use. Current cumulative access-gap bindings are shown separately from historical reason annotations.'})
tsv('TABLE_S8_CANDIDATE_ADMINISTRATIVE_SIGNAL_INVENTORY.tsv',table,['recorded_signal','recorded_positions_all5096','recorded_positions_primary_B3','complete','unknown','not_complete'])

body='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Recorded documentary signals: coverage-limited inventory</title><style>body{font:15px/1.55 Arial;margin:32px;color:#1e293b}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cbd5e1;padding:9px;text-align:left;vertical-align:top}th{background:#edf2f7}.note{padding:16px;background:#fff5d9}li{margin:9px}</style><h1>Recorded documentary signals: partial administrative inventory</h1><p class="note"><strong>These counts do not estimate the prevalence of reporting defects or causes of non-reconstruction in trials.</strong> All 5,096 historical annotation rows expressly prohibit corpus-frequency inference. Existing positive codes can be counted as recorded observations, with their scope and uncertainty preserved. No new source reading, scientific classification or clinical estimate is claimed.</p><h2>Candidate supplementary table</h2><p>Primary-B3 frame: 1,113 positions (159 units × 7 component/modality cells). Full historical frame: 5,096 positions (182 units × 28 cells). Rows overlap and cannot be summed.</p><table><thead><tr><th>Recorded signal</th><th>All 5,096 positions</th><th>Primary-B3 positions</th><th>Complete</th><th>Unknown</th><th>Not complete</th></tr></thead><tbody>'''
for x in table:
    body+='<tr>'+''.join('<td>'+html.escape(str(x[k]))+'</td>' for k in ['recorded_signal','recorded_positions_all5096','recorded_positions_primary_B3','complete','unknown','not_complete'])+'</tr>'
body+='</tbody></table><p>Zero means no positive code in the retained field; it is not evidence that a mechanism is absent. Instrument non-use and between-arm aggregation are not separately estimable from these standardized records. Structured-assessment non-inference is shown to prevent its misinterpretation as non-use.</p><h2>Files and scope</h2><ul>'
for n,label in [('POSITION_REASON_LEDGER_5096.jsonl.gz','Position-level coded ledger and provenance'),('RECORDED_SIGNAL_COUNTS.tsv','All recorded counts by analysis scope and status'),('DIMENSION_SUBCODE_COUNTS.tsv','Six dimensions in the historical 5,096 and technical 426 batches'),('RECORDED_SIGNALS_BY_LAYER_COMPONENT_MODALITY.tsv','Breakdown by cumulative layer, component and modality'),('EXPLICIT_INCOMPATIBILITY_EVIDENCE_INDEX.json','Existing positive incompatibility codes and retained evidence'),('COVERAGE_AND_INFERENCE_LIMITS.json','Coverage and inference limitations'),('ALTERNATIVE_REFERENCE_PILOT_FEASIBILITY.json','Feasibility of five alternative-reference pilot cases')]:
    body+='<li><a href="'+n+'">'+label+'</a></li>'
body+='</ul><h2>Interpretation</h2><p>This is a partial inventory of what prior annotations recorded. Their directed and heterogeneous coverage cannot tell how much of the observed result is caused by the chosen reference rather than by public-reporting limitations. An independently coded source-based sample using explicit alternative populations and windows is needed for that question. The five feasibility cases are illustrative, post-hoc candidates; no numerical sensitivity was fitted.</p></html>'
(OUT/'COMECE_AQUI.html').write_text(body,encoding='utf-8',newline='\n')

checks={'5096_unique_positions_and_annotation_join':len(ledger)==len({key(x) for x in ledger})==5096,
        'current_status_partition_matches_frozen_classifications':dict(frame)=={'complete':57,'unknown':1009,'not_complete_in_examined_scope':4030},
        'all_historical_corpus_frequency_permissions_false':coverage['annotation_rows_explicitly_allowing_corpus_reason_frequencies']==0,
        'current426_keys_subset_existing':set(corrby)<=set(bykey),
        'each_candidate_table_status_partition_matches_count':all(x['complete']+x['unknown']+x['not_complete']==x['recorded_positions_primary_B3'] for x in table),
        'no_new_classification_value':all(old_effective[key(x)]==legacy.indicator([bykey[key(x)]]) for x in ledger),
        'no_new_clinical_estimate':all(x['new_estimate_computed'] is False for x in feasibility)}
assert all(checks.values()),checks
save('QA_RECORDED_REASONS.json',{'checks':checks,'all_passed':True,'scientific_validity_not_established_by_computational_checks':True})
save('INPUT_MANIFEST.json',{'inputs':INPUTS,'originals_modified':False,'existing_repository_analysis_or_input_files_modified':False,'scientific_classification_values_changed':False,'new_human_judgments':False})
print(json.dumps({'coverage':coverage,'candidate_table':table,'qa':checks},ensure_ascii=False,indent=2))
