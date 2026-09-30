# Instituto Fabiana Pinto - Sistema de Avaliações

Sistema funcional de aplicação, acompanhamento e análise de avaliações,
construído com Flask. A persistência MySQL começou pela base administrativa;
os módulos ainda não migrados continuam usando dados demonstrativos em memória.

## Estado atual

Os blocos 1 a 6 foram concluídos. A aplicação contém login demonstrativo, cinco
perfis, estrutura acadêmica, banco de questões e gestão de simulados.

## Funcionalidades disponíveis

- Login livre e cinco acessos rápidos.
- Sessão e navegação específicas por perfil.
- Municípios, instituições, séries, turmas, alunos e professores.
- Busca, filtros, paginação, detalhes e formulários demonstrativos.
- Escopo acadêmico aplicado ao Aluno, Professor e Coordenador do Colégio.
- Banco com 16 questões de Matemática sobre operações primárias.
- Professores criam e editam as próprias questões; coordenadores consultam e solicitam revisão.
- Catálogo de matérias e assuntos com escopo global ou institucional.
- Professores com CPF, e-mail e disciplinas selecionadas do catálogo aprovado.
- Professores gerenciam assuntos somente das matérias vinculadas ao próprio cadastro.
- CPF usado somente no cadastro e na verificação de duplicidade, sem exibição em listas ou detalhes.
- Bloqueio demonstrativo de CPF e e-mail duplicados entre usuários.
- Filtros de alunos e professores por município e instituição.
- Transferência de professores entre instituições para Coordenação do Instituto e T.I.
- Gestão de usuários exclusiva para T.I., com filtros, ordenação, cadastro e desativação.
- Persistência local MySQL para municípios, instituições e usuários.
- Criação, composição, publicação e agendamento demonstrativos de simulados.
- Fluxo de simulados conduzido pelo Coordenador do Colégio: solicitação com prazo, entrega pelos professores, aprovação ou revisão, agendamento e aviso aos alunos.
- Professores podem responder com questões do próprio banco, do histórico de envios ou com uma questão nova.
- Central de notificações do aluno para os simulados agendados ao seu ano escolar.
- Histórico de revisão com estados Pendente, Em revisão, Revisada e Aprovada.
- Tentativas, respostas, tempo restante, correções abertas e resultados persistidos no banco.
- Correção de respostas abertas pelo professor com nota, conceito e comentário.
- Anexos e imagens armazenados em pasta local controlada, com metadados no MySQL.
- Notificações internas para solicitações, revisões, simulados, materiais e correções.
- Simulado de teste com oito questões, distribuídas entre as quatro operações.
- Alternativas do simulado exibidas verticalmente, de A a D.
- Questões objetivas e abertas, com resposta digitada e correção manual pendente.
- Questões com imagem opcional de até 2 MB e trechos em negrito.
- Área do aluno para consultar e responder simulados liberados, com resultado ao final.
- Proteções durante o simulado contra impressão, cópia, recorte, colagem e menu de contexto, além de tela de privacidade ao perder o foco.
- Mural de materiais de revisão publicados pelos professores para suas turmas.
- Postagens com título, descrição, texto e anexos PDF, PNG, PPT ou PPTX.
- Edição e exclusão das próprias publicações pelo professor.
- Banco de questões disponível para professores e coordenações, com ações definidas por responsabilidade.
- Layout responsivo para computador e telas menores.
- Relatórios hierárquicos de desempenho: rede, escola, série e turma.
- Gráficos de linhas e colunas para médias, evolução, frequência e faltas.
- Ranking das médias das escolas exclusivo para a Coordenação do Instituto.
- Visão da própria escola com restrição de acesso para a Coordenação do Colégio.

## Executar localmente

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app run.py run --debug --port 8000
```

A aplicação ficará disponível em `http://127.0.0.1:8000`.

## Documentação

- [Planejamento do frontend](docs/PLANEJAMENTO_FRONTEND.md)
- [Diário de desenvolvimento](docs/DIARIO_DESENVOLVIMENTO.md)
- [Banco de dados local](docs/BANCO_DADOS.md)
- [Pendências de segurança](docs/PENDENCIAS_SEGURANCA.md)
