# Matriz de rotas e permissões

## Legenda

- **Gerencia:** lista, cria, edita e executa ações disponíveis.
- **Consulta:** visualiza dados dentro do próprio escopo.
- **Próprio:** visualiza somente o registro associado à sessão.
- **Oculto:** rota e item de navegação não são apresentados.

## Permissões da primeira entrega

| Área | Aluno | Professor | Coord. Colégio | Coord. Instituto | T.I. |
| --- | --- | --- | --- | --- | --- |
| Início | Próprio | Consulta | Consulta | Consulta | Consulta |
| Municípios | Oculto | Oculto | Oculto | Gerencia | Gerencia |
| Instituições | Oculto | Oculto | Consulta da própria | Gerencia | Gerencia |
| Séries | Oculto | Consulta vinculada | Gerencia na própria | Gerencia | Gerencia |
| Turmas | Oculto | Consulta vinculada | Gerencia na própria | Gerencia | Gerencia |
| Alunos | Próprio | Consulta vinculada | Gerencia na própria | Gerencia | Gerencia |
| Professores | Oculto | Próprio | Gerencia na própria | Gerencia | Gerencia |
| Vínculos acadêmicos | Oculto | Consulta vinculada | Gerencia na própria | Gerencia | Gerencia |
| Ativar/desativar usuário | Oculto | Oculto | Condicional na própria | Gerencia | Gerencia/override |

## Comportamento das ações

| Situação | Apresentação |
| --- | --- |
| Perfil não possui a função | Ação oculta |
| Perfil pode receber a função por política | Ação desabilitada com explicação |
| Registro está fora do escopo | Registro não aparece na lista e a rota retorna acesso negado |
| Ação permitida | Ação visível e habilitada |
| Ação de T.I. fora do fluxo comum | Ação identificada como administrativa e confirmada antes da execução |

## Acesso direto a rotas

O menu não será usado como única barreira. Ao abrir uma URL diretamente, a
aplicação verificará a sessão demonstrativa e o escopo do perfil. Uma tentativa
fora do escopo exibirá uma página de acesso restrito com caminho para retornar.

