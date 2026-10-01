# Diário de desenvolvimento

Este documento registra decisões, início e evolução da implementação do
frontend.

## 11 de setembro de 2026 - Início do planejamento

**Estado:** planejamento concluído para revisão; implementação ainda não
iniciada.

### Decisões registradas

- Primeira entrega limitada aos blocos 1 a 4.
- Projeto baseado em Flask, Jinja, CSS próprio e JavaScript modular.
- Login livre, com acesso permitido mesmo quando os campos estiverem vazios.
- Cinco atalhos de acesso rápido representarão os cinco perfis.
- Nome do produto: **Instituto Fabiana Pinto**.
- Paleta institucional: azul `#2D3D5F` e laranja `#B96121`.
- Direção visual educacional, acolhedora e sóbria.
- Interface em português brasileiro.
- Uso prioritário em computador, com adaptação para telas menores.
- Ações sem permissão serão ocultadas; ações condicionais serão desabilitadas
  com explicação.
- Professor não publica simulados.
- Coordenador do Instituto cria e publica simulados.
- Coordenador do Colégio agenda apenas para a própria escola.
- Conteúdo representa apenas material de estudo, sem entrega de tarefas.

### Próxima etapa

Iniciar o Bloco 1 após a aprovação do planejamento. Cada bloco deverá registrar
neste diário as telas criadas, decisões técnicas, verificações realizadas e
pendências encontradas.

## 11 de setembro de 2026 - Bloco 1 concluído

**Estado:** definição funcional e visual concluída; nenhum código da aplicação
foi iniciado.

### Entregas

- Arquitetura de informação e hierarquia acadêmica consolidadas.
- Mapa de rotas definido para acesso, início e estrutura acadêmica.
- Matriz de permissões definida para os cinco perfis.
- Sistema visual documentado com cores, tipografia, espaçamento, componentes,
  estados e regras responsivas.
- Dados fictícios planejados para os fluxos demonstrativos.
- Estados vazio, carregando, sucesso, erro, acesso condicionado e acesso restrito
  especificados.

### Decisões técnicas

- Rotas e componentes serão compartilhados entre perfis.
- O escopo será aplicado antes da montagem de menus, listas e ações.
- A fonte Nunito Sans será servida localmente, com fallback seguro.
- A faixa de contexto acadêmico será o elemento visual característico das telas
  internas.
- Listas administrativas priorizarão tabelas e agrupamentos claros em vez de uma
  grade de cartões repetitivos.

### Revisão da proposta visual

A direção inicial foi revisada para evitar a aparência de um painel genérico. A
faixa de contexto acadêmico passou a concentrar a identidade da experiência, e
o laranja institucional ficou reservado a ações e informações relevantes.

### Próxima etapa

Iniciar o Bloco 2, criando a fundação Flask e os componentes estruturais conforme
as definições aprovadas neste bloco.

## 11 de setembro de 2026 - Bloco 2 concluído

**Estado:** fundação Flask implementada e verificada.

### Implementação

- Aplicação organizada com fábrica, configuração e Blueprint principal.
- Templates Jinja separados em base, partials, macros, páginas e erros.
- Sistema de estilos dividido em tokens, base, componentes, layout e
  responsividade.
- Comportamento do menu móvel implementado com JavaScript sem framework.
- Dados demonstrativos isolados da camada de apresentação.
- Página inicial de fundação e catálogo navegável de componentes criados.
- Páginas de erro 403, 404 e 500 adicionadas.
- Dependências registradas em `requirements.txt` e `requirements-dev.txt`.

### Verificação

- Aplicação iniciada localmente com Flask 3.1.2.
- Dois testes automatizados executados com sucesso.
- Rotas `/`, `/componentes` e tratamento de página inexistente verificados.
- Layout desktop revisado em navegador.
- Breakpoint de 390 px verificado: navegação lateral recolhida e menu móvel
  funcional.
