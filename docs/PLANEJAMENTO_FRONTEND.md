# Planejamento do frontend

## 1. Objetivo

Construir um frontend funcional para o **Instituto Fabiana Pinto**, com Flask,
dados demonstrativos e navegação completa. A base administrativa já usa MySQL
local; autenticação real e validação de credenciais continuam fora desta etapa.

A primeira entrega contemplou os **blocos 1 a 4**. A segunda etapa amplia o
frontend com os **blocos 5 e 6**, dedicados ao banco de questões e aos
simulados.

## 2. Princípios de arquitetura

- Construir módulos compartilhados e aplicar permissões conforme o perfil.
- Evitar uma aplicação independente para cada tipo de usuário.
- Separar rotas, serviços de dados fictícios, componentes visuais e templates.
- Manter a interface preparada para substituir os dados fictícios por serviços
  reais quando o backend for implementado.
- Priorizar uso em computador, mantendo funcionamento adequado em telas menores.
- Usar português brasileiro em toda a interface.
- Destacar informações importantes com peso tipográfico, cor e hierarquia, sem
  depender somente da cor para comunicar significado.

## 3. Base técnica

- **Servidor e renderização:** Flask com templates Jinja.
- **Organização:** Blueprints por domínio funcional.
- **Interface:** HTML semântico e CSS próprio com componentes reutilizáveis.
- **Interações:** JavaScript modular, sem dependência obrigatória de framework.
- **Dados temporários:** estruturas mockadas em memória.
- **Sessão:** sessão Flask usada apenas para simular o perfil ativo.
- **Persistência:** MySQL local para municípios, instituições e usuários; os
  demais módulos ainda são restaurados ao reiniciar a aplicação.

Dependências adicionais só serão incluídas quando trouxerem benefício claro e
serão registradas no diário de desenvolvimento.

## 4. Identidade visual

A direção será **educacional, acolhedora e sóbria**, adequada a uma instituição
de ensino e a usuários administrativos.

### Cores fornecidas

| Papel | Cor | Uso planejado |
| --- | --- | --- |
| Azul institucional | `#2D3D5F` | Navegação, títulos, estrutura e ações principais |
| Laranja de destaque | `#B96121` | Ênfase, seleção, indicadores e chamadas de atenção |

Variações claras e escuras dessas cores poderão ser derivadas para fundos,
bordas, foco, estados interativos e gráficos. A interface também usará neutros
acessíveis para superfícies, textos e divisores.

### Diretrizes

- Tipografia legível e hierarquia clara.
- Cantos discretamente arredondados e superfícies leves.
- Destaques em negrito reservados para dados, alertas e ações importantes.
- Ícones sempre acompanhados de rótulos quando a ação puder gerar dúvida.
- Movimento limitado a respostas de interação e mudanças de estado.

## 5. Perfis previstos

1. Aluno.
2. Professor.
3. Coordenador do Colégio.
4. Coordenador do Instituto.
5. Administrador/T.I.

As regras já definidas para esta etapa são:

- O professor acessa as próprias matérias, assuntos e questões e responde às solicitações de questões recebidas.
- O Coordenador do Instituto pode criar e publicar simulados.
- O Coordenador do Colégio solicita, avalia e agenda simulados somente para a própria escola após aprovar todas as questões.
- A área de conteúdo representa materiais de estudo; não haverá entrega de
  tarefas.
- Ações totalmente indisponíveis para um perfil ficarão ocultas.
- Ações condicionais permanecerão visíveis e desabilitadas, acompanhadas do
  motivo.

## 6. Blocos de execução

### Bloco 1 - Definição funcional e visual

**Estado:** concluído em 11 de setembro de 2026.

**Escopo**

- Consolidar mapa de rotas e permissões.
- Definir tokens de cor, tipografia, espaçamento, bordas e estados.
- Definir componentes compartilhados e conteúdo fictício.
- Projetar os estados vazio, carregando, sucesso, erro e acesso condicionado.

**Critério de conclusão**

- Arquitetura de informação documentada.
- Sistema visual básico definido.
- Matriz de rotas e perfis aprovada para os blocos 2 a 4.

**Entregáveis produzidos**

