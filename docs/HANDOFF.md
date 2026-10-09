# Handoff — sessão de 08/10/2026

Documento para o próximo agente continuar o trabalho no Sistema de Avaliações do
Instituto Fabiana Pinto (Flask + Jinja, CSS próprio, JS sem framework). Leia a
seção 1 antes de qualquer outra coisa: o branch atual está quebrado.

---

## 1. Estado atual (CRÍTICO — resolver primeiro)

### O que aconteceu

Todo o trabalho foi feito no branch `wyd` (HEAD `8f67a8f CARTAO`, que contém o
leitor de cartões-resposta). Às 11:18 o **GitHub Desktop** trocou para o `main`
levando as alterações: fez um stash (`c22cde7`, "On wyd: !!GitHub_Desktop<main>"),
trocou para `main` (`8cca7fc`, pai do `CARTAO`) e reaplicou o stash. Houve
conflitos, e o commit `6703194 cartoes respostas` foi feito **com marcadores de
conflito dentro dos arquivos**.

Resultado no `main` (HEAD `6703194`):

- Marcadores `<<<<<<< Updated upstream` / `>>>>>>> Stashed changes` em
  `app/database.py`, `app/models.py`, `app/templates/base.html` e `requirements.txt`.
- Ficaram de fora todos os arquivos do leitor que vieram do commit `CARTAO` e não
  tinham sido alterados: `app/scanner/{__init__,layout,routes,vision}.py`,
  `app/data/answer_sheets.py`, `app/static/js/scanner.js`,
  `app/templates/scanner/{index,batch,review}.html`, `docs/SCANNER_CARTOES.md`,
  `tests/test_scanner.py`, além das linhas do leitor em `app/__init__.py`
  (blueprint), `app/navigation.py` (menu), `app/data/notifications.py`,
  `app/config.py`, `app/templates/macros/icons.html` (ícone `scanner`) e `tests/test_app.py`.
- O app **não inicia** a partir do `main` (SyntaxError em `app/database.py`); 78 testes falham.
- O servidor que está no ar ainda funciona só porque subiu antes da troca; a rota
  `/cartoes-resposta/` já retorna 500 (template `scanner/index.html` sumiu). **Se o
  servidor reiniciar antes do reparo, ele não volta.**

### Backup criado

`backup-antes-da-troca-main` → `c22cde7`. É o estado completo de antes da troca
(wyd + todo o trabalho desta sessão), que passava nos **116 testes**. O `main`
difere dele **somente** nesses 21 arquivos; nada mais se perdeu.

### Reparo (o usuário precisa rodar ou autorizar)

Restaurar os 21 arquivos foi **bloqueado pelo classificador de permissões**
(sobrescrita de arquivos locais). Não contorne. O comando entregue ao usuário foi:

```bash
git checkout backup-antes-da-troca-main -- $(git diff --name-only backup-antes-da-troca-main HEAD)
```

Depois do reparo:

```bash
.venv/Scripts/python.exe -m pytest -q          # esperado: 116 passed
git grep -n -E "^(<<<<<<<|>>>>>>>)" -- .         # esperado: nada
```

Em seguida, reiniciar o servidor (seção 2) e deixar o usuário decidir o commit.
**Não faça commit nem push sem pedido explícito.**

---

## 2. Ambiente e execução

- Windows 11, Git Bash e PowerShell. Python 3.12 em `.venv`. Rode tudo com
  `.venv/Scripts/python.exe`.
- `pytest==8.4.2` foi instalado no `.venv` (estava em `requirements-dev.txt`, mas ausente).
- `psycopg[binary]==3.3.6` foi instalado e adicionado ao `requirements.txt`.
- `.claude/launch.json` tem duas configurações de servidor (use a ferramenta de preview, não Bash):
  - `ifp-flask`: `--debug`, só `127.0.0.1:8000`.
  - `ifp-flask-rede`: `--host 0.0.0.0`, **sem debug** (o depurador do Werkzeug
    permitiria execução remota de código na rede). É a que está no ar para o
    amigo do usuário: **http://172.16.8.108:8000** (adaptador "Ethernet", rede
    marcada como Pública; o firewall já tinha regra liberando o Python 3.12).
- Sem debug, templates recarregam sozinhos (`TEMPLATES_AUTO_RELOAD`), mas mudanças
  em Python exigem reiniciar o servidor. A partida leva ~8s (o app confere os
  dados iniciais no banco ao subir).
- Login demonstrativo: `POST /acesso/rapido/<perfil>` com `student`, `teacher`,
  `school_coordinator`, `institute_coordinator`, `it_admin`.
- Arquivos alterados por `sed` no Git Bash perderam o CRLF (o Git normaliza; o diff
  de conteúdo fica limpo). Prefira editar preservando a quebra de linha existente.

---

## 3. Banco de dados — Supabase (banco principal)

- **Projeto em uso:** `IFP SP`, ref `rlhuwhziswyxibabnnjv`, região **São Paulo
  (`sa-east-1`)**, organização `InstitutoFabianaPinto` (plano Free). Criado com
  "Automatically expose new tables" e "Enable automatic RLS" **desligados**.
