ANÁLISE DOCUMENTAL DOS28 ENSAIOS — 11/11/2026

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
