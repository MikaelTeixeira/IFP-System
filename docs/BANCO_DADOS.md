# Banco de dados

## Supabase (banco principal)

O banco principal é um PostgreSQL no Supabase, acessado por SQLAlchemy com o
driver psycopg 3. A URL com a senha fica somente em `instance/database.env`,
arquivo ignorado pelo Git.

1. No Supabase, use o projeto **IFP SP** da organização InstitutoFabianaPinto
   (região São Paulo, `sa-east-1`; criado com "Automatically expose new tables" e
   "Enable automatic RLS" desligados).
2. Copie `instance/database.env.example` para `instance/database.env`.
3. Em **Connect**, copie a URI do **Session pooler** (porta 5432), troque
   `[YOUR-PASSWORD]` pela senha do banco e cole em `IFP_DATABASE_URL`.
4. Crie as tabelas e carregue os dados iniciais:

```powershell
flask --app run.py init-db
flask --app run.py db-status
```

O app converte a URI para o driver psycopg, exige SSL e desativa prepared
statements no servidor, o que mantém a conexão compatível com o pooler.

### Segurança

O Supabase publica o schema `public` pela Data API para os papéis `anon` e
`authenticated`. Ao inicializar no PostgreSQL, o app ativa Row Level Security em
todas as tabelas, sem políticas, e revoga as permissões desses dois papéis
nelas. A API pública não enxerga nem altera nada, e a aplicação continua
acessando como dona das tabelas. Não crie políticas nem conceda permissões sem
revisar o escopo por perfil.

Anexos e imagens continuam em `instance/uploads`; o banco guarda os metadados.

## Alternativa local (MySQL)

Para trabalhar sem internet, o app também aceita MySQL 8 com `utf8mb4` e o
driver PyMySQL. Com o serviço MySQL em execução, rode:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_mysql.py
```

O comando solicita a senha administrativa do MySQL sem exibi-la, cria o banco
`instituto_fabiana_pinto`, cria o usuário dedicado `ifp_app`, grava a configuração
local e inicializa as tabelas.

Depois, reinicie o servidor Flask:

```powershell
flask --app run.py run --debug --port 8000
```

## Comandos de diagnóstico

```powershell
flask --app run.py db-status
flask --app run.py init-db
```

## Escopo migrado

A camada persistente contém as tabelas relacionais, com nomes de tabelas e
colunas em português (os modelos Python em `app/models.py` mapeiam cada atributo
para a coluna correspondente):

- `municipios`;
- `instituicoes`, vinculada ao município por chave estrangeira;
- `usuarios`, vinculada opcionalmente a município e instituição;
- `series`, `turmas`, `alunos` e `professores`, com os vínculos acadêmicos;
- `materias` e `assuntos`, com escopo global ou institucional;
- `questoes`, incluindo alternativas, resposta esperada, imagem e estado de revisão;
- `simulados` e `solicitacoes_simulado`, incluindo composição e fluxo de solicitação;
- `materiais`, com texto, turmas e referência ao anexo;
- `indicadores_relatorio` e `frequencias_alunos`, com os indicadores usados pelos gráficos;
- `tentativas`, com início, entrega, duração, tempo restante, situação e pontuação;
- `respostas`, com respostas objetivas ou abertas, nota, conceito e comentário;
- `arquivos`, com caminho relativo, nome original, formato e tamanho;
- `notificacoes`, com destinatário, tipo, leitura e destino do aviso;
- `historico_revisoes`, com o histórico dos estados de revisão;
- `cartoes_resposta`, `lotes_leitura` e `paginas_leitura`, com a emissão e a leitura dos cartões-resposta.

Esses registros sobrevivem ao reinício do Flask quando `instance/database.env`
estiver configurado. As listas usadas pelas telas são recarregadas das tabelas
ao iniciar a aplicação e cada inclusão, edição, transferência, revisão,
agendamento ou exclusão atualiza o banco imediatamente.

Os arquivos físicos ficam sob `instance/uploads`, fora da pasta pública, e
somente são entregues pelas rotas após a verificação do perfil. Registros de
arquivo sem questão ou publicação proprietária são removidos na inicialização.

Os números históricos de frequência e evolução ainda são dados de demonstração,
mas agora ficam registrados em `indicadores_relatorio`. Resultados de simulados são
calculados a partir das tentativas e respostas persistidas.