- Nenhum erro de console ou falha de renderização observado durante a revisão.

### Limite preservado

O login, a sessão por perfil e a navegação baseada em permissão não foram
antecipados. Esses fluxos pertencem ao Bloco 3.

### Próxima etapa

Iniciar o Bloco 3 com formulário livre, acessos rápidos, sessão demonstrativa e
navegação correspondente ao perfil ativo.

## 29 de setembro de 2026 - Bloco 3 concluído

**Estado:** acesso demonstrativo e estrutura principal implementados.

### Implementação

- Login livre, sem validação de usuário e senha.
- Perfil selecionável no formulário e cinco botões de acesso rápido.
- Sessão demonstrativa para Aluno, Professor, Coordenador do Colégio,
  Coordenador do Instituto e Administrador/T.I.
- Dashboard, menu lateral e resumo inicial adaptados ao perfil.
- Troca de perfil e encerramento da sessão.
- Rotas protegidas contra acesso sem sessão ou perfil sem permissão.
- Cabeçalho e menu móvel integrados ao layout compartilhado.

### Verificação

- Entrada com campos vazios validada.
- Cinco acessos rápidos exercitados por testes automatizados.
- Login e dashboard revisados visualmente no navegador.
- Navegação por teclado preservada por controles nativos e foco visível.

## 29 de setembro de 2026 - Bloco 4 concluído

**Estado:** estrutura acadêmica funcional implementada com dados em memória.

### Implementação

- Municípios, instituições, séries, turmas, alunos e professores relacionados.
- Busca textual, filtro por situação e paginação nas listas.
- Detalhes, vínculos relacionados, inclusão, edição e mudança de situação.
- Formulários compartilhados com opções contextualizadas por série e instituição.
- Escopo restrito à própria escola para o Coordenador do Colégio.
- Escopo restrito às turmas vinculadas para o Professor.
- Visualização do próprio registro para o Aluno.
- Gestão ampla para Coordenador do Instituto e Administrador/T.I.
- Ações indisponíveis ocultadas e ações condicionais desabilitadas com motivo.

### Verificação

- Testes automatizados cobrem login, perfis, escopo, acesso restrito, filtros,
  inclusão demonstrativa e páginas de erro.
- Login, dashboard, listagem e formulário revisados no navegador.
- Formulário revisado em viewport de 390 px.
- Nenhum erro ou aviso encontrado no console do navegador.

### Encerramento da primeira entrega

Os quatro blocos planejados estão concluídos. A aplicação oferece uma base
funcional para integrar autenticação, persistência e os módulos de avaliações em
uma próxima etapa.

## 29 de setembro de 2026 - Bloco 5 concluído

**Estado:** banco de questões funcional implementado com dados em memória.

### Implementação

- Módulo próprio para listar, consultar, incluir e editar questões.
- Busca por enunciado ou autor, filtros de operação e dificuldade e paginação.
- Questões classificadas por operação e nível, com quatro alternativas,
  gabarito e resolução esperada.
- Banco inicial restrito a **Matemática** e **Operações primárias**.
- Dezesseis questões cadastradas: quatro de soma, quatro de subtração, quatro de
  multiplicação e quatro de divisão.
- Professor autorizado a incluir e editar questões, sem permissão para publicar
  simulados.
- Coordenador do Colégio com acesso de consulta; Coordenador do Instituto e
  Administrador/T.I. com acesso de gestão.

### Verificação

- Cobertura automatizada confirmou disciplina, assunto, quantidade e presença
  equilibrada das quatro operações.
- Listagem, detalhes e formulário revisados no navegador.
- Listagem revisada em viewport de 390 px.
- Nenhum erro ou aviso encontrado no console do navegador.

## 29 de setembro de 2026 - Bloco 6 concluído

**Estado:** criação e gestão demonstrativa de simulados implementadas.

### Implementação

- Listagem com busca e filtro por situação, tela de detalhes e formulário de
  criação e edição.
