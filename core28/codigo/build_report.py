"""Build a readable, portable analytical delivery; no spreadsheet dependency."""
from pathlib import Path
from html import escape as E
from itertools import product
import json, shutil, subprocess, sys, unittest, io, zipfile, re
from analysis_core import *

ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
OUT=ROOT/'outputs/analise_documental_nucleo28_2026-11-11'
PREV=ROOT/'outputs/julgamentos_nucleo28_referencias_modalidades_2026-11-11'
CORE=ROOT/'outputs/extracao_referencias_nucleo28_2026-11-11/base_preservada/NUCLEO_CONGELADO_28.json'
PROTOCOL=ROOT/'outputs/integracao_nucleo28_2026-11-11/plano/PROTOCOLO_NUCLEO_V2_RATIFICADO.json'
RN={REFS[0]:'R0 · histórica tratada',REFS[1]:'ITT · todos randomizados',REFS[2]:'Segurança definida na fonte',REFS[3]:'Janela em tratamento / TEAE'}
CN={COMPS[0]:'Ideação suicida',COMPS[1]:'Tentativa de suicídio',COMPS[2]:'Morte por suicídio'}
MN={MODS[0]:'Eventos adversos',MODS[1]:'Avaliação estruturada',MODS[2]:'Derivação de mortalidade', 'secondary_any_modality':'União secundária'}
SN={'complete':'Completa','unknown':'Desconhecida','bounded_not_complete':'Não completa delimitada','not_applicable':'Não aplicável'}
SC={'WITHHOLD_DERIVED_PROOFS':'Retirada das provas derivadas','NO_MORTALITY_MODALITY':'Sem modalidade de mortalidade','WITHOUT_FOUR_MEMBERSHIP_AMENDMENTS':'Subconjunto sem quatro emendas de entrada',
    'REGISTRY27_ALL_POPULATIONS':'27 registros: todas as populações completas'}
for p in ['SCALE','STEP','SURMOUNT']:
    SC['PROGRAM_'+p]='Somente '+p;SC['LEAVE_OUT_'+p]='Sem '+p

STYLE='''body{font:16px/1.55 system-ui,Segoe UI,sans-serif;color:#18344b;background:#f3f6f8;margin:0}main{max-width:1250px;margin:auto;padding:35px 28px 70px}h1{font-size:32px;line-height:1.2}h2{font-size:24px;margin-top:40px}h3{font-size:19px}p{max-width:1050px}a{color:#075b91}table{width:100%;border-collapse:collapse;background:white;margin:16px 0 28px;font-size:14px}th,td{padding:10px 11px;border:1px solid #ced8df;text-align:left;vertical-align:top}th{background:#173c57;color:white}td.num{text-align:right;font-variant-numeric:tabular-nums}caption{text-align:left;font-weight:bold;padding:8px 0}.box{border-left:5px solid #23876d;padding:15px 20px;background:#e7f3ee;margin:22px 0}.warn{border-color:#b67d25;background:#fff1d9}.muted{color:#526575;font-size:14px}details{padding:12px;background:white;border:1px solid #d5dfe5;margin:10px 0}summary{font-weight:650;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}code{overflow-wrap:anywhere}.nav{display:flex;gap:16px;flex-wrap:wrap}input,select{font:inherit;padding:9px;margin-right:8px}.matrix{font-size:13px}.matrix td,.matrix th{padding:8px}.C{color:#06664c;background:#e3f3ec}.U{color:#866100;background:#fff4d8}.N{color:#7c3330;background:#f8e7e5}small{font-size:12px}.scroll{overflow-x:auto}section{scroll-margin-top:20px}@media print{body{background:white}main{padding:0}details{break-inside:avoid}a{color:inherit}nav,input,select{display:none}thead{display:table-header-group}}'''

def readable_prose(body):
    # Format visible prose only; never alter HTML attributes, anchors or IDs.
    pieces=re.split('(<[^>]+>)',body)
    for i in range(0,len(pieces),2):
        saved=[]
        def protect(m):
            saved.append(m.group());return 'PROTECTEDTOKEN'+chr(0xE000+len(saved)-1)
        t=re.sub(r'\b[a-f0-9]{40,64}\b|\bNCT\d+(?::[A-Z0-9_]+)?|\bCJ28-[a-f0-9]+|\b(?:R0|B3|B2|B1|GPI1|GPI2|T2D|HFpEF)\b',protect,pieces[i])
        t=re.sub(r'(?<=[A-Za-zÀ-ÿ])(?=\d)', ' ',t)
        t=re.sub(r'(?<=\d)(?=[A-Za-zÀ-ÿ])', ' ',t)
        t=re.sub(r'(?<=[,;])(?=[A-Za-zÀ-ÿ])',' ',t)
        t=t.replace('×4','× 4').replace('×3','× 3')
        for j,s in enumerate(saved):t=t.replace('PROTECTEDTOKEN'+chr(0xE000+j),s)
        pieces[i]=t
    return ''.join(pieces)