- **Conexão:** `instance/database.env` (ignorado pelo Git) com `IFP_DATABASE_URL`
  apontando para o **Session pooler** `aws-1-sa-east-1.pooler.supabase.com:5432`,
  usuário `postgres.rlhuwhziswyxibabnnjv`. **A senha é do usuário: nunca a leia,
  imprima ou peça.** Para inspecionar o formato, analise a URL sem exibir a senha.
  O modelo está em `instance/database.env.example`. A linha do projeto antigo
  (Oregon) ficou comentada no fim do arquivo e contém a senha antiga.
- `app/config.py`: lê `instance/database.env` (e `mysql.env` como legado),
  converte `postgresql://` para `postgresql+psycopg://`, adiciona
  `sslmode=require` para hosts `*.supabase.com/.co` e desliga prepared statements
  no servidor (`prepare_threshold=None`, compatível com o pooler). `TestConfig`
  sobrescreve as opções do engine para o SQLite dos testes não herdar as do Postgres.
- `app/database.py` → `_close_data_api()`: em PostgreSQL, ativa RLS em todas as
  tabelas do app (sem políticas) e revoga todas as permissões de `anon` e
  `authenticated`. A Data API não lê nem altera nada; o app acessa como dono das tabelas.
- Comandos: `flask --app run.py init-db` (idempotente: cria, fecha a API, carrega
  os dados iniciais sem duplicar) e `flask --app run.py db-status`.
- Verificado no IFP SP: 23 tabelas, RLS 23/23, 0 permissões para `anon`/`authenticated`,
  Security Advisor com 0 erros e 0 alertas (os 23 avisos "info" são RLS sem política, intencional).
- **Nomes em português:** tabelas e colunas do banco foram traduzidas
  (`alunos`, `turmas`, `questoes`, `simulados`, `tentativas`, `respostas`,
  `cartoes_resposta`, `lotes_leitura`, `paginas_leitura` etc.; colunas como
  `nome`, `matricula`, `turma_id`, `instituicao_id`). Os **atributos Python dos
  modelos continuam em inglês** e mapeiam para a coluna via
  `db.Column("nome_pt", ...)` em `app/models.py`. Os `to_record()` já usavam as
  chaves em português, que batem com as colunas. As rotinas de migração do
  esquema antigo em inglês (`_upgrade_scanner_columns`, `DROP INDEX` MySQL) foram
  removidas. Um MySQL antigo em inglês **não é migrado**.
- **Projeto antigo** `IFP` (Oregon, `us-west-2`, ref `nshljcqfuoevjsshohkm`): não é
  mais usado. Contém as 23 tabelas em inglês e as 23 em português. Tentar apagar as
  tabelas em inglês foi **bloqueado** (exclusão em massa em serviço externo); o SQL
  de `drop table` foi entregue ao usuário. Ele também tem uma função
  `public.rls_auto_enable()` (SECURITY DEFINER, de evento) que gera 2 alertas;
  não foi criada pelo app e não foi alterada. Pausar ou excluir esse projeto é
  decisão do usuário.
- Anexos (`instance/uploads`) e digitalizações (`SCAN_ROOT`, `instance/answer-scans`)
  continuam no disco local, não no Supabase Storage.

---

## 4. Marca e visual (concluído)

- **Logo:** vetorizada a partir da foto do perfil `@institutofabianapinto`
  (sobreposição de ~88% com o original). Fonte única: `app/templates/macros/brand.html`
  (`brand_logo_shapes`, `brand_logo`, `brand_logo_file`), com cada traço em elementos
  separados por classe (`brand-logo__line`, `__bowl`, `__cap`, `__sun`, `__wave`).
  Usada no topo (`base.html`), no login e no cartão-resposta impresso.
- **Ícones:** `scripts/gerar_icones.py` gera, a partir do macro, `logo-ifp.svg`,
  `favicon.svg`, `favicon.ico` (16/32/48), `apple-touch-icon.png`, `icon-192/512.png`
  e `icon-maskable-512.png` (rasteriza com Chrome/Edge headless).
  `app/templates/partials/brand_head.html` inclui favicons, `theme-color` e `app/static/manifest.json`.
- **Paleta:** em `app/static/css/tokens.css` — laranja `#B86122`, marrom
  `#522304`, marinho `#2D3B57`, areia `#EADAB3`, mais papéis semânticos (superfícies
  quentes, `--border-control` com contraste 3:1, tintas e linhas de estado). Cerca
  de 80 cores fixas foram trocadas por tokens; o print do cartão não carrega
  `tokens.css` e mantém hex próprios.
- **Animação da marca:** `.brand-watermark` em `app/static/css/identity.css` (as
  linhas do P sobem, as curvas se traçam, o sol nasce, as ondas entram e fazem uma
  maré finita de ~40s; há caminho para `prefers-reduced-motion`). Usada no login e no banner inicial.