- Composição de simulados por seleção de questões do banco.
- Configuração de título, modalidade, público, duração, data e instituições.
- Publicação reservada ao Coordenador do Instituto e ao Administrador/T.I.
- Agendamento permitido ao Coordenador do Colégio apenas para a própria escola.
- Professor mantido em modo de consulta, sem ação de publicação.
- Simulado de teste criado com oito questões de operações primárias, distribuídas
  igualmente entre soma, subtração, multiplicação e divisão.

### Verificação

- Testes automatizados cobrem a composição equilibrada do simulado, a proibição
  de criação pelo Professor, a publicação pelo Coordenador do Instituto e o
  limite institucional do agendamento pelo Coordenador do Colégio.
- Listagem, detalhes e formulário revisados no navegador.
- Detalhes do simulado revisados em viewport de 390 px.
- A suíte completa terminou com **16 testes aprovados** e nenhum erro no console
  do navegador.

### Estado ao final do Bloco 6

O frontend cobre acesso, estrutura acadêmica, banco de questões e gestão de
simulados. Os dados continuam temporários e são restaurados ao reiniciar o
servidor, preservando o planejamento de integração futura com o backend.

## 29 de setembro de 2026 - Ampliação de usuários e currículo

**Estado:** regras adicionais implementadas no frontend e nos dados em memória.

### Implementação

- Cadastro de município ampliado com código oficial e descrição do campo.
- Banco de questões reorganizado em três etapas: matéria, assunto e questões.
- Catálogo de matérias e assuntos criado com opções globais e institucionais.
- T.I. pode adicionar matérias, assuntos e questões.
- Coordenador do Instituto pode criar matérias globais e gerir professores de
  todas as instituições.
- Coordenador do Colégio pode criar matérias para a própria instituição e criar,
  editar e gerir seus professores.
- Cadastro de professor ampliado com CPF, e-mail e seleção múltipla de matérias
  aprovadas em menu suspenso.
- Alunos e professores podem ser filtrados por município e instituição nos
  perfis administrativos.
- CPF e e-mail são normalizados e verificados entre alunos e professores; dados
  duplicados bloqueiam novos cadastros e edições.
- Coordenação do Instituto e T.I. podem transferir professores para outra
  instituição; a transferência limpa os vínculos anteriores de turma.

### Verificação

- Testes adicionados para filtros institucionais, duplicidade de CPF/e-mail,
  escopo do catálogo, criação de professor, navegação do banco de questões e
  transferência.
- A suíte completa terminou com **24 testes aprovados**.
- Catálogo, banco de questões, filtros, formulário de professor e transferência
  revisados visualmente no navegador.

## 29 de setembro de 2026 - Restrição dos módulos de avaliação

**Estado:** visibilidade e escopo revisados conforme a regra mais recente.

### Alterações

- CPF removido das listas e páginas de detalhes de alunos e professores; o dado
  permanece nos formulários e na verificação de duplicidade.
- Banco de questões, simulados, matérias e assuntos removidos dos menus e painéis
  de Professor e T.I.
- As mesmas rotas retornam acesso restrito quando abertas diretamente por esses
  perfis.
- Coordenador do Instituto mantém acesso completo aos quatro módulos.
- Coordenador do Colégio pode criar e editar questões e matérias vinculadas à
  própria instituição, sem alterar itens globais ou de outras escolas.
- Simulados do Coordenador do Colégio são limitados aos que incluem sua escola;
  o perfil mantém somente a ação de agendamento dentro desse escopo.

### Verificação

- Testes de acesso direto, privacidade do CPF e escopo institucional adicionados.
- A suíte completa terminou com **28 testes aprovados**.

## 29 de setembro de 2026 - Simulados e revisão na área do aluno

**Estado:** fluxo do aluno concluído e integrado à navegação.

### Alterações