def html(title,body,script=''):
    body=readable_prose(body)
    return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+E(title)+'</title><style>'+STYLE+'</style></head><body><main>'+body+'</main>'+script+'</body></html>'

def pct(v):return '—' if v is None else f'{100*v:.2f}%'.replace('.',',')
def bounds(x):return 'Não aplicável' if not x['N'] else f"{pct(x['identification_lower'])}–{pct(x['identification_upper'])}"
def rowsort(x):return (REFS.index(x['reference_id']),COMPS.index(x['component']),MODS.index(x['modality']) if x['modality'] in MODS else 3)

def table(rows,reference=False,level='primary'):
    headers=(['Referência'] if reference else [])+['Componente','Modalidade','N','Direta','Depende de derivação','Não completa','Desconhecida','Intervalo condicional']
    s='<div class="scroll"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'
    for x in sorted(rows,key=rowsort):
        if not x['N']:continue
        v=([RN[x['reference_id']]] if reference else [])+[CN[x['component']],MN[x['modality']],x['N'],x['complete_direct_supported'],x['complete_requires_derivation'],x['bounded_not_complete'],x['unknown'],bounds(x)]
        s+='<tr>'+''.join('<td>'+E(str(z))+'</td>' for z in v)+'</tr>'
    return s+'</tbody></table></div>'

def compare_independent(d):
    a=load(WORK/'auditoria_independente/INDEPENDENT_COUNTS.json')
    assert a['input_sha256']==SOURCE_HASH
    pairs=[('primary_modality_tables','by_reference_component_modality'),('secondary_union_tables','secondary_union')]
    checked=0
    def check(x,y):
        nonlocal checked
        for ours,theirs in [('N','N'),('complete','C'),('complete_direct_supported','C_direct'),('complete_requires_derivation','C_derived'),('unknown','U'),('bounded_not_complete','B'),('not_applicable','NA')]:
            assert x[ours]==y[theirs],(ours,x,y)
        if x['N']:
            assert x['lower_numerator']==y['lower_numerator'] and x['upper_numerator']==y['upper_numerator']
        checked+=1
    for ours,theirs in pairs:
        for x in d[ours]:
            yy=[y for y in a[theirs] if y['reference']==x['reference_id'] and y['component']==x['component'] and (ours!='primary_modality_tables' or y['modality']==x['modality'])]
            assert len(yy)==1;check(x,yy[0])
    for x in d['primary_modality_tables']:
        y=next(y for y in a['positive_membership'] if (y['reference'],y['component'],y['modality'])==(x['reference_id'],x['component'],x['modality']))
        assert set(x['complete_ids'])=={u['unit_id'] for u in y['complete_units']}
    other_cells={(r['unit_id'],r['reference_id'],r['component']):r for r in a['secondary_union_cells']}
    for x in d['secondary_population_states']:
        y=other_cells[x['unit_id'],x['reference_id'],x['component']]
        assert x['state']==y['analytical_state']
    b=load(WORK/'auditoria_independente/INDEPENDENT_SENSITIVITIES.json')['results']
    sm={'WITHHOLD_DERIVED_PROOFS':'direct_witness_only','NO_MORTALITY_MODALITY':'exclude_allcause_modality','WITHOUT_FOUR_MEMBERSHIP_AMENDMENTS':'omit_population_amendments','REGISTRY27_ALL_POPULATIONS':'registry_target_all_nested_populations_complete'}
    for x in d['sensitivity_tables']:
        if x['scenario_id'] in sm and x['analysis_level']=='union_secondary':
            y=next(y for y in b[sm[x['scenario_id']]] if y['reference']==x['reference_id'] and y['component']==x['component'])
            check(x,y)
    return dict(passed=True,summary_rows_checked=checked,input_hash=SOURCE_HASH,kind='Separate AI computational implementation; not independent human source validation',
        primary_and_secondary_counts_agree=True,positive_membership_and_secondary_states_agree=True,four_sensitivity_union_families_agree=True)

def evidence_index(rows):
    s='<h1>Julgamentos congelados que sustentam os cálculos</h1><p><a href="../COMECE_AQUI.html">Voltar ao relatório</a></p><p>Transcrição dos campos da base congelada, sem nova classificação. Fontes editoriais completas não são redistribuídas. O catálogo e a extração de evidências estão nesta pasta em JSON.</p>'
    for r in rows:
        if r['analytical_state']=='not_applicable':continue
        s+='<details id="'+r['judgment_id']+'"><summary>'+E(r['trial']+' · '+r['unit_id']+' · '+RN[r['reference_id']]+' · '+CN[r['component']]+' · '+MN[r['modality']]+' · '+SN[r['analytical_state']])+'</summary>'
        for k,label in [('target_population','População'),('target_window','Janela'),('source_scoped_status','Tipo de prova / situação'),('rationale','Justificativa'),('arm_facts','Fatos por braço'),('derivation','Operação de derivação'),('unresolved_dimensions','Dimensões desconhecidas'),('evidence_ids','Identificadores de evidência'),('evidence_locators','Localizadores'),('reuse_disposition','Reaproveitamento')]:
            val=r.get(k)
            if val not in [None,[],{},'']:
                s+='<p><b>'+label+':</b></p><pre>'+E(val if isinstance(val,str) else json.dumps(val,ensure_ascii=False,indent=2))+'</pre>'
        s+='</details>'
    return html('Índice de provas congeladas',s,'<script>function openHash(){const x=document.getElementById(location.hash.slice(1));if(x){x.open=true;x.scrollIntoView()}}window.addEventListener("hashchange",openHash);openHash()</script>')

