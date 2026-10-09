# Handoff para o Claude — cartões-resposta (08/10/2026)

## Atualização — integridade do fechamento (fim da tarde de 08/10/2026)

Riscos **1, 3 e 4** abaixo foram resolvidos (nada commitado; suíte: **126 passed**):

- **Risco 1:** `review_page`, `identify_page` e `decide_page` passam por `_transition_page` em `app/data/answer_sheets.py`, que trava lote e página (`with_for_update`), confere a situação dentro da transação e monta a alteração a partir da página travada. Uma revisão chegando depois do lançamento é recusada (`STALE_PAGE`) e a rota mostra o aviso.
- **Risco 3:** `_roster()` em `app/scanner/results.py` compara o público esperado do filtro do lote com os cartões ativos de todos os lotes do simulado. A prévia mostra esperados, com cartão lido, com nota lançada e sem cartão lido (com nomes). Ausentes sem nenhum resultado exigem a confirmação `confirm_missing` no lançamento; não bloqueiam.
- **Risco 4:** `_lock_open_attempt` em `app/data/attempts.py` trava a linha do aluno (a mesma da publicação) e relê a tentativa antes de salvar ou entregar; tentativa fora de "Em andamento" gera `AttemptClosedError` (a entrega redireciona ao resultado; o autosave responde 409). Salvar e corrigir ocorrem numa única transação.
- `SCOPE_KEYS`, `matches_scope`, `student_audience` e `eligible_students` saíram de `app/scanner/routes.py` para `app/data/academic.py` (dono único do público).
- O SQLite dos testes não executa travas de linha: os testes provam a reconferência de estado, não a serialização no PostgreSQL.

**Risco 2** também foi resolvido (suíte: **134 passed**):

- `AttemptAnswer.answer_key` (coluna `respostas.gabarito`, anulável) guarda o gabarito usado; é preenchido em `submit_attempt` e em `publish_results`. `_add_missing_columns()` em `app/database.py` cria a coluna em bancos existentes ao iniciar o app (lista explícita `ADDED_COLUMNS`; `IF NOT EXISTS` no PostgreSQL). **O Supabase ganha a coluna no próximo reinício do servidor**; o processo antigo continua funcionando sem ela.
- `AttemptAnswer.graded_key(current_key)` devolve o gabarito da correção; respostas antigas, sem gabarito gravado, só mostram o que ainda é comprovável (resposta certa = seu próprio gabarito; errada = gabarito atual enquanto ele discordar da resposta; caso contrário, "Gabarito revisado depois da correção").
- A tela de resultado do aluno lista as questões da tentativa (não a composição atual) e mostra o gabarito da correção. `_load_scores_by_student` normaliza pela quantidade de respostas da tentativa.
- O formulário de questão avisa quando já há respostas corrigidas com ela (`graded_answer_count`).
- Enunciado, alternativas e explicação continuam vivos (não versionados).

**Risco 5** também foi resolvido (suíte: **138 passed**):

- `rectify_attempt` em `app/data/attempts.py` corrige o resultado no próprio registro (sem criar tentativa nova) e grava `AttemptCorrection` (tabela `retificacoes`, criada pelo `create_all` no próximo início) com motivo, autor e valores antigos/novos; notifica o aluno (`result_rectified`) só quando a nota muda. Recusa resultados fora de "Resultado disponível"/"Correção pendente".
- `lock_students` é a trava única por aluno, usada por lançamento em papel, entrega/autosave online, correção de questões abertas e retificação.
- Cartão: rota `scanner.page_rectify` (`/lotes/<lote>/paginas/<página>/retificar`) + `rectify_paper_page` em `app/scanner/results.py`; a prévia passa a mostrar a nota atual do resultado.
- Gabarito: `POST /questoes/<id>/recorrigir` (`regrade_question`), para coordenações e T.I.; coordenação da escola limitada aos próprios alunos.
- O CSRF do leitor virou `csrf_token()`/`check_csrf()` em `app/auth/security.py` (chave de sessão `form_csrf`); as demais rotas POST do app continuam sem CSRF, como antes.

Continuam abertos: 6 (validação física), 7 (lotes grandes) e as melhorias de UX.

## Pedido e decisões do usuário

