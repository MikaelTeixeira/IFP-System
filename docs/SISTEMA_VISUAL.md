# Sistema visual

## Conceito

A interface combina a organização de um ambiente institucional com sinais
visuais acolhedores ligados ao cotidiano escolar. A personalidade virá da cor,
da tipografia e de uma faixa contextual que acompanha a navegação acadêmica.
Ela não dependerá de uma coleção de cartões iguais.

## Tokens de cor

### Institucionais

| Token | Valor | Uso |
| --- | --- | --- |
| `brand-navy-900` | `#1D2942` | Texto de forte contraste e navegação ativa |
| `brand-navy-700` | `#2D3D5F` | Azul institucional fornecido |
| `brand-navy-500` | `#526484` | Ícones e textos secundários |
| `brand-navy-100` | `#E7EAF0` | Fundos contextuais e divisores |
| `brand-orange-700` | `#914713` | Estado pressionado e contraste em fundo claro |
| `brand-orange-500` | `#B96121` | Laranja institucional fornecido |
| `brand-orange-100` | `#F7E8DD` | Destaques suaves e seleção |

### Neutros e estados

| Token | Valor | Uso |
| --- | --- | --- |
| `surface-page` | `#F6F7F9` | Fundo geral |
| `surface-panel` | `#FFFFFF` | Superfícies principais |
| `text-primary` | `#202735` | Texto corrido |
| `text-muted` | `#667085` | Apoio e metadados |
| `border-default` | `#D8DDE6` | Bordas e divisores |
| `state-success` | `#277454` | Confirmações |
| `state-warning` | `#9A6512` | Atenção |
| `state-danger` | `#A33A3A` | Erro ou ação destrutiva |
| `focus-ring` | `#D47A35` | Foco visível sobre fundos claros |

O laranja institucional não será usado para textos pequenos sobre fundo branco
quando o contraste for insuficiente. Nessas situações será usada a variação
`brand-orange-700`.

## Tipografia

- **Família principal:** `Nunito Sans`, com `Arial` e `sans-serif` como fallback.
- **Títulos:** pesos 700 e 800, com entrelinha compacta.
- **Texto e controles:** pesos 400, 600 e 700.
- **Escala:** 14, 16, 18, 22, 28 e 36 px.
- **Comprimento de leitura:** até 72 caracteres em textos explicativos.

Nunito Sans oferece formas acolhedoras sem perder a clareza necessária para
listas, filtros e tarefas administrativas. A fonte deverá ser servida localmente
para a aplicação não depender de uma conexão externa.

## Espaçamento e forma

- Unidade base de espaçamento: 4 px.
- Espaçamentos principais: 8, 12, 16, 24, 32 e 48 px.
- Raio pequeno: 6 px para campos e controles.
- Raio médio: 10 px para painéis e mensagens.
- Sombras reservadas a menus flutuantes, diálogos e elementos elevados.
- Listas administrativas usarão linhas e agrupamentos, evitando transformar cada
  registro em um cartão isolado.

## Elemento característico

A navegação acadêmica terá uma **faixa de contexto** que mostra a posição do
usuário na estrutura do instituto, por exemplo:

```text
Fortaleza  /  Escola Horizonte  /  9º ano  /  Turma B
```

A faixa usa azul institucional, detalhes laranja e nomes legíveis. Ela serve de
orientação, filtro e confirmação de escopo, especialmente para coordenadores.

## Componentes compartilhados

| Componente | Uso |
| --- | --- |
| Cabeçalho | Marca, acesso ao perfil, avisos e ação de menu em telas menores |
| Navegação lateral | Módulos permitidos e indicação da seção ativa |
| Faixa de contexto | Hierarquia e escopo acadêmico atual |
| Cabeçalho de página | Título, explicação curta e ação principal |
| Breadcrumb | Retorno dentro da hierarquia |
| Barra de filtros | Busca e filtros relevantes para a lista |
| Tabela responsiva | Listas administrativas e ações por registro |
| Lista compacta | Conteúdo simples em telas menores |
| Campo de formulário | Rótulo, ajuda, controle e mensagem de estado |
| Botão | Primário, secundário, discreto e destrutivo |
| Tag de estado | Ativo, inativo, pendente e condicionado |
| Mensagem contextual | Informação, sucesso, atenção e erro |
| Menu de ações | Ações secundárias de um registro |
| Diálogo de confirmação | Confirmações de mudanças relevantes |
| Paginação | Navegação em coleções mockadas |
| Estado vazio | Explicação e próxima ação disponível |
| Esqueleto de carregamento | Simulação coerente de conteúdo sendo carregado |

### Regra obrigatória para popups

Todo popup deve usar o componente visual `site-dialog` e seguir a identidade do
Instituto Fabiana Pinto. Não serão usados `alert`, `confirm` ou `prompt` nativos
do navegador.

- fundo branco, borda superior de estado e sombra de elevação;
- fundo da página escurecido enquanto o diálogo estiver aberto;
- título, explicação direta e ações com os botões compartilhados do sistema;
- variações `warning`, `success`, `danger` e informativa;
- foco de teclado mantido no diálogo, fechamento acessível e adaptação para
  telas menores;
- laranja para atenção, verde para sucesso, vermelho para perigo e azul
  institucional para informação.

## Estados obrigatórios

### Vazio

Explica o que pertence à área e oferece uma ação quando o perfil tiver permissão.
Exemplo: **Nenhuma turma encontrada.** Ajuste os filtros ou cadastre uma turma.

### Carregando

Preserva a estrutura aproximada da tela com esqueletos discretos. Não bloqueia o
cabeçalho nem a navegação.

### Sucesso

Confirma a ação com o mesmo verbo usado no botão. Exemplo: botão **Salvar turma**
e retorno **Turma salva**.

### Erro

Informa o problema e a próxima ação possível. Erros em campos ficam próximos ao
controle; erros de página aparecem em uma mensagem contextual.

### Acesso condicionado

Mantém a ação visível e desabilitada, com explicação acessível por texto. Exemplo:
**Ativação indisponível para esta escola.**

### Acesso restrito

Exibe uma página própria, identifica que o perfil atual não possui acesso e
oferece retorno ao início ou ao nível anterior permitido.

## Responsividade

- Desktop a partir de 1024 px: navegação lateral persistente e tabelas completas.
- Tablet entre 768 e 1023 px: navegação recolhível e ações condensadas.
- Celular abaixo de 768 px: painel de navegação, filtros empilhados e listas
  adaptadas para evitar rolagem horizontal sempre que possível.

## Acessibilidade mínima

- Foco visível em todos os controles.
- Navegação completa por teclado.
- Contraste compatível com WCAG AA para textos e controles essenciais.
- Rótulos explícitos em formulários.
- Ícones decorativos ignorados por leitores de tela.
- Estados nunca comunicados apenas por cor.
- Respeito à preferência de movimento reduzido.

## Autocrítica da direção

A primeira proposta poderia resultar em um painel administrativo genérico se a
interface fosse composta por muitos cartões arredondados e métricas decorativas.
Por isso, a direção foi ajustada para usar listas estruturadas, superfícies mais
quietas e a faixa de contexto acadêmico como elemento visual característico. O
laranja será reservado a decisões e estados importantes, evitando excesso de
destaques.