- [Arquitetura de informação](ARQUITETURA_INFORMACAO.md).
- [Matriz de rotas e permissões](MATRIZ_ROTAS_PERMISSOES.md).
- [Sistema visual](SISTEMA_VISUAL.md).
- [Dados de demonstração](DADOS_DEMONSTRACAO.md).

### Bloco 2 - Fundação Flask

**Estado:** concluído em 11 de setembro de 2026.

**Escopo**

- Criar a estrutura modular da aplicação.
- Configurar aplicação, Blueprints e sessão.
- Criar template base, componentes compartilhados e arquivos estáticos.
- Preparar dados fictícios e utilitários de apresentação.
- Criar tratamento visual para páginas inexistentes e erros internos.

**Critério de conclusão**

- Aplicação inicia localmente sem erros.
- Templates e componentes compartilham o mesmo sistema visual.
- Estrutura aceita novos módulos sem duplicar layouts ou navegação.

**Entregáveis produzidos**

- Fábrica da aplicação e configuração por ambiente.
- Blueprint principal preparado para receber novos domínios.
- Templates base, partials e macros reutilizáveis.
- Tokens, estilos estruturais, componentes e regras responsivas.
- Dados temporários isolados em módulo próprio.
- Páginas personalizadas para acesso restrito, página inexistente e erro interno.
- Página de referência visual para revisão dos componentes.
- Testes de inicialização, renderização e erro 404.

### Bloco 3 - Acesso e estrutura principal

**Estado:** concluído em 29 de setembro de 2026.

**Escopo**

- Criar formulário de login livre.
- Permitir acesso mesmo com usuário e senha vazios.
- Oferecer cinco acessos rápidos, um para cada perfil.
- Simular o perfil ativo por sessão.
- Criar navegação principal, cabeçalho, menu de perfil, breadcrumbs e avisos.
- Direcionar cada perfil para uma página inicial coerente com seu escopo.

**Critério de conclusão**

- Qualquer pessoa consegue entrar pelo formulário sem validação.
- Os acessos rápidos ativam corretamente cada um dos cinco perfis.
- A navegação mostra apenas os módulos permitidos para o perfil ativo.
- É possível sair e trocar de perfil.
- O fluxo funciona por teclado e em telas menores.

**Entregáveis produzidos**

- Login livre com perfil selecionável e campos opcionais.
- Cinco acessos rápidos com identidades demonstrativas.
- Sessão Flask para armazenar o perfil ativo.
- Entrada, saída e troca de perfil.
- Dashboard e navegação montados conforme o perfil.
- Cabeçalho, menu de perfil, avisos e navegação móvel.
- Proteção de rotas e página de acesso restrito.

### Bloco 4 - Estrutura acadêmica

**Estado:** concluído em 29 de setembro de 2026.

**Escopo**

- Criar interfaces compartilhadas para municípios, instituições, séries e
  turmas.
- Criar listas de alunos, professores e vínculos.
- Incluir busca, filtros, paginação visual, detalhes e formulários simulados.
- Aplicar o escopo institucional e as permissões de cada perfil.
- Incluir confirmações e retorno visual das ações mockadas.

**Critério de conclusão**

- Usuários autorizados navegam pela hierarquia acadêmica.
- Listas, filtros e detalhes funcionam com dados fictícios.
- Formulários simulam inclusão e edição durante a sessão.
- O Coordenador do Colégio permanece restrito à própria escola.
- Ações ocultas e condicionais seguem a regra visual definida.
- As telas principais funcionam em computador e se adaptam a telas menores.

**Entregáveis produzidos**

- Dados fictícios relacionando municípios, instituições, séries, turmas, alunos
  e professores.
- Listagens reutilizáveis com busca, filtro por situação e paginação.
- Telas de detalhe com vínculos acadêmicos relacionados.
- Formulários demonstrativos de inclusão e edição.
- Alteração de situação reservada aos perfis autorizados.
- Escopo próprio para aluno, professor e Coordenador do Colégio.
- Hierarquia completa para Coordenador do Instituto e Administrador/T.I.
- Adaptação das tabelas, filtros, detalhes e formulários para telas menores.

### Bloco 5 - Banco de questões

**Estado:** concluído em 29 de setembro de 2026.

**Escopo**