def render(d,core,rows):
    p=d['primary_modality_tables'];u=d['secondary_union_tables'];st=d['sensitivity_tables']
    b='<p class="muted">11 de novembro de 2026 · análise documental do núcleo congelado · versão1</p><h1>28 populações, quatro referências e modalidades separadas</h1>'
    b+='<nav class="nav"><a href="#principal">Resultados principais</a><a href="#sens">Sensibilidades</a><a href="MATRIZ_POR_ENSAIO.html">Matriz por ensaio</a><a href="RESULTADOS_COMPLETOS.json">Resultados JSON</a><a href="METODOS_E_RESULTADOS_EN.txt">Texto científico em inglês</a><a href="PACOTE_ANALISE_NUCLEO28.zip">Pacote reproduzível</a></nav>'
    b+='<div class="box warn"><b>A interpretação mudou com o núcleo verificável.</b> Não há posições aplicáveis classificadas como “não completas” delimitadas: as restantes são desconhecidas. Todos os limites superiores condicionais são100%. Isso impede estimar uma proporção demonstrada de ensaios não reconstruíveis. A morte apresenta várias reconstruções confirmadas, sobretudo derivadas; ideação e tentativa têm menos confirmações.</div>'
    b+='<p>São 28 populações randomizadas de 27 registros: 6 SCALE, 15 STEP e 7 SURMOUNT. GPI1 e GPI2 de SURMOUNT-OSA são duas populações independentes. A análise descreve <b>reconstrução documental por braço</b>, não pacientes com eventos, risco de suicídio ou eficácia dos medicamentos.</p>'
    b+='<h2>Método e alcance</h2><p>Aplicaram-se os julgamentos congelados às fontes cumulativas arquivadas até11/11/2026. Os cortes de registro e conclusão primária19/10/2026 não demonstram disponibilidade histórica de todas essas fontes. O núcleo foi delimitado retrospectivamente, após conhecimento dos resultados anteriores, e não é um censo exaustivo. Esta rodada é técnica e assistida por IA, com reaproveitamento das decisões em seu escopo; não representa uma nova avaliação humana independente.</p>'
    b+='<p>C=completas, U=desconhecidas, B=não completas delimitadas e N=C+U+B. O intervalo de identificação condicional é <b>[C/N;(C+U)/N]</b>. Todos os desconhecidos permanecem no denominador. Os extremos são cenários lógicos; não imputam resultados à base. Pressupõem corretas as classificações conhecidas, a composição e a compatibilidade do alvo; não cobrem erros de seleção/classificação ou ensaios fora do núcleo. Não são intervalos de confiança.</p>'
    b+='<p>“Direta” e “depende de derivação” se referem ao testemunho documental congelado, não ao estado clínico de uma pessoa. Um zero de mortalidade global ou lista exaustiva de causas pode sustentar derivação; um termo ausente não vira zero. Uma prova positiva em qualquer modalidade não garante equivalência clínica entre modalidades.</p>'
    b+='<section id="principal"><h2>Resultados principais por modalidade</h2><p>As quatro referências são apresentadas separadamente. Em cada tabela, N=28. As combinações de mortalidade derivada com ideação/tentativa são inaplicáveis e não entram no denominador. “Não completa” é0 em todas as linhas aplicáveis.</p>'
    for ref in REFS:
        b+='<h3>'+RN[ref]+'</h3>'+table([x for x in p if x['reference_id']==ref])
    b+='</section><p>O único ensaio com reconstrução estruturada confirmada foi SCALE Maintenance, para ideação e tentativa na população de segurança e janela definida pela fonte. Isso não completa automaticamente a referência histórica, a ITT, a janela TEAE ou morte. As demais posições estruturadas permanecem desconhecidas; ausência de prova confirmada não equivale a ausência de avaliação.</p>'
    b+='<h2>União das modalidades — análise secundária</h2><p>Cada população conta uma vez por referência/componente. Basta uma modalidade completa; na ausência dela, qualquer desconhecido mantém a união desconhecida. “Direta” indica pelo menos uma prova direta; “depende de derivação” significa que todas as provas completas disponíveis nessa união são derivadas. As modalidades podem sobrepor-se e não são somadas.</p>'+table(u,True)
    b+='<details><summary>Conferência das sobreposições</summary><table><tr><th>Referência</th><th>Componente</th><th>Soma das posições completas por modalidade</th><th>Populações completas na união</th></tr>'
    for x in d['overlap_audit']:
        b+='<tr>'+''.join('<td>'+E(str(z))+'</td>' for z in [RN[x['reference_id']],CN[x['component']],x['modality_memberships'],x['complete_union']])+'</tr>'
    b+='</table><p>Por exemplo, na referência histórica,14 provas por eventos adversos e18 por mortalidade produzem20 populações completas para morte, por sobreposição. Não representam32 ensaios nem32 mortes.</p></details>'
    b+='<section id="sens"><h2>Análises de sensibilidade</h2><p>A base original não foi recodificada. Os resultados abaixo são cenários analíticos ou subconjuntos. As tabelas por modalidade de todos os cenários estão no detalhamento; a união continua secundária.</p>'
    for sid in ['WITHHOLD_DERIVED_PROOFS','NO_MORTALITY_MODALITY','WITHOUT_FOUR_MEMBERSHIP_AMENDMENTS','REGISTRY27_ALL_POPULATIONS']:
        desc=next(s for s in d['sensitivity_definitions'] if s['scenario_id']==sid)
        b+='<h3>'+SC[sid]+'</h3><p>'+E(desc['definition'])+'</p>'+table([x for x in st if x['scenario_id']==sid and x['analysis_level']=='union_secondary'],True)
        if sid=='WITHHOLD_DERIVED_PROOFS':
            b+='<p>Esta retirada testa a dependência das provas derivadas, sem afirmar que inexiste prova direta não examinada. Na união histórica de morte,19 das20 confirmações passam a desconhecidas no cenário; uma permanece por prova direta. Na ITT e na janela em tratamento, nenhuma confirmação de morte permanece após essa retirada.</p>'
        if sid=='WITHOUT_FOUR_MEMBERSHIP_AMENDMENTS':
            b+='<p>Retirados somente neste cenário: SCALE Maintenance, STEP12, SURMOUNT-3 e SURMOUNT-CN. As decisões de inclusão ratificadas continuam válidas; o subconjunto não reproduz uma análise prospectiva nem declara esses ensaios inelegíveis.</p>'
    b+='<details><summary>Estratos por programa e retirada de um programa por vez</summary><p>Comparações de composição, sem testes de diferença, causalidade ou ranking dos medicamentos.</p>'
    for sid in [s['scenario_id'] for s in d['sensitivity_definitions'] if s['scenario_id'].startswith(('PROGRAM_','LEAVE_OUT_'))]:
        b+='<h3>'+SC[sid]+'</h3>'+table([x for x in st if x['scenario_id']==sid and x['analysis_level']=='union_secondary'],True)
    b+='</details><p><a href="SENSIBILIDADES_POR_MODALIDADE.html">Todas as sensibilidades por referência e modalidade</a> · <a href="TRANSICOES_REFERENCIAS.html">Transições pareadas entre referências</a></p></section>'
    b+='<h2>Conclusão sustentada e limitações</h2><p>O núcleo permite confirmar reconstruções por braço em parte dos ensaios, mais frequentemente para morte e com dependência importante de derivações. As confirmações de ideação e tentativa são escassas e as de avaliação estruturada concentram-se em um alvo específico. O conjunto restante é desconhecido; não foi demonstrado que a maioria do núcleo seja não reconstruível.</p>'
    b+='<p>Diferenças entre referências refletem população, atribuição dos braços, janela e fonte do testemunho. A janela TEAE pode incluir períodos após suspensão; a população de segurança pode ser por tratamento recebido e conter exclusões. Não há uma duração universal nem uma comparação causal entre definições. Intensidade de exame, disponibilidade documental, decisões históricas e participação técnica de IA limitam o resultado. A integridade computacional não prova a correção de toda interpretação documental ou a captação de todos os eventos clínicos.</p>'
    b+='<p>As análises anteriores182/159 permanecem históricas e não foram sobrescritas. Seus percentuais não são diretamente comparáveis a estes28, porque composição e exame mudaram. Nenhuma camada históricaA–B3 foi recalculada, e não houve metanálise clínica, nova avaliação GRADE ou concordância humana calculada.</p>'
    b+='<h2>Validação e próximos passos</h2><p>Os 28 testes sintéticos passaram; as 48 linhas principais/secundárias (incluindo 8 combinações inaplicáveis) e 48 linhas de quatro sensibilidades secundárias coincidiram com implementação computacional separada. A identidade das populações positivas e os estados das uniões também coincidiram. Os hashes congelados, a grade de 1.008 posições e as partições de denominador foram conferidos. A execução portátil reproduziu integralmente os resultados. Isso é conferência computacional por IA, não validação humana independente.</p><p><b>Nenhum novo caso foi aberto para os revisores.</b> O próximo passo é incorporar estas tabelas e a interpretação revisada a um novo manuscrito centrado no núcleo verificável, preservando a trilha histórica. A aprovação de versões antigas não foi automaticamente estendida a esse futuro texto.</p>'
    b+='<nav class="nav"><a href="plano/PLANO_ANALITICO.json">Plano operacional</a><a href="VALIDACAO_FINAL.json">Validação</a><a href="lote_unico/ESTADO_LOTE.json">Lote de revisão</a><a href="README.txt">Como reproduzir</a><a href="evidencias/INDICE_JULGAMENTOS.html">Provas dos julgamentos</a></nav><p class="muted">SHA-256 da base: <code>'+SOURCE_HASH+'</code></p>'
    (OUT/'COMECE_AQUI.html').write_text(html('Análise documental dos28 ensaios',b),encoding='utf-8')
    b='<h1>Sensibilidades por modalidade</h1><p><a href="COMECE_AQUI.html">Relatório</a></p><p>Sem união entre modalidades; referências separadas. As contagens de positivos que dependem de derivação continuam distintas.</p>'
    for sd in d['sensitivity_definitions']:
        sid=sd['scenario_id'];b+='<details><summary>'+SC[sid]+'</summary><p>'+E(sd['definition'])+'</p>'+table([x for x in st if x['scenario_id']==sid and x['analysis_level']=='modality_primary'],True)+'</details>'
    (OUT/'SENSIBILIDADES_POR_MODALIDADE.html').write_text(html('Sensibilidades por modalidade',b),encoding='utf-8')
    b='<h1>Transições entre referências</h1><p><a href="COMECE_AQUI.html">Relatório</a></p><p>As tabelas pareiam as mesmas28 populações. Não representam mudança clínica, efeito causal da referência ou nova leitura independente. Toda transição conta populações, não pacientes.</p>'
    for t in d['reference_transitions']:
        b+='<details><summary>'+E(RN[t['reference_from']]+' → '+RN[t['reference_to']]+' · '+CN[t['component']]+' · '+MN[t['modality']])+'</summary><table><tr><th>Estado anterior</th><th>Estado na referência comparada</th><th>n</th><th>Populações</th></tr>'
        for c in t['cells']:
            if c['n']:b+='<tr>'+''.join('<td>'+E(str(z))+'</td>' for z in [SN[c['from_state']],SN[c['to_state']],c['n'],', '.join(c['unit_ids'])])+'</tr>'
        b+='</table></details>'
    (OUT/'TRANSICOES_REFERENCIAS.html').write_text(html('Transições entre referências',b),encoding='utf-8')
    lookup={key(r):r for r in rows};b='<h1>Matriz por população e referência</h1><p><a href="COMECE_AQUI.html">Relatório</a></p><p>D = completa direta; R = completa derivada; ? = desconhecida; 0 = não completa delimitada. Clique para abrir o julgamento e seus localizadores. R não significa risco. As quatro referências não são quatro avaliações humanas.</p><input id="q" placeholder="Filtrar ensaio ou registro" aria-label="Filtrar ensaio"><div class="scroll"><table class="matrix"><thead><tr><th>População</th><th>Referência</th>'
    pairs=[(c,m) for c in COMPS for m in MODS if applicable(c,m)]
    b+=''.join('<th>'+E(CN[c])+'<br>'+E(MN[m])+'</th>' for c,m in pairs)+'</tr></thead><tbody>'
    for x in core:
        for ref in REFS:
            b+='<tr class="data"><td>'+E(x['trial']+' · '+x['unit_id'])+'</td><td>'+E(RN[ref])+'</td>'
            for c,m in pairs:
                r=lookup[x['unit_id'],ref,c,m];s=r['analytical_state'];label='D' if r['source_scoped_status']=='complete_direct' else 'R' if s=='complete' else '?' if s=='unknown' else '0'
                b+='<td class="'+('C' if s=='complete' else 'U' if s=='unknown' else 'N')+'"><a href="evidencias/INDICE_JULGAMENTOS.html#'+r['judgment_id']+'">'+label+'</a></td>'
            b+='</tr>'
    b+='</tbody></table></div>'
    (OUT/'MATRIZ_POR_ENSAIO.html').write_text(html('Matriz dos28 ensaios',b,'<script>document.getElementById("q").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tr.data").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script>'),encoding='utf-8')
    (OUT/'evidencias/INDICE_JULGAMENTOS.html').write_text(evidence_index(rows),encoding='utf-8')

