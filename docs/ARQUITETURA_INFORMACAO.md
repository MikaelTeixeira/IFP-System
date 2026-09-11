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

Os formulários de edição usarão o sufixo `/editar`. Exclusões, ativações e
mudanças de vínculo serão ações simuladas, submetidas por `POST`, sem persistência
após o reinício da aplicação.

## Navegação por perfil

### Aluno

- Início.
- Acesso ao próprio perfil.
- Nenhum item administrativo da estrutura acadêmica.

### Professor

- Início.
- Turmas às quais está vinculado.
- Alunos dessas turmas em modo de consulta.
- Próprio perfil.

### Coordenador do Colégio

- Início.
- Instituição atual em modo de consulta e edição permitida.
- Séries, turmas, alunos e professores da própria escola.
- Nenhum acesso a outra instituição.

### Coordenador do Instituto

- Início.
- Municípios, instituições, séries, turmas, alunos e professores.
- Criação e edição dentro do instituto.

### Administrador/T.I.

- Início.
- Toda a estrutura acadêmica.
- Ações administrativas simuladas.
- Indicação visual de ações executadas como override.

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

