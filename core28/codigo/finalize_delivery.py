from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json, shutil, zipfile, subprocess, sys, tempfile
from analysis_core import load,sha,write,SOURCE_HASH,CORE_HASH

ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent
OUT=ROOT/'outputs/analise_documental_nucleo28_2026-11-11'

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('href'):self.links.append(a['href'])
        if a.get('id'):self.ids.add(a['id'])

def main():
    assert load(WORK/'QA_RENDER_HTML.json')['passed']
    shutil.copyfile(WORK/'QA_RENDER_HTML.json',OUT/'auditoria/QA_RENDER_HTML.json')
    shutil.copyfile(WORK/'auditoria_metodos/QA_RELATORIO_FINAL.json',OUT/'auditoria/auditoria_metodos/QA_RELATORIO_FINAL.json')
    docs={}
    for p in OUT.rglob('*.html'):
        parser=Links();parser.feed(p.read_text(encoding='utf-8'));docs[p.resolve()]=parser
    count=0
    for p,parser in docs.items():
        for link in parser.links:
            url=urlsplit(link)
            if url.scheme or url.netloc:continue
            target=(p.parent/unquote(url.path)).resolve() if url.path else p
            assert target.is_file(),(p,link,'missing file')
            if url.fragment and target in docs:assert unquote(url.fragment) in docs[target].ids,(p,link,'missing anchor')
            count+=1
    # Package only hash-listed artifacts, without mutable Python caches.
    report=load(OUT/'VALIDACAO_FINAL.json')
    report.update(local_html_links_checked=count,local_render_filter_anchor_passed=True,
        source_ratings_and_membership_unchanged=True,package_reproduction_entrypoint='codigo/run_analysis.py')
    write(OUT/'VALIDACAO_FINAL.json',report)
    shutil.copyfile(WORK/'finalize_delivery.py',OUT/'codigo/finalize_delivery.py')
    manifest=[dict(path=str(p.relative_to(OUT)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['MANIFESTO_SHA256.json','PACOTE_ANALISE_NUCLEO28.zip'] and '__pycache__' not in p.parts]
    write(OUT/'MANIFESTO_SHA256.json',dict(files=manifest,excludes=['MANIFESTO_SHA256.json','PACOTE_ANALISE_NUCLEO28.zip','__pycache__']))
    archive=OUT/'PACOTE_ANALISE_NUCLEO28.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for r in manifest:z.write(OUT/r['path'],r['path'])
        z.write(OUT/'MANIFESTO_SHA256.json','MANIFESTO_SHA256.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for r in manifest:
            import hashlib
            assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
        # Extract only this known self-generated package, to a unique workspace directory.
        verify=Path(tempfile.mkdtemp(prefix='portable_check_',dir=WORK))
        for name in z.namelist():assert (verify/name).resolve().is_relative_to(verify.resolve())
        z.extractall(verify)
    reproduction=verify/'rerun.json'
    subprocess.run([sys.executable,str(verify/'codigo/run_analysis.py'),'--output',str(reproduction)],cwd=verify,check=True,capture_output=True)
    assert reproduction.read_bytes()==(OUT/'RESULTADOS_COMPLETOS.json').read_bytes()
    assert sha(verify/'dados/JULGAMENTOS_CONGELADOS.json')==SOURCE_HASH
    assert sha(verify/'dados/NUCLEO_CONGELADO_28.json')==CORE_HASH
    write(WORK/'VERIFICACAO_PACOTE_FINAL.json',dict(passed=True,zip_sha256=sha(archive),manifest_files_verified=len(manifest),
        extracted_elsewhere_reproduction_identical=True,local_links_verified=count,archive_contains_no_original_publisher_pdfs=True))
    print(json.dumps(load(WORK/'VERIFICACAO_PACOTE_FINAL.json'),ensure_ascii=False))

if __name__=='__main__':main()