- Adicionados **Meus simulados** e **Assuntos de revisão** ao menu do Aluno.
- O aluno visualiza somente simulados liberados para sua instituição.
- A aplicação apresenta orientações, questões e alternativas sem revelar o
  gabarito antes do envio.
- Após responder, a tela mostra a pontuação e a revisão de cada questão.
- A biblioteca de revisão organiza os conteúdos por matéria e assunto.
- O assunto **Operações primárias** contém material de soma, subtração,
  multiplicação e divisão com exemplos.

### Verificação

- Fluxos de acesso, resposta e revisão cobertos por testes automatizados.
- A suíte completa terminou com **32 testes aprovados**.
- Páginas revisadas visualmente em computador e tela menor.

## 29 de setembro de 2026 - Bloqueio de respostas em branco

**Estado:** validação da entrega concluída.

### Alterações

- A entrega do simulado é interrompida quando existe qualquer questão sem
  resposta.
- Um popup informa os números de todas as questões pendentes.
- As questões em branco recebem destaque e a página retorna à primeira delas
  quando o aviso é fechado.
- As respostas já selecionadas são preservadas caso uma requisição incompleta
  chegue ao servidor.
- A mesma regra é validada no servidor para impedir entregas incompletas mesmo
  quando o JavaScript não está disponível.

### Verificação

- Adicionado teste automatizado para tentativa de entrega parcial.
- A suíte completa terminou com **33 testes aprovados**.

## 29 de setembro de 2026 - Postagens de revisão e padrão de popups

**Estado:** fluxo de publicação pelo professor implementado.

### Alterações

- Criado mural de materiais de revisão inspirado em postagens de turma.
- O Professor publica título, descrição, texto opcional e anexo opcional.
- Anexos aceitos: PDF, PNG, PPT e PPTX, limitados a 16 MB.
- A publicação pode ser destinada somente às turmas vinculadas ao professor.
- O Aluno visualiza apenas as postagens destinadas à sua turma.
- O aviso de questões em branco foi consolidado no componente visual reutilizável
  `site-dialog`.
- Registrada a regra de que todos os popups devem seguir a identidade visual do
  sistema e nunca usar diálogos nativos do navegador.

### Verificação

- Publicação em texto, anexo permitido, formato inválido e permissões cobertos
  por testes automatizados.
- A suíte completa terminou com **36 testes aprovados**.

## 29 de setembro de 2026 - Gestão de usuários por T.I.

**Estado:** módulo exclusivo de usuários concluído.

### Alterações

- Adicionada a aba **Usuários** ao menu e ao resumo inicial de T.I.
- A listagem pode ser ordenada de A a Z ou de Z a A.
- Adicionados filtros combináveis por município, instituição e cargo.
- T.I. pode cadastrar usuários com cargo e vínculo institucional.
- CPF e e-mail duplicados são bloqueados e o CPF permanece oculto na listagem.
- Ativação e desativação usam confirmação pelo componente visual `site-dialog`.

### Verificação

- Ordenação, filtros, cadastro, duplicidade, permissões e alteração de status
  cobertos por testes automatizados.
- A suíte completa terminou com **39 testes aprovados**.

## 29 de setembro de 2026 - Primeira etapa do banco MySQL

**Estado:** integração implementada; ativação local depende da autenticação
administrativa do MySQL instalado na máquina.

### Alterações

- Adicionados SQLAlchemy, Flask-SQLAlchemy e PyMySQL.
- Criadas tabelas relacionais para municípios, instituições e usuários.
- Instituições e usuários usam chaves estrangeiras para seus vínculos.
- Carga inicial e sincronização de compatibilidade executadas de forma
  idempotente.
- Criados os comandos `init-db` e `db-status`.
- Criado configurador seguro que gera um usuário dedicado e grava a senha fora
  do repositório.
- Documentado o escopo migrado e o roteiro das próximas etapas.

### Verificação

- Persistência da base administrativa validada em banco isolado pela suíte.
- A suíte completa terminou com **40 testes aprovados**.

