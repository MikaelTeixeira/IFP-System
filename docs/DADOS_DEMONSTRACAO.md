# Dados de demonstração

## Objetivo

Fornecer conteúdo coerente para os fluxos dos blocos 3 e 4 sem banco de dados.
Os dados abaixo são fictícios e não representam pessoas reais.

## Estrutura acadêmica inicial

### Municípios

- Fortaleza.
- Caucaia.
- Maracanaú.

### Instituições

- Escola Horizonte - Fortaleza.
- Colégio Caminhos - Fortaleza.
- Escola Lagoa Azul - Caucaia.
- Centro Educacional Girassol - Maracanaú.

### Séries e turmas

- 7º ano: turmas A e B.
- 8º ano: turmas A e B.
- 9º ano: turmas A, B e C.

Cada instituição receberá somente parte dessas turmas, de modo que os filtros e
estados vazios possam ser demonstrados.

## Pessoas fictícias

- Alunos terão nome completo, matrícula demonstrativa, turma, situação e data de
  ingresso.
- Professores terão nome completo, disciplinas, turmas vinculadas e situação.
- Coordenadores terão instituição ou instituto associado.
- O perfil de T.I. não ficará associado a uma única escola.

Serão usados nomes variados e claramente fictícios. CPF, endereço residencial,
telefone e outros dados pessoais desnecessários não farão parte do protótipo.

## Perfis de acesso rápido

| Perfil | Identidade demonstrativa | Escopo inicial |
| --- | --- | --- |
| Aluno | Ana Clara Souza | Próprio cadastro e início |
| Professor | Rafael Lima | Turmas vinculadas na Escola Horizonte |
| Coord. Colégio | Beatriz Nogueira | Escola Horizonte |
| Coord. Instituto | Helena Martins | Todo o Instituto Fabiana Pinto |
| T.I. | Suporte IFP | Todo o ambiente demonstrativo |

## Comportamento durante a sessão

- Inclusões, edições e mudanças de estado são gravadas no MySQL local.
- O estado é restaurado das tabelas quando o servidor reinicia.
- Filtros e paginação usam a cópia carregada do banco e mantida em sincronia após cada alteração.
# Relatórios

As médias dos relatórios usam resultados concluídos do banco quando o recorte
possui tentativas disponíveis. Na ausência deles, a interface usa uma base
demonstrativa estável para preservar a navegação. Frequência, faltas e evolução
mensal também são demonstrativas até a implementação de um diário de frequência.
