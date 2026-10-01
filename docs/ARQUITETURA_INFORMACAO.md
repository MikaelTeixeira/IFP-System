# Arquitetura de informação

## Objetivo

Organizar uma única aplicação para os cinco perfis do Instituto Fabiana Pinto.
Rotas, componentes e dados serão compartilhados; cada perfil receberá um recorte
de navegação e ações compatível com seu escopo.

## Estrutura global

```text
Acesso
└── Login
    ├── Formulário livre
    └── Acessos rápidos por perfil

Área autenticada
├── Início
├── Estrutura acadêmica
│   ├── Municípios
│   ├── Instituições
│   ├── Séries
│   ├── Turmas
│   ├── Alunos
│   └── Professores
├── Matérias e assuntos
│   ├── Catálogo global
│   └── Catálogo por instituição
├── Banco de questões
│   └── Matéria → assunto → questões
├── Simulados
├── Usuários do sistema
├── Avisos
├── Perfil ativo
└── Sair
```

Nesta primeira entrega, os itens que dependem de blocos posteriores não
aparecerão como links vazios no menu.

## Mapa de rotas dos blocos 2 a 4

| Rota | Nome na interface | Finalidade |
| --- | --- | --- |
| `/` | Entrada | Redirecionar para login ou início conforme a sessão |
| `/acesso` | Entrar | Exibir formulário livre e acessos rápidos |
| `/acesso/entrar` | Entrar | Criar sessão demonstrativa |
| `/acesso/rapido/<perfil>` | Acesso rápido | Ativar um dos cinco perfis |
| `/sair` | Sair | Encerrar a sessão demonstrativa |
| `/inicio` | Início | Exibir resumo contextual do perfil ativo |
| `/academico/municipios` | Municípios | Listar e gerenciar municípios permitidos |
| `/academico/municipios/novo` | Novo município | Simular inclusão de município |
| `/academico/municipios/<id>` | Município | Mostrar detalhes e instituições relacionadas |
| `/academico/instituicoes` | Instituições | Listar instituições no escopo do perfil |
| `/academico/instituicoes/nova` | Nova instituição | Simular inclusão de instituição |
| `/academico/instituicoes/<id>` | Instituição | Mostrar dados, turmas e pessoas relacionadas |
| `/academico/series` | Séries | Listar séries disponíveis |
| `/academico/turmas` | Turmas | Listar turmas no escopo do perfil |
| `/academico/turmas/nova` | Nova turma | Simular inclusão de turma |
| `/academico/turmas/<id>` | Turma | Mostrar alunos, professores e vínculos |
| `/academico/alunos` | Alunos | Listar e filtrar alunos permitidos |
| `/academico/alunos/novo` | Novo aluno | Simular inclusão de aluno |
| `/academico/alunos/<id>` | Aluno | Mostrar cadastro e vínculo acadêmico |
| `/academico/professores` | Professores | Listar e filtrar professores permitidos |
| `/academico/professores/novo` | Novo professor | Simular inclusão de professor |
| `/academico/professores/<id>` | Professor | Mostrar cadastro e turmas relacionadas |
| `/academico/professores/<id>/transferir` | Transferir professor | Alterar a instituição e limpar vínculos de turma |
| `/curriculo` | Matérias e assuntos | Consultar o catálogo disponível no perfil |
| `/curriculo/materias/nova` | Nova matéria | Criar matéria global ou institucional conforme o perfil |
| `/curriculo/assuntos/novo` | Novo assunto | Vincular assunto a uma matéria disponível |
| `/curriculo/assuntos/<id>/editar` | Editar assunto | Alterar assunto dentro do escopo permitido |
| `/curriculo/assuntos/<id>/excluir` | Excluir assunto | Remover assunto sem vínculos após confirmação |
| `/questoes` | Banco de questões | Navegar por matéria, assunto e questões |
| `/questoes/nova` | Nova questão | Professor cria questão em matéria vinculada |
| `/questoes/<id>/editar` | Editar questão | Professor altera questão da própria autoria |
| `/questoes/<id>/solicitar-revisao` | Solicitar revisão | Coordenação envia orientação ao professor responsável |
| `/questoes/<id>/iniciar-revisao` | Iniciar revisão | Professor altera o estado para Em revisão |
| `/questoes/<id>/aprovar-revisao` | Aprovar revisão | Coordenação encerra a revisão após conferir a alteração |
| `/aluno/simulados` | Meus simulados | Listar simulados liberados para a instituição do aluno |
| `/aluno/simulados/<id>` | Orientações do simulado | Exibir duração, questões e instruções antes do início |
| `/aluno/simulados/<id>/responder` | Responder simulado | Persistir respostas, tempo e entrega e mostrar o resultado |
| `/aluno/simulados/<id>/salvar` | Salvar tentativa | Persistir respostas parciais e tempo restante |
| `/aluno/simulados/<id>/resultado` | Resultado | Mostrar situação, pontuação e comentários da correção |
| `/simulados/correcoes` | Correções abertas | Professor consulta respostas abertas de sua autoria |
| `/simulados/correcoes/<tentativa>` | Corrigir respostas | Informar nota, conceito e comentário para o aluno |
| `/notificacoes` | Notificações | Exibir os avisos persistidos para o perfil atual |
| `/aluno/revisao` | Materiais de revisão | Consultar postagens destinadas à turma do aluno |
| `/materiais` | Materiais de revisão | Listar as postagens criadas pelo professor atual |
| `/materiais/novo` | Publicar material | Criar postagem para uma ou mais turmas vinculadas |
| `/materiais/<id>/editar` | Editar publicação | Alterar conteúdo, turmas ou anexo da própria postagem |
| `/materiais/<id>/excluir` | Excluir publicação | Remover a própria postagem após confirmação |
| `/materiais/<id>/anexo` | Anexo do material | Abrir PDF, PNG, PPT ou PPTX permitido para o perfil |
| `/simulados/solicitar` | Solicitar simulado | Selecionar anos, matérias e professores responsáveis |
| `/simulados/solicitacoes/<id>` | Detalhes da solicitação | Consultar escopo e atribuições do pedido |
| `/simulados/solicitacoes-professor` | Solicitações de questões | Professor acompanha pedidos e prazos recebidos |
| `/simulados/solicitacoes/<id>/responder` | Responder solicitação | Enviar questão do banco, histórico ou criar uma nova |
| `/simulados/solicitacoes/<id>/questoes/<questao>/aprovar` | Aprovar questão | Coordenação escolar aceita uma entrega |
| `/simulados/solicitacoes/<id>/questoes/<questao>/solicitar-revisao` | Solicitar revisão | Coordenação escolar devolve a questão com orientação |
| `/simulados/solicitacoes/<id>/agendar` | Agendar solicitação concluída | Criar o simulado aprovado e avisar os alunos participantes |
| `/aluno/notificacoes` | Notificações | Consultar avisos de simulados agendados para o ano do aluno |
| `/usuarios` | Usuários | Ordenar, filtrar e consultar os acessos do sistema |
| `/usuarios/novo` | Adicionar usuário | Criar um acesso demonstrativo com cargo e vínculo |
| `/usuarios/<id>/status` | Alterar situação | Ativar ou desativar um usuário após confirmação |