### Ajuste de navegação

- A página técnica **Componentes** foi removida do menu e do painel inicial de
  T.I.; a rota permanece disponível apenas como referência interna.

## 29 de setembro de 2026 - Imagens e ênfase nas questões

**Estado:** editor e aplicação do simulado atualizados.

### Alterações

- Alternativas do aluno organizadas verticalmente de A a D em todas as telas.
- Editor com imagem opcional em PNG, JPG, JPEG ou WEBP.
- Limite de 2 MB validado no servidor e informado no formulário.
- Botão de negrito adicionado ao enunciado e às quatro alternativas.
- Marcação de negrito renderizada no banco, no simulado e na revisão do
  resultado, com HTML do usuário escapado.

### Verificação

- Upload, limite de tamanho, exibição para o aluno, layout vertical e segurança
  da formatação cobertos por testes automatizados.
- A suíte completa terminou com **44 testes aprovados**.

### Correção visual do enunciado

- A regra do círculo numérico foi limitada ao primeiro elemento do cabeçalho.
- O enunciado voltou a usar texto escuro e ocupa toda a largura disponível ao
  lado da numeração da questão.

### Cronômetro do simulado

- Adicionado cronômetro regressivo no canto superior direito da aplicação.
- O componente usa formato elíptico, azul institucional e números brancos em
  peso forte.
- O prazo da tentativa é preservado em atualizações da página e removido após
  uma entrega completa.

## 30 de setembro de 2026 - Questões abertas e proteção do simulado

**Estado:** fluxo implementado e validado.

### Alterações

- Adicionado tipo de questão no editor: objetiva ou aberta.
- Questões abertas recebem resposta digitada pelo aluno e orientação opcional
  para a correção posterior.
- A validação de questões em branco passou a abranger também os campos de texto.
- O resultado separa a pontuação automática das questões objetivas e marca as
  respostas abertas como **aguardando correção**.
- Durante a tentativa, foram bloqueados impressão, copiar, recortar, colar,
  arrastar conteúdo e abrir o menu de contexto.
- A tecla Print Screen exibe um popup estilizado e a perda de foco ativa uma
  tela de privacidade sobre as questões.

### Verificação

- Criação, preenchimento obrigatório e resultado pendente de questão aberta
  cobertos por teste automatizado.
- Proteções e elementos de privacidade cobertos por teste automatizado.
- A suíte completa terminou com **47 testes aprovados**.

### Limite técnico

- Navegadores não conseguem impedir de forma absoluta capturas feitas pelo
  sistema operacional ou por outro dispositivo. A implementação adiciona as
  barreiras disponíveis dentro da página e deixa essa limitação documentada.

## 30 de setembro de 2026 - Solicitação de simulados e gestão de publicações

**Estado:** fluxos implementados e validados.

### Alterações

- Professores passaram a editar e excluir as próprias publicações de revisão.
- A edição preserva o anexo atual, permite substituí-lo ou removê-lo.
- A exclusão usa o componente visual de confirmação do sistema.
- A opção do Coordenador do Colégio foi renomeada para **Solicitar simulado**.
- O formulário foi dividido em anos participantes, matérias e professores.
- Cada matéria exige um professor ativo da própria escola que tenha a disciplina
  vinculada ao cadastro.
- O agendamento direto pelo Coordenador do Colégio foi removido.
- A Coordenação do Instituto passou a visualizar os pedidos enviados.

### Verificação

- Edição e exclusão de publicação cobertas por teste automatizado.
- Solicitação válida, bloqueio de professor incompatível e remoção do acesso de
  agendamento cobertos por testes automatizados.
- A suíte completa terminou com **49 testes aprovados**.

## 30 de setembro de 2026 - Assuntos administrados pelo professor

**Estado:** permissão implementada e validada.

### Alterações