- Criar listagem, busca, filtros, paginação, detalhes e formulários de questões.
- Restringir o banco inicial à disciplina de **Matemática** e ao assunto
  **Operações primárias**.
- Organizar as questões por soma, subtração, multiplicação e divisão.
- Permitir que os professores criem e editem questões das próprias matérias.
- Permitir que as coordenações consultem questões e solicitem revisão ao autor.

**Critério de conclusão**

- O banco contém as quatro operações com níveis variados de dificuldade.
- As questões exibem enunciado, quatro alternativas, gabarito e resolução.
- Busca e filtros por operação e dificuldade funcionam com dados em memória.
- As permissões separam autoria do Professor e revisão solicitada pelas coordenações.
- Listagem, detalhe e formulário funcionam em computador e telas menores.

**Entregáveis produzidos**

- Banco inicial com **16 questões**, quatro para cada operação primária.
- Listagem paginada com busca, filtro de operação e filtro de dificuldade.
- Tela de consulta com destaque do gabarito e resolução esperada.
- Formulários demonstrativos para inclusão e edição.
- Integração do módulo ao menu e ao resumo inicial dos perfis autorizados.

**Ampliação posterior**

- Navegação hierárquica por matéria, assunto e questões.
- Catálogo administrável de matérias e assuntos.
- Matérias globais para a Coordenação do Instituto.
- Matérias institucionais para o Coordenador do Colégio dentro da própria escola.

### Bloco 6 - Criação e gestão de simulados

**Estado:** concluído em 29 de setembro de 2026.

**Escopo**

- Criar listagem, filtros, detalhes e formulários de simulados.
- Permitir composição da avaliação a partir do banco de questões.
- Configurar título, modalidade, público, duração, data e instituições.
- Manter a criação direta e a publicação administrativa com o Coordenador do Instituto.
- Permitir que o Coordenador do Colégio conduza solicitações e agende apenas o resultado aprovado para a própria escola.
- Ocultar o módulo para Professor e T.I.

**Critério de conclusão**

- Um simulado pode ser composto com questões selecionadas do banco.
- Situação, público, duração, modalidade e data aparecem de forma clara.
- Publicação e agendamento respeitam as permissões definidas.
- O Coordenador do Colégio permanece limitado à própria instituição.
- Listagem, detalhe e formulário funcionam em computador e telas menores.

**Entregáveis produzidos**

- Fluxo demonstrativo de criação e edição de simulados.
- Ações em memória para publicação e agendamento.
- **Simulado teste - Operações primárias**, com oito questões: duas de soma,
  duas de subtração, duas de multiplicação e duas de divisão.
- Seleção de instituições e composição visual da prova.
- Integração do módulo ao menu e ao resumo inicial dos perfis autorizados.

## 7. Ordem de execução

Os blocos serão executados sequencialmente. Cada bloco passará por revisão
visual e funcional antes do início do seguinte. Correções estruturais descobertas
em um bloco serão resolvidas antes de ampliar o escopo.

## 8. Fora do escopo atual

- Banco de dados e migrações.
- Autenticação, recuperação de senha e autorização reais.
- Validação de credenciais e integrações externas.
- Prova remota com temporizador, QR Code, cartões-resposta, scanner e OMR.
- Correção, analytics, conteúdo e gamificação.

Esses itens poderão ser planejados em uma etapa posterior sem alterar a base de
componentes e permissões criada nos seis primeiros blocos.

## 9. Evolução da gestão de usuários e currículo

Após os seis blocos iniciais, a estrutura foi ampliada com:

- código oficial no cadastro de município, acompanhado de explicação curta;
- filtros de alunos e professores por município e instituição;
- CPF e e-mail nos cadastros de usuários, com bloqueio de duplicidade;
- disciplinas de professores selecionadas do catálogo aprovado;
- gestão de professores da própria instituição pelo Coordenador do Colégio;
- transferência de professores entre instituições pela Coordenação do Instituto
  e por T.I.;
- catálogo de matérias e assuntos com escopo global e institucional.
- CPF preservado apenas para cadastro e unicidade, sem exibição em listas ou
  detalhes;
- módulos de currículo e avaliação restritos às coordenações;
- questões e simulados do Coordenador do Colégio limitados à própria escola.

## 10. Evolução da área do aluno

