# Banco de dados local

## Tecnologia

O ambiente local usa MySQL 8 com `utf8mb4`, SQLAlchemy e o driver PyMySQL. A
senha não é armazenada no repositório: fica em `instance/mysql.env`, arquivo
ignorado pelo Git.

## Configuração inicial

Com o serviço MySQL em execução, rode:

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

A camada persistente contém as tabelas relacionais:

- `municipalities`;
- `institutions`, vinculada ao município por chave estrangeira;
- `user_accounts`, vinculada opcionalmente a município e instituição;
- `grade_series`, `school_classes`, `students` e `teachers`, com os vínculos acadêmicos;
- `subjects` e `topics`, com escopo global ou institucional;
- `questions`, incluindo alternativas, resposta esperada, imagem e estado de revisão;
- `assessments` e `assessment_requests`, incluindo composição e fluxo de solicitação;
- `material_posts`, com texto, turmas e referência ao anexo;
- `report_snapshots`, com os indicadores demonstrativos usados pelos gráficos;
- `assessment_attempts`, com início, entrega, duração, tempo restante, situação e pontuação;
- `attempt_answers`, com respostas objetivas ou abertas, nota, conceito e comentário;
- `stored_files`, com caminho relativo, nome original, formato e tamanho;
- `notifications`, com destinatário, tipo, leitura e destino do aviso;
- `question_review_events`, com o histórico dos estados de revisão.

Esses registros sobrevivem ao reinício do Flask quando `instance/mysql.env`
estiver configurado. As listas usadas pelas telas são recarregadas das tabelas
ao iniciar a aplicação e cada inclusão, edição, transferência, revisão,
agendamento ou exclusão atualiza o MySQL imediatamente.

Os arquivos físicos ficam sob `instance/uploads`, fora da pasta pública, e
somente são entregues pelas rotas após a verificação do perfil. Registros de
arquivo sem questão ou publicação proprietária são removidos na inicialização.

Os números históricos de frequência e evolução ainda são dados de demonstração,
mas agora ficam registrados em `report_snapshots`. Resultados de simulados são
calculados a partir das tentativas e respostas persistidas.