O usuário quer um fluxo de cartões-resposta simples, funcional e compreensível para operadores mais velhos. Só o cartão-resposta interessa; não há fluxo de digitalização do caderno de prova. Ao escanear, o sistema deve destacar branco, rasura/marca duvidosa, marcação múltipla e falhas; permitir conferir e corrigir ao lado da imagem digitalizada, com lupa sobre qualquer área. Branco vale zero e não bloqueia; dúvidas e múltiplas marcações exigem revisão. A nota só é publicada após confirmação explícita. Conflito com tentativa online deve ser decidido por aluno, preservando o histórico.

O último pedido antes deste handoff foi uma avaliação do fluxo e nota atual versus melhoria. **Nenhuma nova implementação após a fase 1 foi solicitada.** Recomendação de avaliação: UX atual aproximadamente **6/10** (Impeccable: 23/40 nas heurísticas de Nielsen), meta **8/10** após fechar integridade e simplificar a fila de revisão, e **9/10** somente depois de validar cartões físicos e corrigir os riscos operacionais. São estimativas, não notas medidas em teste com usuários.

## Estado do repositório

- Workspace: `C:\Users\wyder\Music\at\IFP-System`; branch `main`; HEAD `3bae3fb` no momento deste handoff.
- Há várias modificações **não commitadas** e arquivos novos, de tarefas anteriores e da fase 1. Preserve tudo; não faça reset, checkout ou commit sem pedido do usuário. Verifique `git status --short` antes de editar.
- `docs/HANDOFF.md` é um handoff histórico e está desatualizado: descreve um `main` quebrado que já foi reparado. Use este arquivo para o estado atual.
- Banco real usa configuração em `instance/database.env`. Não leia nem exponha credenciais. Os testes usam SQLite em memória. Nenhuma nota real foi lançada nesta sessão.

## O que a fase 1 já implementou

- Emissão, impressão A4, leitura QR/bolhas, identificação manual de QR ilegível e revisão com cartão digitalizado/lupa já existiam ou foram feitos nas tarefas anteriores desta conversa. Veja `app/scanner/routes.py`, `app/scanner/vision.py`, `app/templates/scanner/` e `app/static/js/scanner-review.js`.
- Nova prévia em `app/templates/scanner/results.html`, acessada pelo lote: mostra nota por aluno, brancos, pendências, duplicatas e tentativas existentes.
- `app/scanner/results.py` calcula a pontuação objetiva, bloqueia páginas em revisão/falha, composição alterada, duplicatas ativas e conflitos não decididos. `publish_results()` grava `AssessmentAttempt`, respostas, histórico no JSON da página e notificação em uma transação. A publicação é explícita; não acontece no upload.
- `app/scanner/routes.py` tem decisões de ignorar/restaurar uma página e manter tentativa anterior ou usar o cartão. `app/data/answer_sheets.py` recalcula o estado do lote e audita essas decisões.
- `docs/SCANNER_CARTOES.md` descreve o fluxo e limitações.
- Última suíte executada: `.venv\Scripts\python.exe -m pytest -q` → **123 passed**. `tests/test_scanner.py` cobre lançamento, branco, duplicatas entre lotes, conflito com tentativa anterior e revisão obrigatória. São testes sintéticos; não provam precisão com papel real.

## Riscos prioritários encontrados na auditoria

