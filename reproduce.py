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
    subprocess.run([sys.executable,'-B',str(ROOT/'validation/reproduce_agreement.py'),'--root',str(ROOT/'validation'),'--check'],check=True)
    print(json.dumps({'integrity_files':len(manifest['files']),'exact_result_reproduction':True,'recorded_reason_outputs_reproduced':len(expected_names),'search_trace_checked':True,'locked_paired_returns_integrated':True,'descriptive_agreement_reproduced':True,'full_source_revalidation_completed':False,'clinical_effect_analysis':False}))
if __name__=='__main__':main()
