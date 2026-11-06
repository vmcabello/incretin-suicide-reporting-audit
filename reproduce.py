"""Verify complete historical replay, then the current author-approved NEG117 results."""
from pathlib import Path
import argparse,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    subprocess.run([sys.executable,'-B',str(ROOT/'reproduce_v1_5_0.py'),'--check'],check=True)
    with tempfile.TemporaryDirectory(prefix='release_v160_') as td:
        subprocess.run([sys.executable,'-B',str(ROOT/'negative117/reproduce_neg117.py'),'--repository',str(ROOT),'--out',td],check=True)
        if a.out:
            a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes((Path(td)/'CURRENT_RESULTS.json').read_bytes())
    print(json.dumps({'release':'v1.6.0','historical_replay':'PASS','current_NEG117_replay':'PASS','clinical_effect_analysis':False,'journal_submission_sent':False}))
if __name__=='__main__':main()