A área do aluno foi ampliada com:

- listagem dos simulados publicados ou agendados para sua instituição;
- página de orientações antes do início da atividade;
- formulário de resposta sem exposição prévia do gabarito ou da resolução;
- bloqueio da entrega enquanto houver questões em branco, com aviso das
  questões pendentes;
- resultado com pontuação e revisão das respostas após o envio;
- mural de materiais de revisão organizado por postagem, matéria e assunto;
- material de Matemática sobre soma, subtração, multiplicação e divisão, com
  explicações curtas e exemplos.

## 11. Publicações de revisão pelo professor

- Somente o Professor cria as postagens de revisão.
- Cada publicação possui título, descrição e matéria/assunto.
- O professor pode incluir texto ou anexar PDF, PNG, PPT ou PPTX.
- A postagem é direcionada somente às turmas vinculadas ao professor.
- O aluno visualiza um mural cronológico com os materiais destinados à sua turma.

## 12. Gestão de usuários por T.I.

- Área disponível somente para o perfil Administrador/T.I.
- Ordenação de nomes de A a Z ou de Z a A.
- Filtros combináveis por município, instituição e cargo.
- Cadastro com nome, CPF, e-mail, cargo e vínculo institucional.
- CPF preservado somente para unicidade, sem exibição na listagem.
- Ativação e desativação com confirmação pelo popup estilizado do sistema.

## 13. Início da persistência MySQL

- Conexão local com MySQL 8 por SQLAlchemy e PyMySQL.
- Credenciais armazenadas somente em `instance/mysql.env`, fora do Git.
- Tabelas relacionais para municípios, instituições e usuários.
- Chaves estrangeiras entre instituição, município e usuário.
- Carga inicial idempotente dos dados demonstrativos.
- Comandos `init-db` e `db-status` para inicialização e diagnóstico.
- Migração posterior de currículo, questões, simulados e materiais.

## 14. Conteúdo enriquecido das questões

- Alternativas do simulado do aluno sempre em sequência vertical de A a D.
- Imagem opcional em PNG, JPG, JPEG ou WEBP, limitada a 2 MB.
- Pré-visualização e opção de remoção da imagem durante a edição.
- Aplicação de negrito a trechos do enunciado e das alternativas por botão ou
  marcação `**texto**`.
- Renderização do negrito com escape de HTML para preservar a segurança.
- Cronômetro regressivo no cabeçalho do simulado, preservado durante a tentativa.

## 15. Questões abertas e proteção da aplicação

- O editor permite escolher entre questão objetiva e questão aberta.
- Questões abertas apresentam um campo de texto amplo para a resposta do aluno.
- O professor ou coordenador pode registrar uma orientação de correção opcional,
  sem exibi-la ao aluno durante a tentativa.
- A entrega continua bloqueada se uma questão objetiva ou aberta estiver vazia.
- Respostas abertas aparecem no resultado como **aguardando correção**, sem
  pontuação automática.
- Durante a tentativa, a interface bloqueia impressão, cópia, recorte, colagem,
  arraste e menu de contexto no navegador.
- A tecla Print Screen gera um aviso e a perda de foco cobre o conteúdo com uma
  tela de privacidade.
- Essas medidas funcionam como barreiras no navegador; o sistema operacional não
  permite que uma página web garanta o bloqueio de capturas por ferramentas externas.

## 16. Solicitações de simulados e gestão das publicações

- O Professor pode editar título, descrição, matéria, assunto, turmas, texto e
  anexo das próprias publicações de revisão.
- A exclusão de publicação exige confirmação em popup estilizado.
- O Coordenador do Colégio inicia o simulado por uma solicitação e agenda somente após concluir a avaliação das questões.
- A ação **Solicitar simulado** é dividida em anos participantes, matérias e
  professores responsáveis.
- Cada matéria selecionada cria uma linha com seu nome à esquerda e um menu de
  professores à direita.
- O menu mostra somente professores ativos da própria instituição que possuem a
  matéria vinculada ao cadastro.
- O Professor recebe a solicitação, o prazo e as orientações da coordenação.
- A Coordenação do Instituto mantém uma visão geral das solicitações dos colégios.

## 17. Gestão de assuntos pelo professor