- Adicionada a aba **Meus assuntos** ao menu e ao painel do Professor.
- O catálogo do perfil mostra somente as matérias vinculadas ao professor.
- Foram adicionadas ações para criar, editar e excluir assuntos.
- Todas as rotas validam o vínculo da matéria no servidor.
- A criação de matérias continua indisponível ao Professor.
- A exclusão usa popup estilizado e preserva assuntos vinculados a questões ou
  materiais existentes.

### Verificação

- Criação, edição, exclusão, bloqueio por matéria e proteção de assunto em uso
  cobertos por testes automatizados.
- A suíte completa terminou com **51 testes aprovados**.

## 30 de setembro de 2026 - Questões submetidas pelos professores

**Estado:** responsabilidades do banco de questões reorganizadas.

### Alterações

- O Professor passou a acessar o banco de questões pelo menu e painel inicial.
- Criação limitada às matérias do professor e à instituição do seu cadastro.
- Edição limitada às questões da própria autoria.
- Coordenadores permanecem com consulta dentro do escopo permitido, sem acesso a
  criação ou edição.
- O botão de edição das coordenações foi substituído por **Solicitar revisão**.
- A solicitação usa popup estilizado e registra orientação, solicitante e horário.
- O Professor visualiza a orientação recebida; após editar, a questão fica marcada
  como **Revisada**.

### Verificação

- Autoria, instituição, bloqueio das coordenações, solicitação e recebimento da
  revisão cobertos por testes automatizados.
- Imagens, negrito e questões abertas foram revalidados sob o perfil Professor.
- A suíte completa terminou com **54 testes aprovados**.

### Ajuste de responsabilidade dos assuntos

- Removidas do Coordenador do Colégio as ações de adicionar, editar e excluir
  assuntos.
- O perfil permanece com consulta ao catálogo e gestão das matérias da própria
  instituição.
- A manutenção de assuntos fica com os professores vinculados às respectivas
  matérias, com bloqueio também nas rotas diretas.

## 30 de setembro de 2026 - Fluxo colaborativo de simulados

**Estado:** ciclo completo implementado e validado.

### Alterações

- A solicitação da Coordenação do Colégio agora exige um prazo para os
  professores responsáveis.
- O Professor recebeu uma caixa de solicitações e pode enviar questões do banco,
  reutilizar o histórico ou criar uma nova questão dentro do pedido.
- A Coordenação do Colégio pode aprovar cada entrega ou solicitar revisão por um
  popup alinhado à identidade visual.
- A edição de uma questão devolvida atualiza sua entrega para **Reenviada**.
- O agendamento é liberado somente quando todas as matérias possuem questões e
  todas as entregas estão aprovadas.
- O simulado agendado respeita os anos selecionados e gera notificações internas
  apenas para os alunos participantes.

### Verificação

- O ciclo solicitação, bloqueio antecipado, envio, revisão, reenvio, aprovação,
  agendamento e notificação foi coberto por teste integrado.
- A criação de uma questão nova dentro da solicitação também foi validada.
- A suíte completa terminou com **57 testes aprovados**.

## 30 de setembro de 2026 - Persistência de tentativas, arquivos e correções

**Estado:** etapa implementada e validada.

### Alterações

- Revisões de questões receberam histórico persistente, filtro, aviso no painel
  e estados Pendente, Em revisão, Revisada e Aprovada.
- A Coordenação passou a aprovar explicitamente a revisão concluída.
- Tentativas agora persistem início, entrega, respostas, tempo restante,
  situação e pontuação.
- O preenchimento é salvo automaticamente e recuperado quando a página é aberta novamente.
- Simulados podem bloquear uma segunda tentativa.
- Professores receberam uma fila para corrigir respostas abertas com nota,
  conceito e comentário para o aluno.
- O resultado combina a pontuação objetiva e as notas das respostas abertas.
- Imagens e anexos passaram a usar armazenamento local controlado e metadados no MySQL.
- A exclusão de uma publicação remove o arquivo físico e seu registro.
- A central de notificações foi ampliada para todos os perfis e principais eventos.
- As pendências de segurança foram consolidadas em documento próprio.

