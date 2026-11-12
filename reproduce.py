"""Check preserved historical analyses, then the current 28-population dataset."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    subprocess.run([sys.executable,'-B',str(ROOT/'reproduce_v1_6_1.py'),'--check'],check=True)
    args=[sys.executable,'-B',str(ROOT/'core28/reproduce.py'),'--check']
    if a.out:args.extend(['--out',str(a.out)])
    subprocess.run(args,check=True)
    print(json.dumps({'release':'v2.0.0','historical_replay':'PASS','current_CORE28_replay':'PASS','clinical_effect_analysis':False,'journal_submission_sent_by_release':False}))
if __name__=='__main__':main()