def english(d):
    text='''DRAFT METHODS AND RESULTS FOR THE NEW CORE — 11 NOVEMBER 2026
This is an analytical writing aid, not an approved/submitted manuscript. No previous author approval is extended automatically.

METHODS
We conducted a retrospective documentary audit of an explicitly enumerated, non-exhaustive core of28 independently randomized trial populations (27 registry identifiers):6SCALE,15STEP and7SURMOUNT populations. The two SURMOUNT-OSA populations were retained separately. Core amendments were ratified after earlier results were known; this is not a prospectively registered or blinded selection. The source set comprises individually archived versions available to this audit by11November2026. The19October2026 registry-first-posting and primary-completion cutoffs do not establish historical availability of every documentary source.

The frozen analysis file (SHA-2569214d5de3565b49c127c4c414e02edecc88a9f15588112344a573871dbb431f7) contains1,008 positions:28populations ×4references ×3components ×3modalities. All-cause mortality derivation is inapplicable to ideation and attempt, leaving784 applicable positions. The current analysis applies the frozen technical judgments, reusing prior decisions only within their documented scope. This does not constitute a new independent human assessment. Technical AI assistance and separate computational cross-checks are distinct from human source validation; exact model/version metadata are unavailable in the execution record.

Primary tables separate each reference (historical treated, intention-to-treat, source-defined safety and source-defined on-treatment/TEAE), component and modality (adverse-event reports, structured suicidality assessments, and all-cause mortality derivation). Original-arm attribution, counting unit, population and source-defined window remain attached to each witness. Safety populations, nominal denominators, actual respondent subsets, randomized assignments and treatment-received assignments are not assumed equivalent. Source-defined TEAE windows can include off-treatment follow-up. A complete reconstruction describes the specified public documentary target, not perfect clinical ascertainment.

We report absolute counts of complete direct, complete derived, bounded not-complete and unknown judgments. With Ccomplete, Uunknown and N=C+U+Bapplicable populations, [C/N,(C+U)/N] is a conditional identification interval. These are not confidence intervals and do not describe clinical suicide risk. Unknowns remain in N; no complete-case or patient-weighted analysis is used. The interval assumes the known judgments, target compatibility and enumerated membership are correct; it does not encompass missed trials or selection/classification errors.

Secondary any-modality unions count a population once: a compatible complete witness is sufficient; absent one, any unknown keeps the union unknown. Direct-supported unions require at least one direct witness; derivation-dependent unions contain only derived complete witnesses. Modalities and their source windows are not thereby treated as clinically equivalent. Sensitivities withdraw recorded derived proofs by making those positions scenario-unknown, omit the mortality modality while retaining within-AE derivations, remove four ratified membership-amendment populations as a24population composition scenario, describe programme strata and leave-one-programme-out sets, and change the denominator to27registry identifiers while requiring every nested population complete. For the registry secondary outcome, modalities are unioned within populations before conjunction across populations. All scenarios preserve original source judgments. Reference transitions are descriptive; no causal, significance, clinical-effect, new human agreement or GRADE analysis was performed.

RESULTS
All784 applicable frozen positions were either complete or unknown; none was a bounded not-complete judgment. Consequently, every applicable identification interval in the main analysis and specified sensitivities had an upper endpoint of100%. This is not evidence that all populations are reconstructible, or that unknown populations are non-reconstructible.

Primary counts below are complete-direct / complete-derived / unknown out of28 (bounded not-complete=0):
'''
    for ref in REFS:
        text+='\n'+ref+'\n'
        for x in sorted(d['primary_modality_tables'],key=rowsort):
            if x['reference_id']==ref and x['N']:
                text+=f"{x['component']} | {x['modality']}: {x['complete_direct_supported']} / {x['complete_requires_derivation']} / {x['unknown']}; conditional interval {x['identification_lower']*100:.2f}%–100%.\n"
    text+='''
Structured assessments supported complete ideation and attempt reconstruction only for SCALE Maintenance under the source-defined safety reference. No structured death reconstruction was confirmed; other structured targets remain unknown rather than proven non-reconstructible.

Secondary unions (complete/unknown) were3/25,5/23 and20/8 for ideation, attempt and death under the historical treated reference;2/26,5/23 and13/15 under ITT;5/23,6/22 and22/6 under source-defined safety; and5/23,6/22 and21/7 under on-treatment. For historical death,14AE and18mortality complete positions overlapped, yielding20 unique populations, not32.

With recorded derived proofs withheld, the historical secondary confirmations became3,2and1for ideation, attempt and death; the remaining populations were scenario-unknown. Direct-supported death confirmations were0for ITT,1for source-defined safety and0for on-treatment. Removing only mortality derivation left14historical death confirmations through AE, demonstrating that AE reports themselves can require derivation. The24population scenario yielded2,3and17historical confirmations; the27registry all-populations scenario yielded3,5and19. Neither scenario changes the ratified membership or pools clinical observations.

INTERPRETATION
The enumerated core supports confirmed original-arm documentary reconstructions for several populations, particularly death through derivation. Confirmations of ideation and attempt are less frequent and structured confirmations are limited to a specific population/window. The audit cannot establish that most of this core is non-reconstructible: its unresolved positions are unknown and all upper identification endpoints remain100%. Reference differences reflect source populations, arm attribution, windows, available witnesses and review scope, not causal differences or comparative drug safety. Earlier182/159 analyses remain dated historical comparators and are not directly comparable to this new core. Computational reproduction verifies calculation from the coded file; it does not independently validate all source interpretations.
'''
    # Readability: restore spaces in count-word constructions without altering IDs/hashes.
    import re
    text=text.replace(SOURCE_HASH,'__FROZEN_HASH__')
    text=re.sub(r'(?<=[a-zA-Z:])(?=\d)', ' ', text)
    text=re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', text)
    # Keep exact identifiers/hash compact after prose formatting.
    text=text.replace('__FROZEN_HASH__',SOURCE_HASH)
    text=text.replace('SHA-256'+SOURCE_HASH,'SHA-256 '+SOURCE_HASH)
    text=text.replace('×4','× 4').replace('×3','× 3').replace(',15 STEP',', 15 STEP')
    text=text.replace('Ccomplete','C complete').replace('Uunknown','U unknown').replace('Bapplicable','B applicable')
    return text

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    src=PREV/'JULGAMENTOS_FECHADOS_28_QUATRO_REFERENCIAS.json'
    assert sha(src)==SOURCE_HASH and sha(CORE)==CORE_HASH
    rows=load(src)['records'];core=load(CORE)['records'];d=run(rows,core)
    write(OUT/'RESULTADOS_COMPLETOS.json',d)
    audit=compare_independent(d)
    write(OUT/'auditoria/COMPARACAO_IMPLEMENTACOES.json',audit)
    for p,rel in [(src,'dados/JULGAMENTOS_CONGELADOS.json'),(CORE,'dados/NUCLEO_CONGELADO_28.json'),(PREV/'CONGELAMENTO_TECNICO.json','dados/CONGELAMENTO_ORIGINAL.json'),(PROTOCOL,'plano/PROTOCOLO_RATIFICADO.json'),(WORK/'PLANO_ANALITICO.json','plano/PLANO_ANALITICO.json'),(PREV/'evidencias/CATALOGO_FONTES_VERIFICADAS.json','evidencias/CATALOGO_FONTES_VERIFICADAS.json'),(PREV/'evidencias/EVIDENCIAS_DOS_JULGAMENTOS.json','evidencias/EVIDENCIAS_DOS_JULGAMENTOS.json')]:
        dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    for sub in ['auditoria_independente','auditoria_metodos']:
        for p in (WORK/sub).iterdir():
            if p.is_file():
                dest=OUT/'auditoria'/sub/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    for p in WORK.glob('*.py'):
        dest=OUT/'codigo'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    for p in (PREV/'regras').glob('*.json'):
        dest=OUT/'plano'/p.name;shutil.copyfile(p,dest)
    render(d,core,rows)
    (OUT/'METODOS_E_RESULTADOS_EN.txt').write_text(english(d),encoding='utf-8')
    teststream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(WORK),pattern='test_analysis.py')
    testresult=unittest.TextTestRunner(stream=teststream,verbosity=2).run(suite)
    assert testresult.wasSuccessful()
    (OUT/'auditoria/TESTES_SINTETICOS.txt').write_text(teststream.getvalue(),encoding='utf-8')
    reproduced=WORK/'REPRODUCED_PORTABLE.json'
    proc=subprocess.run([sys.executable,str(OUT/'codigo/run_analysis.py'),'--output',str(reproduced)],capture_output=True,text=True,check=True)
    assert reproduced.read_bytes()==(OUT/'RESULTADOS_COMPLETOS.json').read_bytes()
    for x in d['primary_modality_tables']+d['secondary_union_tables']+d['sensitivity_tables']:
        assert x['complete']+x['unknown']+x['bounded_not_complete']==x['N']
        assert x['complete_direct_supported']+x['complete_requires_derivation']==x['complete']
        if x['N']:assert 0<=x['identification_lower']<=x['identification_upper']<=1
        assert len(x['complete_ids'])==x['complete'] and len(x['unknown_ids'])==x['unknown']
    for t in d['reference_transitions']:assert sum(c['n'] for c in t['cells'])==28
    for o in d['overlap_audit']:assert sum(c['n'] for c in o['mutually_exclusive_patterns'])==o['complete_union']
    hist=ROOT/'outputs/analise_negativos117_2026-11-06/analise/CURRENT_ANALYTICAL_INPUT.json'
    assert sha(hist)==load(PREV/'CONGELAMENTO_TECNICO.json')['historical_input_sha256']
    assert sha(src)==SOURCE_HASH and sha(CORE)==CORE_HASH
    validation=dict(passed=True,synthetic_tests_passed=testresult.testsRun,
        input_hash_verified=True,core_hash_verified=True,grid_records=1008,applicable_positions=784,
        independent_implementation_summary_rows_checked=audit['summary_rows_checked'],
        portable_reproduction_byte_identical=True,all_denominator_partitions_pass=True,
        all_interval_invariants_pass=True,transition_and_overlap_partitions_pass=True,
        frozen_and_historical_inputs_unchanged=True,new_human_cases=0,
        clinical_meta_analysis_performed=False,human_validation_not_inferred=True)
    write(OUT/'VALIDACAO_FINAL.json',validation)
    write(OUT/'lote_unico/ESTADO_LOTE.json',dict(previous_batch_file=str(PREV/'lote_unico/ESTADO_LOTE.json'),
        previous_state=load(PREV/'lote_unico/ESTADO_LOTE.json'),new_cases=[],new_human_votes=0,
        interpretation='Unknowns are preserved dispositions, not newly generated blank human forms.'))
    write(OUT/'STATUS_ATUAL.json',dict(version=d['version'],status='DOCUMENTARY_STATISTICS_AND_SENSITIVITIES_COMPLETE',input_sha256=SOURCE_HASH,
        references=4,trial_populations=28,registry_ids=27,source_ratings_modified=False,
        new_reviewer_cases=0,prior_decisions_reused_within_scope=True,portal_changed=False,public_repository_changed=False,
        future_manuscript_approval_not_inferred=True,next_step='Incorporate the verified core tables and revised interpretation into a new manuscript; retain historical comparator and limitations.'))
    write(OUT/'PROVENIENCIA_IA.json',dict(provider='OpenAI',application='Codex desktop',date='2026-11-11',
        model_version='Exact model/version unavailable in preserved execution metadata; not inferred.',
        activities=['Analysis plan implementation','Statistical code and tests','Separate computational audit','Report interpretation'],
        instructions_location='plano/PLANO_ANALITICO.json',new_independent_human_validation=False,
        author_approval_of_future_manuscript=False))
    (OUT/'README.txt').write_text('''ANÁLISE DOCUMENTAL DOS28 ENSAIOS — 11/11/2026

Abra COMECE_AQUI.html. Os resultados principais mantêm referências e modalidades separadas.
RESULTADOS_COMPLETOS.json contém tabelas, cenários, transições e a rastreabilidade às posições.
METODOS_E_RESULTADOS_EN.txt é um rascunho para a próxima redação, não aprovação autoral.

REPRODUÇÃO PORTÁTIL (Python3.10 ou superior; somente biblioteca padrão)
Na pasta extraída deste pacote:
  python codigo/run_analysis.py --output RESULTADOS_REPRODUZIDOS.json
  python -m unittest discover -s codigo -p test_analysis.py -v
Comparar RESULTADOS_REPRODUZIDOS.json e RESULTADOS_COMPLETOS.json byte a byte ou por SHA-256.
run_analysis.py usa dados/ por padrão, verifica os hashes fixos e não depende do workspace original.
build_report.py é o gerador de integração do workspace original e permanece como proveniência;
não é necessário executá-lo para reproduzir a análise. O script de auditoria separado registra
os caminhos utilizados na conferência original; não substitui o entrypoint portátil.

dados/ contém cópias exatas da base de julgamentos e do núcleo congelados.
plano/ contém o protocolo ratificado e o plano operacional retrospectivo desta rodada.
evidencias/ contém os localizadores/catálogo e índice legível dos julgamentos. PDFs de editoras
não são redistribuídos. Reproduzir cálculos é possível só com o pacote; reexaminar fontes exige
obtê-las pelas referências públicas ou usar os originais locais indicados no catálogo.
auditoria/ contém comparação separada por IA e testes sintéticos, não validação humana externa.
lote_unico/ preserva o histórico do lote; não existem novos casos humanos nesta etapa.

Nenhum desconhecido foi tratado como zero ou excluído do denominador. As derivações retiradas
nas sensibilidades tornam-se desconhecidas no cenário, sem modificar o julgamento original.
Todas as posições aplicáveis são completas ou desconhecidas; os limites superiores são100%.
Não há proporção demonstrada de ensaios não reconstruíveis. As taxas são documentais, não clínicas.
Não foram executados testes de hipótese, IC, metanálise clínica, nova concordância humana ou GRADE.
O núcleo é retrospectivo e não exaustivo; os limites são condicionais à composição e classificação.
As versões históricas182/159, o portal e o repositório público permanecem inalterados.
''',encoding='utf-8')
    manifest=[dict(path=str(p.relative_to(OUT)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['MANIFESTO_SHA256.json','PACOTE_ANALISE_NUCLEO28.zip'] and '__pycache__' not in p.parts]
    write(OUT/'MANIFESTO_SHA256.json',dict(files=manifest,excludes=['MANIFESTO_SHA256.json','PACOTE_ANALISE_NUCLEO28.zip','__pycache__']))
    with zipfile.ZipFile(OUT/'PACOTE_ANALISE_NUCLEO28.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and p.name!='PACOTE_ANALISE_NUCLEO28.zip' and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(OUT)))
    with zipfile.ZipFile(OUT/'PACOTE_ANALISE_NUCLEO28.zip','r') as z:
        assert z.testzip() is None
    print(json.dumps(validation,ensure_ascii=False))
    print(str(OUT/'COMECE_AQUI.html'))

if __name__=='__main__':main()
