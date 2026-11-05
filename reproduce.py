"""Verify release integrity and reproduce the published documentary results."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,tempfile
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
    print(json.dumps({'integrity_files':len(manifest['files']),'exact_result_reproduction':True,'clinical_effect_analysis':False}))
if __name__=='__main__':main()