Os formulários de edição usarão o sufixo `/editar`. Exclusões, ativações e
mudanças de vínculo serão ações submetidas por `POST`. Municípios, instituições
e usuários usam persistência MySQL; currículo, questões, simulados, solicitações,
materiais, tentativas, notificações e relatórios também são restaurados do banco.

## Navegação por perfil

### Aluno

- Início.
- Simulados publicados ou agendados para sua instituição.
- Materiais de revisão publicados pelos professores da turma.
- Acesso ao próprio perfil.
- Nenhum item administrativo da estrutura acadêmica.

### Professor

- Início.
- Publicação, edição e exclusão dos próprios materiais de revisão.
- Consulta das próprias matérias e gestão dos assuntos vinculados a elas.
- Criação e edição das próprias questões, com histórico e aprovação das revisões.
- Correção das respostas abertas vinculadas às questões de sua autoria.
- Caixa de solicitações com prazo e envio de questões do banco, histórico ou uma nova questão.
- Turmas às quais está vinculado.
- Alunos dessas turmas em modo de consulta.
- Próprio perfil.
- Criação direta, publicação e configuração administrativa de simulados ocultas;
  o Professor acessa somente as solicitações que lhe foram atribuídas.

### Coordenador do Colégio

- Início.
- Instituição atual em modo de consulta e edição permitida.
- Séries, turmas, alunos e professores da própria escola.
- Gestão de matérias exclusivas da própria instituição e consulta dos assuntos,
  cuja manutenção pertence aos professores.
