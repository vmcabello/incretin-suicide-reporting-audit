"""Verify release integrity and reproduce the published documentary results."""
from pathlib import Path
import argparse,gzip,hashlib,json,subprocess,sys,tempfile
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
    subprocess.run([sys.executable,'-B',str(ROOT/'search_trace/validate_marked_subsets.py'),'--root',str(ROOT/'search_trace')],check=True)
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
    print(json.dumps({'integrity_files':len(manifest['files']),'exact_historical_result_reproduction':True,'recorded_reason_outputs_reproduced':len(expected_names),'search_trace_checked':True,'marked_new_identifier_subsets_reproduced':True,'locked_paired_returns_integrated':True,'descriptive_agreement_reproduced':True,'targeted_public_design_109_replayed':True,'positive_only_sensitivity_outputs_reproduced':len(sensitivity_names),'source_linked_109_outputs_reproduced':len(expected_source_names),'large_inputs_regenerated_and_hash_verified':len(omitted),'source_linked_support_files_checked':len(source_manifest['files']),'historical_primary_results_replaced':False,'new_source_linked_current_analysis_added':True,'followup109_is_subset_of_663_not772_independent_positions':True,'full_source_revalidation_completed':False,'clinical_effect_analysis':False}))
if __name__=='__main__':main()