### Verificação

- Fluxos de revisão, tentativa recuperável, entrega única, correção aberta,
  resultado final, armazenamento, remoção e autorização de arquivos foram testados.
- O MySQL local respondeu e contém as novas tabelas operacionais.
- A suíte completa terminou com **60 testes aprovados**.

## 30 de setembro de 2026 - Relatórios das escolas

**Estado:** módulo implementado e validado.

### Alterações

- A Coordenação do Instituto recebeu uma visão consolidada das escolas, com
  comparação de médias, faltas e ranking institucional.
- A Coordenação do Colégio passou a acessar diretamente o desempenho da própria
  escola, sem permissão para abrir relatórios de outras instituições.
- A navegação dos relatórios foi organizada em escola, série e turma.
- Foram adicionados gráficos responsivos de linhas e colunas, cartões de
  indicadores, ranking e detalhamento de estudantes.
- Médias de tentativas concluídas são consideradas quando existem; frequência,
  faltas e histórico mensal permanecem demonstrativos e identificados na tela.
- O menu lateral e os painéis iniciais das coordenações receberam atalhos para o
  novo módulo.

### Verificação

- Foram cobertos o comparativo institucional, o isolamento da escola, o acesso
  por série e turma e o bloqueio para perfis sem permissão.
- A suíte completa terminou com **64 testes aprovados**.

## 1º de outubro de 2026 - Migração integral para o MySQL local

**Estado:** domínios funcionais conectados e validados no banco local.

### Alterações

- Estrutura acadêmica, matérias, assuntos, questões, simulados, solicitações e
  publicações receberam tabelas próprias e operações persistentes.
- Alunos e professores foram vinculados às contas de usuário; transferências,
  alterações cadastrais e desativações agora sincronizam os dois registros.
- A carga inicial passou a criar somente tabelas vazias e a aplicação recarrega
  todas as coleções a partir do banco em cada inicialização.
- Revisões, aprovações, anexos, agendamentos e edições que antes alteravam apenas
  o objeto exibido agora também são gravados imediatamente.
- Os indicadores demonstrativos dos relatórios foram movidos para o MySQL e uma
  escola sem alunos passa a apresentar indicadores zerados.
- O servidor passou a rejeitar salvamento e entrega depois do término do tempo,
  além de recusar prazos e datas de agendamento anteriores ao dia atual.
- Foi adicionada limpeza de metadados e arquivos sem questão ou publicação
  proprietária; o arquivo órfão identificado na análise foi removido.

### Verificação

- A suíte completa terminou com **65 testes aprovados**, incluindo reinicialização
  sobre um banco persistente.
- A inicialização foi executada contra o MySQL local e confirmou as tabelas e a
  carga inicial dos domínios migrados.
- As restrições de segurança que dependem de autenticação real e infraestrutura
  permanecem registradas em `PENDENCIAS_SEGURANCA.md`.

# 1º de outubro de 2026 - Carrosséis de correções do professor

- A aba **Correções** passou a apresentar as solicitações pendentes em um carrossel.
- Foi incluído um segundo carrossel com o histórico das respostas já corrigidas,
  exibindo aluno, simulado, quantidade de respostas, média e data da correção.
- A navegação oferece controles anterior e próximo, posição atual, rolagem por
  toque e suporte às setas do teclado.
- O histórico é alimentado pelas notas persistidas no MySQL e permite reabrir a
  correção para consultar notas, conceitos e comentários.

# 1º de outubro de 2026 - Detalhamento dos indicadores escolares

- Frequência, faltas e quantidade de estudantes passaram a abrir relações
  nominais, preservando o recorte de escola, série e turma.
- Foi criado um resumo demonstrativo de frequência por estudante no MySQL, com
  percentual, faltas e situação do último registro.