- **Banner inicial para todos os perfis:** `app/static/css/home.css` (`.home-hero*`,
  vindo do antigo `student-home-hero`), `HOME_HEROES` em `app/core/routes.py`
  (chamada, ícone, ação e endpoint por perfil) e `app/templates/dashboard/index.html`.
  O balão do ícone fica à esquerda da marca para não cobri-la, com versão
  compacta entre 768 e 1279px. O antigo `welcome-header` foi removido.
- Correções de layout: `.guidance-panel` alinhado à esquerda (`components.css`); o
  card do aluno só exibe o número grande quando o valor é contagem (`value.isdigit()`).
- `PRODUCT.md` (raiz) tem o contexto de produto e da marca; não há `DESIGN.md`.

---

## 5. Desempenho (concluído)

- `app/auth/security.py`: `current_profile()` valida a conta **uma vez por
  requisição** e guarda o resultado em `flask.g` (antes eram 3 a 4 consultas por
  página: o mapa de identidade do SQLAlchemy usa referências fracas e a conta era descartada).
- `app/data/reports.py`: indicadores (`_load_baselines`) e notas
  (`_load_scores_by_student`) são lidos uma vez por requisição via `_per_request()`.
  O relatório das escolas caiu de 21 para 4 consultas.
- Medido contra o Supabase SP, com o servidor aquecido: páginas comuns em
  0,31–0,38s, relatório das escolas em 0,43–0,46s, notificações em 0,62s.
- Piso restante: ~64 ms por ida e volta × ~5 (ping do pool, BEGIN, conta, contador
  de notificações, ROLLBACK). Próximos ganhos dependem de decisão do usuário:
  hospedar o app em São Paulo, perto do banco (maior ganho), ou guardar a checagem
  da conta entre requisições (um usuário desativado continuaria entrando durante esse tempo).

---

## 6. Cartões-resposta — análise do fluxo (próximo trabalho)

O código do leitor está no branch de backup (seção 1). Hoje ele emite, imprime,
lê (QR, marcadores, bolhas) e permite conferência manual. Lacunas encontradas:

1. **As notas nunca são lançadas** (prioridade). Nada fora do leitor usa
   `paginas_leitura.respostas_detectadas`; a própria tela do lote avisa isso, e
   `docs/SCANNER_CARTOES.md` diz "não há lançamento automático de notas". Falta a
   etapa "Lançar resultados":
   - corrigir pelo `gabarito` das questões as páginas `Lido`/`Conferido`;
   - criar o resultado do aluno como `AssessmentAttempt` com status
     `Resultado disponível`. Os relatórios normalizam `final_score / nº de questões × 10`,
     então `final_score` é a pontuação bruta (acertos);
   - tratar conflito com tentativa online do mesmo aluno;
   - notificar o aluno.
2. **Sem fechamento de lote:** páginas em `Revisão` não bloqueiam nada.
3. **Página com QR ilegível (`Falha`) não pode ser atribuída manualmente a um aluno.**
4. **Duplicatas entre lotes** só geram aviso; não há como escolher a página válida.
5. **Questões discursivas em papel ficam sem nota:** o manifesto as ignora e não há onde lançar.
6. **Sem registro de ausentes** na prova em papel.
7. **Limite de 20 questões objetivas** (modelo `A4-20-v2`, `app/scanner/layout.py`).
8. **Professores não acessam o módulo** (`ALLOWED_ROLES` só tem as coordenações e a T.I.); confirmar com o usuário se é intencional.
9. **Processamento síncrono** de até 300 páginas por requisição; arriscado em hospedagem.
10. **Imagens no disco local**, fora do Supabase.

Cuidados ao mexer no cartão impresso (`app/templates/scanner/print.html`):

- `tests/test_scanner.py` rasteriza o SVG procurando o **primeiro `<image>` filho direto** (o QR) e os `<rect class="registration-marker">`. A logo precisa ficar dentro de um `<g>`, nunca num `<svg>` aninhado (a regex `<svg class="answer-sheet-art".*?</svg>` cortaria no primeiro `</svg>`).
- A logo no canto foi validada com o leitor real (normal, girado 180°, em cinza e em 150 dpi): os marcadores continuam detectados.

---

## 7. Decisões pendentes do usuário

1. Rodar o reparo da seção 1 (ou autorizar), depois decidir o commit.
2. Apagar as tabelas em inglês e decidir se pausa ou exclui o projeto Supabase de Oregon.
3. Remover a linha comentada de Oregon do `instance/database.env` depois de excluir aquele projeto.
4. Hospedagem do app em São Paulo, ou cache da checagem de conta.
5. Lacunas dos cartões-resposta: começar pelo lançamento de notas; confirmar o acesso de professores.
6. Traduzir também os nomes das classes e atributos Python dos modelos (opcional, refatoração grande).

## 8. Regras observadas nesta sessão

- Duas ações foram bloqueadas pelo classificador de permissões (exclusão das
  tabelas antigas no Supabase e restauração de arquivos locais). Não repita nem
  contorne; peça ao usuário.
- Nunca faça login, nunca digite senhas e nunca leia a senha do banco. O usuário preenche `instance/database.env`.
- Tentativas com senha errada no pooler podem bloquear o IP por um tempo; valide o formato da URL antes de conectar.
- Interface e documentação em português do Brasil.
