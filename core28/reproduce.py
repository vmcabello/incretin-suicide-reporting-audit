"""Verify and replay current CORE28 data; Python standard library only."""
from pathlib import Path
from hashlib import sha256
import argparse,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent
def archived_serialization(produced,expected):
    # The frozen Windows JSON uses CRLF. Restore that byte convention on POSIX;
    # every other byte, including all numerical values and keys, must match.
    clean=produced.replace(b'\r\n',b'\n')
    if clean!=expected.replace(b'\r\n',b'\n'):raise SystemExit('CORE28 result content differs')
    serialized=clean.replace(b'\n',b'\r\n') if b'\r\n' in expected else clean
    if serialized!=expected:raise SystemExit('CORE28 archive serialization differs')
    return serialized
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    manifest=json.loads((ROOT/'ESM2_MANIFEST.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        file=ROOT/entry['path']
        if not file.is_file() or sha256(file.read_bytes()).hexdigest()!=entry['sha256']:raise SystemExit('Integrity mismatch: '+entry['path'])
    with tempfile.TemporaryDirectory(prefix='core28_replay_') as td:
        produced=Path(td)/'results.json'
        subprocess.run([sys.executable,'-B',str(ROOT/'codigo/run_analysis.py'),'--output',str(produced)],check=True)
        archival_bytes=archived_serialization(produced.read_bytes(),(ROOT/'RESULTADOS_COMPLETOS.json').read_bytes())
        produced.write_bytes(archival_bytes)
        if a.out:
            a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(produced.read_bytes())
    subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'codigo'),'-p','test_analysis.py','-v'],check=True)
    print(json.dumps({'release':'v2.0.0','manifest_files':len(manifest['files']),'populations':28,'registry_ids':27,'exact_frozen_results_reproduced':True,'archive_line_endings_restored_if_needed':True,'new_ratings_generated':False,'clinical_effect_analysis':False}))
if __name__=='__main__':main()