- O cartão de período letivo passou a abrir o histórico da escola, inicialmente
  com o ano de 2026.
- As novas páginas mantêm o aviso de que frequência e faltas serão substituídas
  pelos dados do futuro diário de frequência.

# 1º de outubro de 2026 - Limite de questões nas solicitações

- A Coordenação do Colégio passou a definir a quantidade de questões para cada
  matéria e professor da solicitação.
- A página recebida pelo Professor não oferece mais a criação direta de questão;
  novos itens devem ser cadastrados primeiro no **Banco de questões**.
- A seleção reúne banco e histórico e mantém o limite solicitado. Quando o
  Professor escolhe outra questão com a seleção completa, a nova substitui
  automaticamente a última marcada, sem interromper o fluxo com um popup.
- O servidor exige a quantidade exata antes de registrar qualquer entrega e o
  agendamento só é liberado quando todos os totais pedidos forem aprovados.

# 1º de outubro de 2026 - Destaque de notificações não lidas

- O atalho de notificações do cabeçalho recebeu um sino maior e uma área de
  clique ampliada.
- Avisos não lidos agora exibem um contador numérico em laranja, com contraste,
  borda e sombra para não passarem despercebidos pelo Professor.
- O contador mostra até **99+** e desaparece quando a central de notificações é
  aberta e os avisos são marcados como lidos.

# 1º de outubro de 2026 - Refinamento visual integral com Impeccable

- O frontend recebeu uma revisão completa de identidade, hierarquia,
  consistência, interação e responsividade sem alterar as permissões ou os
  fluxos funcionais existentes.
- A direção de **caderno institucional** passou a usar superfícies em marfim,
  azul como estrutura e laranja como marcação, preservando a paleta aprovada.
- A navegação lateral foi agrupada por tarefa para cada perfil e recebeu um
  conjunto único de ícones SVG lineares.
- Cabeçalhos, formulários, filtros, botões, tabelas, estados vazios, avisos,
  simulados e relatórios foram alinhados aos mesmos tokens e estados visuais.
- O painel inicial ganhou melhor aproveitamento do espaço e leitura mais rápida
  das áreas de trabalho.
- Em telas menores, o menu recolhido deixa de receber foco por teclado e devolve
  o foco ao botão de abertura quando é fechado.
- A revisão foi conferida em desktop e em uma largura de **390 px**.
- A suíte completa terminou com **68 testes aprovados** e o JavaScript principal
  passou pela verificação de sintaxe.

# 1º de outubro de 2026 - Biblioteca de materiais por matéria e assunto

- As áreas de materiais do Professor e do Aluno passaram a apresentar uma
  hierarquia visível de **matéria**, **assunto** e **publicações**.
- Um índice no início da página permite acessar rapidamente cada matéria e exibe
  quantos assuntos e materiais estão disponíveis.
- O cadastro do Professor reforça a classificação obrigatória, filtra os
  assuntos pela matéria selecionada e oferece acesso direto a **Meus assuntos**.
- Os vínculos já persistidos no MySQL foram reutilizados, sem alteração da
  estrutura do banco ou perda de publicações existentes.
- A suíte completa terminou com **70 testes aprovados** após a mudança.

# 1º de outubro de 2026 - Experiência visual do Aluno

- O início do Aluno recebeu uma apresentação própria, atalhos inteiros clicáveis
  e chamadas de ação mais evidentes.
- Simulados, orientações, notificações, materiais e resultados passaram a usar
  cabeçalhos e botões coerentes com essa experiência.
- A prova ganhou um indicador persistente de questões respondidas, atualizado a
  cada marcação ou texto digitado.
- Foram adicionados movimentos breves em cartões e controles, com desativação
  automática quando o dispositivo solicita redução de movimento.
- A disposição foi conferida no navegador em tela compacta, inclusive durante a
  seleção de respostas, e a suíte terminou com **71 testes aprovados**.
