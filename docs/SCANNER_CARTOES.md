# Scanner de cartões-resposta

## Fluxo

1. Em **Cartões-resposta**, selecione o simulado e aplique os filtros de instituição, série/ano, ano letivo e turma. Série/ano é o nível escolar (por exemplo, 9º ano); ano letivo é o período (por exemplo, 2026).
2. Gere os cartões desse público. O QR identifica um cartão emitido, estudante e simulado por um identificador assinado; não contém CPF.
3. Imprima em A4, escala 100%, sem cabeçalhos/rodapés do navegador. Preserve os quatro quadrados nos cantos. Preencha inteiramente uma bolha por questão com caneta azul ou preta.
4. Digitalize preferencialmente em 300 dpi, com uma folha por página, sem cortar os cantos. Envie PDF, PNG ou JPEG, até 50 MB e 300 páginas por lote.
5. Confira as páginas sinalizadas. A tela mostra a imagem com sobreposição da leitura, as ocorrências e as respostas. A conferência manual exige confirmação e registra responsável, data e respostas anteriores.

## Precisão e limites

- A impressão e a leitura usam as mesmas coordenadas físicas. O modelo `A4-20-v2` suporta até 20 questões objetivas, em dois blocos, com duas a cinco alternativas consecutivas de A a E. Questões discursivas não geram bolhas; sua posição na numeração é preservada.
- Reimprima cartões do modelo anterior. A geometria antiga não é compatível com a leitura nova.
- O algoritmo identifica o QR, corrige orientação e perspectiva pelos quatro marcadores e compensa variações de iluminação. Só analisa o interior das bolhas; letras ficam fora delas.
- Bolhas deslocadas, marcas fracas, rasuras, múltiplas respostas, respostas em branco, baixa resolução e desfoque são encaminhados para conferência. A confiança exibida é uma heurística da leitura, não uma probabilidade calibrada nem garantia de acerto.
- Cada cartão preserva a composição das questões e seu público no momento da emissão. Mudanças posteriores no simulado são sinalizadas, sem trocar silenciosamente a ordem das respostas.
- Cartões de outro simulado/público e duplicatas no mesmo lote são separados. Reenvios em outros lotes exigem conferência. Coordenadores escolares não acessam lotes de outras instituições.
- O PDF é renderizado uma página por vez. O processamento ainda é síncrono; lotes grandes podem levar tempo. A resolução máxima de entrada é limitada a 40 milhões de pixels por imagem.
- As respostas são armazenadas para leitura/conferência; **não há lançamento automático de notas** nesta etapa.

## Operação

Instale `requirements.txt` e configure um banco para uso persistente. Sem banco, cartões e lotes são demonstrativos, ficam na memória do processo e não sobrevivem à reinicialização. As imagens ficam no diretório configurado em `SCAN_ROOT` (por padrão, `instance/scans`). A inicialização acrescenta as colunas opcionais dos novos recursos às tabelas do scanner já existentes, sem remover registros.

Use um `SECRET_KEY` estável e privado em produção: mudar a chave invalida as assinaturas dos cartões já emitidos. O banco e as imagens precisam entrar juntos na política de backup e retenção.

## Validação

Execute `.venv\Scripts\python.exe -m pytest`. `tests/test_scanner.py` testa coordenadas extraídas da impressão SVG, rotações, perspectiva, margens, sombras, baixa resolução, desfoque, marcas ambíguas, duplicatas, PDFs multipágina, filtros e isolamento de acesso, histórico de conferência e modo demonstrativo.

Antes de uso em provas reais, valide com cartões impressos e digitalizados nos equipamentos da escola, diferentes canetas e preenchimentos. Os testes sintéticos não medem uma taxa de acerto em folhas físicas; ajuste dos limiares deve ser acompanhado por amostras reais e novas regressões.
