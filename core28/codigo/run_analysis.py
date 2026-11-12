"""Portable rerun: python codigo/run_analysis.py --output reproduced.json"""
from pathlib import Path
import argparse
from analysis_core import load,sha,write,run,SOURCE_HASH,CORE_HASH

def main():
    p=argparse.ArgumentParser()
    base=Path(__file__).resolve().parents[1]
    p.add_argument('--input',type=Path,default=base/'dados/JULGAMENTOS_CONGELADOS.json')
    p.add_argument('--core',type=Path,default=base/'dados/NUCLEO_CONGELADO_28.json')
    p.add_argument('--output',type=Path,default=base/'RESULTADOS_REPRODUZIDOS.json')
    args=p.parse_args()
    assert sha(args.input)==SOURCE_HASH,'Frozen judgments hash mismatch'
    assert sha(args.core)==CORE_HASH,'Frozen membership hash mismatch'
    d=run(load(args.input)['records'],load(args.core)['records'])
    write(args.output,d)
    print('OK:28 populations, four references, separate modalities; input hashes verified.')

if __name__=='__main__':main()
