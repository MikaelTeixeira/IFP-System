# Scanner de cartões-resposta

## Fluxo

1. Em **Cartões-resposta**, selecione o simulado e aplique os filtros de instituição, série/ano, ano letivo e turma. Série/ano é o nível escolar (por exemplo, 9º ano); ano letivo é o período (por exemplo, 2026).
2. Gere os cartões desse público. O QR identifica um cartão emitido, estudante e simulado por um identificador assinado; não contém CPF.
3. Imprima em A4, escala 100%, sem cabeçalhos/rodapés do navegador. Preserve os quatro quadrados nos cantos. Preencha inteiramente uma bolha por questão com caneta azul ou preta.
4. Digitalize preferencialmente em 300 dpi, com uma folha por página, sem cortar os cantos. Envie PDF, PNG ou JPEG, até 50 MB e 300 páginas por lote.
5. Confira as páginas sinalizadas. Passe o mouse sobre o cartão para ampliar qualquer área com a lupa, ou toque na imagem no celular. Pelo teclado, use as setas para mover a lupa e Escape para fechá-la. Corrija as respostas ao lado. Questões em branco são sinalizadas e podem ser corrigidas, mas não bloqueiam o lote. Marcas duvidosas, rasuras suspeitas, múltiplas respostas e problemas de alinhamento exigem conferência. A conferência manual exige confirmação e registra responsável, data e respostas anteriores.
6. Se o QR não for lido, tente digitalizar novamente. Quando os quatro marcadores forem localizados, é possível identificar o aluno manualmente: compare nome, matrícula e título impressos; selecione o aluno; digite a matrícula e confirme a identidade. O vínculo exige um único cartão emitido e ainda não utilizado para aquele aluno no simulado. Depois, confira todas as respostas. QR decodificado mas inválido, imagem desalinhada e identidade incerta exigem nova digitalização.
7. No lote, abra **Conferir notas e lançar**. A prévia mostra acertos e questões em branco de cada cartão. Revise páginas pendentes; desconsidere, com motivo e confirmação, páginas inválidas ou duplicadas. É possível restaurar uma página desconsiderada antes do lançamento. Uma duplicata ativa em outro lote também bloqueia o lançamento. A seção **Público esperado** compara os alunos do filtro do lote com os cartões lidos em todos os lotes do simulado e lista quem ainda não tem cartão lido (indicando quem já tem resultado por outro meio). Se algum aluno do público ficar sem nota, o lançamento pede uma confirmação a mais; ausências não bloqueiam, e o cartão pode ser enviado depois em outro lote.
8. Se o aluno já tiver uma tentativa, escolha por aluno: manter o resultado anterior e desconsiderar o cartão, ou usar o cartão e arquivar a tentativa anterior. A escolha e o histórico ficam registrados. Quando todas as pendências estiverem resolvidas, confirme o lançamento. Só então a nota aparece para o aluno e ele recebe uma notificação. O lote inteiro é lançado em uma transação: se houver erro, nenhum dos resultados novos é salvo.
9. Conferência, identificação manual, decisões e lançamento seguem o mesmo protocolo: travam o lote (e a página) no banco e conferem de novo a situação da página dentro da transação. Uma conferência enviada depois que a página foi lançada ou alterada é recusada com aviso para atualizar a tela, em vez de sobrescrever o resultado. A entrega online trava o mesmo registro do aluno que o lançamento usa; uma tentativa arquivada pelo cartão não pode mais ser entregue.

## Retificação de notas publicadas

Uma nota publicada é corrigida no próprio resultado, nunca apagada. Cada retificação grava em `retificacoes` o tipo, o motivo, quem a fez e, por questão, a resposta, o gabarito e o acerto antigos e novos, além da nota anterior e da nova. Quando a nota muda, o aluno recebe um aviso com o motivo, e a tela de resultado lista as revisões. Retificar fica com quem lança notas: coordenações e T.I.; a coordenação da escola só altera notas de alunos da própria escola.

