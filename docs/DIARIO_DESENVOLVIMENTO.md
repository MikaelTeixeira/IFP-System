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