- O menu do Professor inclui **Meus assuntos**.
- A página apresenta somente as matérias vinculadas ao cadastro do professor.
- O Professor pode adicionar, editar e remover assuntos dessas matérias.
- O Professor não pode criar matérias nem gerenciar assuntos de disciplinas não
  vinculadas ao seu cadastro.
- O Coordenador do Colégio apenas consulta os assuntos e não recebe ações de
  criação, edição ou exclusão.
- A exclusão usa popup estilizado e é bloqueada quando o assunto já está associado
  a uma questão ou publicação de revisão.

## 18. Autoria e revisão do banco de questões

- O Professor acessa o banco e adiciona questões somente nas matérias vinculadas
  ao próprio cadastro.
- O Professor edita somente as questões de sua autoria.
- Coordenadores consultam as questões dentro do respectivo escopo, sem acesso às
  rotas de criação ou edição.
- O antigo botão **Editar** é substituído por **Solicitar revisão** nas visões das
  coordenações.
- A solicitação registra a orientação, o coordenador e o horário e fica visível
  para o professor responsável.
- Ao salvar a questão após uma solicitação, o estado passa para **Revisada**.

## 19. Fluxo colaborativo do simulado

- A Coordenação do Colégio seleciona os anos participantes, as matérias, um
  professor habilitado por matéria e o prazo de entrega.
- Cada Professor recebe a solicitação em uma caixa própria e pode enviar
  questões do banco pessoal, reutilizar questões do histórico ou criar uma nova.
- A Coordenação do Colégio avalia cada questão, podendo aprová-la ou solicitar
  revisão com uma orientação escrita em popup estilizado.
- A edição de uma questão com revisão pendente a devolve automaticamente à
  coordenação com o estado **Reenviada**.
- O agendamento fica bloqueado até que toda matéria tenha ao menos uma questão e
  todas as questões enviadas estejam aprovadas.
- Ao agendar, o sistema cria a aplicação somente para os anos selecionados e
  envia uma notificação interna aos alunos participantes.

## 20. Persistência operacional e correções

- O histórico da revisão registra os estados **Pendente**, **Em revisão**,
  **Revisada** e **Aprovada**, com responsável, data e orientação.
- O banco de questões permite filtrar itens por situação da revisão e o painel
  do Professor destaca pendências.
- Tentativas registram início, entrega, duração, tempo restante, respostas,
  pontuação e situação no MySQL.
- O navegador salva respostas durante o preenchimento e a página recupera a
  tentativa ativa após ser fechada.
- Questões abertas entram em **Correção pendente**; o Professor autor informa
  nota de 0 a 1, conceito opcional e comentário.
- Quando todas as respostas abertas são corrigidas, a tentativa muda para
  **Resultado disponível** e o Aluno recebe uma notificação.
- Imagens e anexos são gravados em pasta controlada, enquanto caminho, nome,
  formato e tamanho ficam registrados no banco.
- A exclusão ou substituição de uma publicação remove também seu arquivo físico
  e o registro correspondente.
- A central de avisos atende Aluno, Professor e coordenações e registra leitura.

As medidas que ainda exigem implementação antes de um ambiente real estão em
[Pendências de segurança](PENDENCIAS_SEGURANCA.md).

## 21. Relatórios de desempenho

- A Coordenação do Instituto inicia por uma visão consolidada de todas as escolas,
  com gráficos comparativos e ranking das médias.
- Cada escola possui uma página própria com média, frequência, faltas, quantidade
  de estudantes e evolução mensal.
- A navegação segue a hierarquia **escola → série → turma**, preservando o contexto
  em títulos, trilha de navegação e barra superior.
- O relatório de série compara suas turmas; o relatório de turma detalha os
  estudantes em ordem de desempenho.
- A Coordenação do Colégio entra diretamente no relatório da própria escola e não
  pode consultar outra instituição por endereço direto.
- Gráficos de linhas representam evolução no tempo. Gráficos de colunas comparam
  escolas, turmas e faltas.
- Cada gráfico conserva uma tabela equivalente para tecnologias assistivas.
- Resultados de tentativas concluídas alimentam a média quando disponíveis. Até a
  criação do diário de frequência, faltas e séries históricas permanecem como
  dados demonstrativos, com aviso visível na interface.
