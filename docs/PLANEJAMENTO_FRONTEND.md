# Planejamento do frontend

## 1. Objetivo

Construir um frontend funcional para o **Instituto Fabiana Pinto**, com Flask,
dados fictícios e navegação completa. Nesta etapa não haverá banco de dados,
autenticação real nem validação de credenciais.

A primeira entrega contempla somente os **blocos 1 a 4**. Os demais módulos do
board funcional permanecem fora do escopo desta etapa.

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
- **Persistência:** nenhuma nesta etapa; dados alterados podem ser restaurados ao
  reiniciar a aplicação.

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

- O professor pode consultar e trabalhar com questões conforme a permissão do
  módulo, mas **não publica simulados**.
- O Coordenador do Instituto pode criar e publicar simulados.
- O Coordenador do Colégio pode agendar simulados somente para a própria escola.
- A área de conteúdo representa materiais de estudo; não haverá entrega de
  tarefas.
- Ações totalmente indisponíveis para um perfil ficarão ocultas.
- Ações condicionais permanecerão visíveis e desabilitadas, acompanhadas do
  motivo.

## 6. Blocos da primeira entrega

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

**Estado:** não iniciado.

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

### Bloco 3 - Acesso e estrutura principal

**Estado:** não iniciado.

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

### Bloco 4 - Estrutura acadêmica

**Estado:** não iniciado.

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

## 7. Ordem de execução

Os blocos serão executados sequencialmente. Cada bloco passará por revisão
visual e funcional antes do início do seguinte. Correções estruturais descobertas
em um bloco serão resolvidas antes de ampliar o escopo.

## 8. Fora do escopo atual

- Banco de dados e migrações.
- Autenticação, recuperação de senha e autorização reais.
- Validação de credenciais e integrações externas.
- Banco de questões completo.
- Criação, publicação e aplicação de simulados.
- Prova remota, QR Code, cartões-resposta, scanner e OMR.
- Correção, analytics, conteúdo e gamificação.

Esses itens poderão ser planejados em uma etapa posterior sem alterar a base de
componentes e permissões criada nos quatro primeiros blocos.