- **Leitura errada no cartão:** na prévia do lote, a página lançada tem **Retificar resultado**. A tela é a mesma da conferência, com a lupa, e pede motivo e confirmação. A página guarda a leitura anterior em `analise.rectifications`; o registro do lançamento (`result_launch`) não muda.
- **Gabarito corrigido:** a página da questão mostra quantos resultados publicados usam outro gabarito e permite recorrigi-los com o gabarito atual, com motivo e confirmação, numa única transação. Só a questão recorrigida muda.

Resultados arquivados ("Substituída") e tentativas em andamento não podem ser retificados. Retificação, lançamento, entrega online e correção de questões abertas usam a mesma trava por aluno.

## Precisão e limites

- A impressão e a leitura usam as mesmas coordenadas físicas. O modelo `A4-20-v2` suporta até 20 questões objetivas, em dois blocos, com duas a cinco alternativas consecutivas de A a E. Questões discursivas não geram bolhas; sua posição na numeração é preservada.
- Reimprima cartões do modelo anterior. A geometria antiga não é compatível com a leitura nova.
- O algoritmo identifica o QR, corrige orientação e perspectiva pelos quatro marcadores e compensa variações de iluminação. Só analisa o interior das bolhas; letras ficam fora delas.
- Bolhas deslocadas, marcas fracas, rasuras suspeitas, múltiplas respostas, baixa resolução e desfoque são encaminhados para conferência. Respostas claramente em branco ficam sem ponto e são destacadas para consulta opcional. A confiança exibida é uma heurística da leitura, não uma probabilidade calibrada nem garantia de acerto.
- Cada cartão preserva a composição das questões e seu público no momento da emissão. Mudanças posteriores na composição bloqueiam o lançamento e exigem um cartão atualizado. A correção usa o gabarito vigente no momento do lançamento (a prévia já mostra a nota com ele), e cada resposta guarda o gabarito com que foi corrigida (`respostas.gabarito`). Editar a questão depois não altera notas publicadas: o aluno continua vendo o gabarito e as questões da correção, e os relatórios usam o número de questões da própria tentativa. O formulário da questão avisa quando ela já tem respostas corrigidas. Para aplicar o gabarito novo a notas já publicadas, use a recorreção na página da questão (veja **Retificação**).
- Cartões de outro simulado/público e duplicatas no mesmo lote são separados. Reenvios em outros lotes exigem conferência. Coordenadores escolares não acessam lotes de outras instituições.
- O PDF é renderizado uma página por vez. O processamento ainda é síncrono; lotes grandes podem levar tempo. A resolução máxima de entrada é limitada a 40 milhões de pixels por imagem.
- O lançamento é manual e só aceita cartões de questões objetivas em banco persistente. Questões discursivas não são corrigidas por cartão e impedem a publicação deste modo. A nota e as respostas usadas são guardadas no histórico do cartão. Resultados já lançados não voltam para a conferência; uma leitura errada é corrigida pela retificação.

## Operação

Instale `requirements.txt` e configure um banco para uso persistente. Sem banco, cartões e lotes são demonstrativos, ficam na memória do processo e não sobrevivem à reinicialização. As imagens ficam no diretório configurado em `SCAN_ROOT` (por padrão, `instance/scans`). A inicialização acrescenta as colunas opcionais dos novos recursos às tabelas do scanner já existentes, sem remover registros.

Use um `SECRET_KEY` estável e privado em produção: mudar a chave invalida as assinaturas dos cartões já emitidos. O banco e as imagens precisam entrar juntos na política de backup e retenção.

## Validação

Execute `.venv\Scripts\python.exe -m pytest`. `tests/test_scanner.py` testa coordenadas extraídas da impressão SVG, rotações, perspectiva, margens, sombras, baixa resolução, desfoque, marcas ambíguas, duplicatas, PDFs multipágina, filtros e isolamento de acesso, histórico de conferência, prévia, conflitos, lançamento e modo demonstrativo.

Antes de uso em provas reais, valide com cartões impressos e digitalizados nos equipamentos da escola, diferentes canetas e preenchimentos. Os testes sintéticos não medem uma taxa de acerto em folhas físicas; ajuste dos limiares deve ser acompanhado por amostras reais e novas regressões.