1. **Corrida entre revisão e publicação:** `app/scanner/routes.py:477` verifica o estado antes de chamar `review_page`, mas `app/data/answer_sheets.py:244` salva a revisão sem bloquear a página/lote e sem conferir novamente o estado dentro da transação. `publish_results` bloqueia lote/alunos (`app/scanner/results.py:112`), mas a revisão não participa do mesmo protocolo. Dois POSTs simultâneos podem deixar nota publicada e página reaberta/divergente. Corrigir com trava e transição atômica, com teste de concorrência.
2. **Gabarito não congelado:** o cartão guarda ID/número/alternativas (`app/scanner/layout.py:15`), enquanto a pontuação usa `gabarito` vivo (`app/scanner/results.py:70`). Uma edição após a impressão ou depois do lançamento pode fazer a tela do aluno divergir da nota histórica. Versionar ou congelar gabarito e conteúdo relevante; mostrar no resultado a versão usada para corrigir.
3. **Não há fechamento do público esperado:** a prévia confere só as páginas presentes no lote (`app/scanner/results.py:38`). É possível lançar 1 cartão de 4 impressos sem ver os 3 ausentes. Criar um grupo de emissão com alunos esperados e mostrar esperados, recebidos, ausentes, ignorados e lançados. A ausência deve receber decisão explícita antes do fechamento do grupo; permitir envio posterior segundo regra clara.
4. **Tentativa online concorrente:** não existe unicidade de resultado ativo por aluno+simulado (`app/models.py:303`), e o fluxo online em `app/data/attempts.py:17` não usa a mesma trava da publicação em papel. Definir uma política única e impedir resultados ativos duplicados em concorrência.
5. **Sem retificação pós-publicação:** `app/scanner/routes.py:477` impede rever página lançada. Criar correção auditada, com motivo, valor antigo/novo e nova notificação ao aluno, sem apagar o histórico.
6. **Precisão física não medida:** OMR com limiares fixos em `app/scanner/vision.py`; a documentação alerta que os testes usam imagens sintéticas. Validar folhas impressas e digitalizadas em equipamentos reais, canetas, rasuras e resolução diferentes; medir falso positivo/falso negativo antes de notas reais.
7. **Lotes grandes:** até 300 páginas são processadas sincronicamente em uma requisição (`app/scanner/routes.py:285`). Uma falha intermediária preserva páginas, mas o erro do lote bloqueia o lançamento (`app/scanner/results.py:100`). Planejar fila com progresso e retomada/reprocessamento de páginas.

## Melhorias de UX recomendadas após a integridade

- A etapa `index.html` diz “Escolha os alunos”, mas só oferece filtros e um número antes de imprimir. Mostrar a lista de nomes/matrículas do público e pedir conferência do grupo.
- Em `batch.html`, as pendências devem vir antes do botão “Conferir notas e lançar”. Em `results.html`, cada item da lista de pendências deve apontar à página e à ação adequada. Priorizar “Revisar N páginas” e oferecer “Próxima pendência” após salvar; hoje `page_review` volta ao lote.
- Na revisão, mostrar primeiro questões duvidosas/múltiplas, permitir salto direto para cada uma e manter a imagem acessível ao editar no celular. O formulário atual mostra todas as questões; abaixo de 900 px a imagem fica acima do formulário longo (`app/static/css/scanner.css:94`).
- Na confirmação final, resumir em um quadro compacto alunos/notas prontos, cartões ignorados e conflitos resolvidos. Explicar a recuperação ao lado de falhas que não permitem identificação manual.
- Linguagem mais orientada à ação: “Pronto”, “Conferir marca”, “Identificar aluno”, “Cartão repetido”, “Publicado”; deixar “confiança” técnica em detalhes, para não parecer nota.

## Avaliação e ambiente visual

- Revisão Impeccable da interface: 23/40 nas dez heurísticas; pontos fortes são quatro etapas claras, revisão lado a lado com lupa e lançamento explícito. A página inicial foi vista no navegador; lote, revisão e resultados foram avaliados principalmente pelo código.
- O detector Impeccable retornou 0 achados em **modo degradado por falta dos parsers HTML/CSS**, então esse zero não é validação visual nem de acessibilidade.
- O navegador local em `http://127.0.0.1:8000` estava rodando um processo Python antigo. Uma tentativa anterior de reiniciar o servidor foi **bloqueada pela revisão automática** (“blocked by policy”); não contorne. A aba `file:///.../results.html` mostra o template Jinja bruto, não a tela renderizada. Na inspeção desta auditoria, a entrada do scanner renderizou, mas um lote existente abriu a página genérica “Algo não funcionou”; causa não diagnosticada e pode envolver o processo antigo. Verifique a versão do servidor e logs antes de concluir que é regressão do código novo.

## Próximo passo sugerido ao Claude

Primeiro confirme com o usuário a fase que ele quer executar; a pergunta em aberto é “o que melhorar e qual nota”. Minha recomendação é começar pela **integridade do fechamento** (corrida revisão/publicação, gabarito versionado e contagem de cartões esperados), depois simplificar a **fila de pendências**. Não publique notas reais nem altere dados do banco de produção para testar. Antes de editar, leia `AGENTS.md` se existir, `git status --short`, os arquivos citados e rode os testes relevantes. Após qualquer correção, execute `.venv\Scripts\python.exe -m pytest -q`.
