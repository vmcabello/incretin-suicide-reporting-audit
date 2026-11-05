"""Verify release integrity and reproduce the published documentary results."""
from pathlib import Path
import argparse,gzip,hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        actual=ROOT/row['path']
        if not actual.is_file() or sha(actual)!=row['sha256']:raise SystemExit('Integrity mismatch: '+row['path'])
    subprocess.run([sys.executable,'-B',str(ROOT/'input_snapshot/codigo/analise_final.py'),'--selftest'],check=True)
    with tempfile.TemporaryDirectory(prefix='incretin_audit_') as td:
        out=Path(td)/'RESULTS_BY_MODALITY.json'
        subprocess.run([sys.executable,'-B',str(ROOT/'current_analysis/analysis_by_modality.py'),'--source',str(ROOT/'input_snapshot'),'--data',str(ROOT/'current_input/documental_entrada_reconciliada.json'),'--out',str(out)],check=True)
        expected=ROOT/'current_analysis/RESULTS_BY_MODALITY.json'
        if out.read_bytes()!=expected.read_bytes():raise SystemExit('Results differ from the versioned expected output')
        if a.out:
            a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(out.read_bytes())
    with tempfile.TemporaryDirectory(prefix='reason_inventory_') as td:
        generated=Path(td)
        subprocess.run([sys.executable,'-B',str(ROOT/'reason_inventory/quantify_recorded_reasons.py'),'--repository',str(ROOT),'--out',str(generated)],check=True)
        expected_names=[f.name for f in generated.iterdir() if f.is_file()]
        for name in expected_names:
            actual=(generated/name).read_bytes(); expected=(ROOT/'reason_inventory'/name).read_bytes()
            if name.endswith('.gz'):
                actual=gzip.decompress(actual); expected=gzip.decompress(expected)
            if actual!=expected:
                raise SystemExit('Recorded-reason inventory differs: '+name)
    subprocess.run([sys.executable,'-B',str(ROOT/'search_trace/validate_search_trace.py'),'--root',str(ROOT/'search_trace')],check=True)
    # The immutable v1.4 validator also validates its dated chronology and only
    # recognizes statuses that existed in v1.4. Replay that validator against
    # an explicit historical view, then check the new append-only history below.
    frozen_json=ROOT/'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_V140_FROZEN.json'
    frozen_html=ROOT/'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_V140_FROZEN.html'
    if sha(frozen_json)!='b52a3dfac6b19be52f2fa0b78d73fd9aefa0c5111ae11937a1b3b29b0041ab51' or sha(frozen_html)!='3e148473cba3e372163eb897aa44916d9ceb410a1126d4a3162f41795ad40f93':
        raise SystemExit('Exact frozen v1.4 chronology bytes differ')
    frozen_history=json.loads(frozen_json.read_text(encoding='utf-8'))
    current_history=json.loads((ROOT/'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_EN.json').read_text(encoding='utf-8'))
    if len(frozen_history['events'])!=17 or current_history['events'][:17]!=frozen_history['events']:
        raise SystemExit('The original seventeen chronology events changed')
    prefix_sha=hashlib.sha256(json.dumps(current_history['events'][:17],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if prefix_sha!='1d1d7df451180c647d3c15032efb369fc1501dd97e1ddcb260ccf9104f6c9e33':
        raise SystemExit('Canonical seventeen-event chronology prefix differs')
    appended_statuses=[e['status']for e in current_history['events'][17:]]
    if appended_statuses!=['completed_version_specific_author_conference','corrected_return_received_before_technical_conciliation','technical_conciliation_prepared_not_new_human_review','retrospective_verified_clarification_no_reclassification','prepared_support_v1_5_0_not_published','public_support_release_v1_5_0']:
        raise SystemExit('The current dated chronology additions differ')
    if any(e.get('new_human_votes_created') is True or e.get('new_author_approval_inferred') is True or e.get('journal_submission_sent') is True for e in current_history['events'][17:]):
        raise SystemExit('Chronology falsely creates human votes, approval or submission')
    if current_history['events'][-1]['author_conference_for_new_scientific_version']!='not_established':
        raise SystemExit('Current scientific-version conference status differs')
    with tempfile.TemporaryDirectory(prefix='historical_subset_validation_') as td:
        view=Path(td)
        shutil.copytree(ROOT/'search_trace',view/'search_trace')
        (view/'corpus').mkdir()
        shutil.copyfile(ROOT/'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_V140_FROZEN.json',view/'corpus/PROTOCOL_AMENDMENT_CHRONOLOGY_EN.json')
        subprocess.run([sys.executable,'-B',str(ROOT/'search_trace/validate_marked_subsets.py'),'--root',str(view/'search_trace')],check=True)
    subprocess.run([sys.executable,'-B',str(ROOT/'validation/reproduce_agreement.py'),'--root',str(ROOT/'validation'),'--check'],check=True)
    subprocess.run([sys.executable,'-B',str(ROOT/'linked_review_protocol/validate_public_design.py'),'--repository',str(ROOT)],check=True)
    with tempfile.TemporaryDirectory(prefix='human_positive_sensitivity_') as td:
        generated=Path(td)
        subprocess.run([sys.executable,'-B',str(ROOT/'validation_sensitivity/reassessed_positive_sensitivity.py'),'--repository',str(ROOT),'--out',str(generated)],check=True)
        sensitivity_names=sorted(f.name for f in generated.iterdir() if f.is_file())
        expected_sensitivity_names=sorted(f.name for f in (ROOT/'validation_sensitivity').iterdir() if f.is_file())
        if sensitivity_names!=expected_sensitivity_names:raise SystemExit('Positive-only sensitivity file roster differs')
        for name in sensitivity_names:
            if (generated/name).read_bytes()!=(ROOT/'validation_sensitivity'/name).read_bytes():
                raise SystemExit('Positive-only sensitivity differs: '+name)
    source_review = ROOT/'source_review109'
    source_manifest=json.loads((source_review/'PUBLIC_SUPPORT_MANIFEST.json').read_text(encoding='utf-8'))
    for row in source_manifest['files']:
        if sha(source_review/row['path'])!=row['sha256']:
            raise SystemExit('Source-linked support integrity differs: '+row['path'])
    expected_source_manifest=json.loads((source_review/'REPRODUCTION_MANIFEST.json').read_text(encoding='utf-8'))
    omitted=json.loads((source_review/'OMITTED_REGENERABLE_OUTPUTS.json').read_text(encoding='utf-8'))['files']
    with tempfile.TemporaryDirectory(prefix='source_review109_') as td:
        generated=Path(td)
        subprocess.run([sys.executable,'-B',str(source_review/'integrate_source_review109.py'),
                        '--repository',str(ROOT),
                        '--public-paired',str(source_review/'HUMAN_SOURCE_REVIEW109_PAIRED.json'),
                        '--accepted-new-positives',str(source_review/'ACCEPTANCE_FOUR_POSITIVE_WITNESSES.json'),
                        '--out',str(generated)],check=True)
        expected_source_names=set(expected_source_manifest['files'])|{'REPRODUCTION_MANIFEST.json'}
        if {p.name for p in generated.iterdir() if p.is_file()}!=expected_source_names:
            raise SystemExit('Source-linked generated file roster differs')
        for name,expected_sha in expected_source_manifest['files'].items():
            if sha(generated/name)!=expected_sha:
                raise SystemExit('Source-linked generated output differs: '+name)
            if name in omitted:
                if expected_sha!=omitted[name]:
                    raise SystemExit('Regenerable output hash policy differs: '+name)
            elif (generated/name).read_bytes()!=(source_review/name).read_bytes():
                raise SystemExit('Source-linked distributed bytes differ: '+name)
        if (generated/'REPRODUCTION_MANIFEST.json').read_bytes()!=(source_review/'REPRODUCTION_MANIFEST.json').read_bytes():
            raise SystemExit('Source-linked reproduction manifest differs')
    reconciled = ROOT/'source_review109_reconciled'
    current_manifest=json.loads((reconciled/'PUBLIC_SUPPORT_MANIFEST.json').read_text(encoding='utf-8'))
    for row in current_manifest['files']:
        if sha(reconciled/row['path'])!=row['sha256']:
            raise SystemExit('Corrected-return support integrity differs: '+row['path'])
    current_expected=json.loads((reconciled/'REPRODUCTION_MANIFEST.json').read_text(encoding='utf-8'))
    current_omitted=json.loads((reconciled/'OMITTED_REGENERABLE_OUTPUTS.json').read_text(encoding='utf-8'))['files']
    with tempfile.TemporaryDirectory(prefix='corrected_source_review109_') as td:
        generated=Path(td)
        subprocess.run([sys.executable,'-B',str(reconciled/'reconcile_corrected_source_review109.py'),
                        '--repository',str(ROOT),
                        '--paired',str(reconciled/'MINIMAL_CORRECTED_PAIRED.json'),
                        '--rules',str(reconciled/'TECHNICAL_PROOF_RULES.json'),
                        '--out',str(generated)],check=True)
        current_names=set(current_expected['files'])|{'REPRODUCTION_MANIFEST.json'}
        if {p.name for p in generated.iterdir()if p.is_file()}!=current_names:
            raise SystemExit('Corrected-return generated file roster differs')
        for name,expected_sha in current_expected['files'].items():
            if sha(generated/name)!=expected_sha:
                raise SystemExit('Corrected-return generated output differs: '+name)
            if name in current_omitted:
                if expected_sha!=current_omitted[name]:
                    raise SystemExit('Corrected-return large-input hash policy differs: '+name)
            elif (generated/name).read_bytes()!=(reconciled/name).read_bytes():
                raise SystemExit('Corrected-return distributed bytes differ: '+name)
        if (generated/'REPRODUCTION_MANIFEST.json').read_bytes()!=(reconciled/'REPRODUCTION_MANIFEST.json').read_bytes():
            raise SystemExit('Corrected-return reproduction manifest differs')
    current_summary=json.loads((reconciled/'CURRENT_EDITOR_SUMMARY.json').read_text(encoding='utf-8'))
    current_pair=json.loads((reconciled/'MINIMAL_CORRECTED_PAIRED.json').read_text(encoding='utf-8'))['rows']
    if len(current_pair)!=109 or not any(r['R1']['cumulative_classification']!=r['R2']['cumulative_classification']for r in current_pair):
        raise SystemExit('Corrected divergent raw rating sets were not preserved')
    agree=current_summary['agreement_all109']
    if agree['cumulative_classification']['exact_agreement_positions']!=85 or agree['source_scoped_classification']['exact_agreement_positions']!=79:
        raise SystemExit('Current raw paired-label agreement differs from the corrected return')
    current_check={r['component']:(r['confirmed_total'],r['unknown'])for r in current_summary['current_B3_whole_population_union']}
    if current_check!={'suicidal_ideation':(1,37),'suicide_attempt':(2,33),'suicide_death':(17,39)}:
        raise SystemExit('Current conservative union differs from the independently checked version')
    print(json.dumps({'corrected_source_review109_outputs_reproduced':len(current_names),'current_support_files_checked':len(current_manifest['files']),'large_current_inputs_regenerated_and_hash_verified':len(current_omitted),'current_raw_cumulative_agreement':'85/109','current_raw_source_scoped_agreement':'79/109','AI_technical_dispositions_are_not_human_consensus':True,'source_review109_preserved_as_v1_4_history':True,'current_path':'source_review109_reconciled/'}))
    print(json.dumps({'integrity_files':len(manifest['files']),'exact_historical_result_reproduction':True,'recorded_reason_outputs_reproduced':len(expected_names),'search_trace_checked':True,'marked_new_identifier_subsets_reproduced':True,'locked_paired_returns_integrated':True,'descriptive_agreement_reproduced':True,'targeted_public_design_109_replayed':True,'positive_only_sensitivity_outputs_reproduced':len(sensitivity_names),'source_linked_109_outputs_reproduced':len(expected_source_names),'large_inputs_regenerated_and_hash_verified':len(omitted),'source_linked_support_files_checked':len(source_manifest['files']),'historical_primary_results_replaced':False,'new_source_linked_current_analysis_added':True,'followup109_is_subset_of_663_not772_independent_positions':True,'full_source_revalidation_completed':False,'clinical_effect_analysis':False}))
if __name__=='__main__':main()