- Questões vinculadas somente à própria instituição.
- Consulta das questões da instituição e solicitação de revisão ao professor,
  sem acesso à edição.
- Solicitação de simulados para os anos da própria instituição, avaliação das
  entregas e agendamento após a aprovação integral.
- Seleção de matérias e de um professor habilitado por matéria, sempre dentro da
  própria escola.
- Nenhum acesso a outra instituição.

### Coordenador do Instituto

- Início.
- Municípios, instituições, séries, turmas, alunos e professores.
- Criação e edição dentro do instituto.
- Criação de matérias globais e transferência de professores entre instituições.
- Consulta das solicitações de simulados enviadas pelos colégios.
- Consulta de todas as questões e solicitação de revisão aos autores, sem edição.

### Administrador/T.I.

- Início.
- Aba de usuários com ordenação alfabética e filtros por município, instituição
  e cargo.
- Cadastro e ativação ou desativação de usuários.
- Toda a estrutura acadêmica.
- Ações administrativas simuladas.
- Transferência de professores entre instituições.
- Indicação visual de ações executadas como override.
- Banco de questões, simulados, matérias e assuntos ocultos.

## Hierarquia de navegação

```text
Município
└── Instituição
    ├── Série
    │   └── Turma
    │       ├── Alunos
    │       └── Professores
    └── Usuários vinculados
```

O breadcrumb refletirá essa hierarquia. Quando o usuário entrar por uma lista
global, o caminho será encurtado para evitar uma trilha artificial.

## Regras de escopo

- O escopo é calculado antes de montar menus, listas e ações.
- O Coordenador do Colégio recebe uma única instituição fixa na sessão.
- O Professor recebe somente as turmas às quais está vinculado.
- O Aluno recebe somente o próprio registro.
- Coordenador do Instituto e T.I. podem navegar por toda a estrutura mockada.
- A interface não oferecerá troca de instituição para perfis com escopo fixo.
- O cadastro de usuários valida CPF e e-mail únicos na camada persistente.
- Listas de alunos e professores podem ser filtradas por município e instituição.
- O CPF permanece disponível para validação, mas não é exibido em listas ou
  detalhes.
- A gestão dos módulos de currículo e avaliação é exclusiva dos dois perfis de
  coordenação; o Aluno recebe somente o fluxo de aplicação e o material de revisão.
- O banco aceita questões objetivas, corrigidas automaticamente, e questões
  abertas, respondidas por texto e encaminhadas para correção manual.
- A entrega exige resposta em todas as questões e a página de aplicação aplica
  barreiras de impressão, área de transferência e exposição ao perder o foco.
- Início, respostas parciais, entrega, tempo restante, pontuação e correções das
  tentativas são persistidos no banco.
- Arquivos ficam fora da pasta pública e são servidos somente após a validação do
  perfil e do vínculo com a questão, publicação ou turma.
- Identificadores técnicos não serão usados como títulos principais das páginas.

## Padrão de página interna

```text
┌─────────────────────────────────────────────────────────────┐
│ marca      busca opcional             avisos | perfil       │
├──────────────┬──────────────────────────────────────────────┤
│ navegação    │ breadcrumb                                   │
│              │ título da página          ação principal     │
│ Início       │ explicação curta                              │
│ Acadêmico    │                                               │
│  Turmas      │ filtros contextuais                           │
│  Alunos      │───────────────────────────────────────────────│
│  Professores │ lista ou detalhe                              │
│              │                                               │
└──────────────┴──────────────────────────────────────────────┘
```

Em telas menores, a navegação lateral vira um painel acionado pelo cabeçalho. A
ação principal permanece próxima do título e não fica presa ao rodapé da tela.
# Relatórios

O módulo `/relatorios` atende as duas coordenações. A Coordenação do Instituto
recebe a visão de rede e segue para `/relatorios/escolas/<id>`. A partir da escola,
o detalhamento usa `/series/<id>` e `/turmas/<id>`. A Coordenação do Colégio é
direcionada para sua instituição e todas as rotas internas repetem a verificação
de escopo no servidor.

A leitura segue sempre a mesma ordem: indicador resumido, evolução em linha,
comparação em colunas e acesso ao próximo nível acadêmico.
