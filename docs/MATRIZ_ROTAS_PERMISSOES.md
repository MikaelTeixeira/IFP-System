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
| Usuários do sistema | Oculto | Oculto | Oculto | Oculto | Gerencia |
| Matérias | Oculto | Consulta as próprias | Gerencia na própria instituição | Gerencia globais | Oculto |
| Assuntos | Oculto | Gerencia nas próprias matérias | Consulta | Gerencia globais | Oculto |
| Banco de questões | Oculto | Cria e edita as próprias | Consulta e solicita revisão na própria instituição | Consulta todas e solicita revisão | Oculto |
| Revisão de questões | Oculto | Revisa as próprias solicitações | Solicita e aprova na própria instituição | Solicita e aprova em todo o instituto | Oculto |
| Simulados administrativos | Oculto | Responde solicitações atribuídas | Solicita, avalia e agenda na própria instituição | Cria, edita, publica e consulta solicitações | Oculto |
| Meus simulados | Responde os liberados para sua instituição e ano | Oculto | Oculto | Oculto | Oculto |
| Notificações de simulados | Consulta as próprias | Oculto | Envia ao agendar | Consulta | Oculto |
| Materiais de revisão | Consulta os destinados à sua turma | Publica, edita e exclui os próprios | Oculto | Oculto | Oculto |
| Correção de respostas abertas | Consulta o próprio resultado | Corrige respostas das próprias questões | Consulta futura | Consulta futura | Oculto |
| Transferir professor | Oculto | Oculto | Oculto | Entre instituições | Entre instituições |
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

## Regras de identidade e vínculo

- CPF é comparado apenas pelos dígitos, independentemente da pontuação digitada.
- E-mail é comparado sem diferença entre letras maiúsculas e minúsculas.
- Um CPF ou e-mail já usado por aluno ou professor bloqueia um novo cadastro.
- O CPF não aparece em listagens, detalhes ou resumos; fica restrito aos
  formulários de criação e edição e à verificação de duplicidade.
- As disciplinas do professor vêm do catálogo de matérias disponível para sua
  instituição.
- O Coordenador do Colégio cria e edita professores somente na própria
  instituição.
- Ao transferir um professor, os vínculos de turma anteriores são removidos para
  impedir a permanência de relações com a instituição de origem.
- O banco de questões aceita Professor e coordenações; simulados administrativos
  continuam restritos aos dois perfis de coordenação.
- O Professor cria questões nas próprias matérias e edita somente as questões de
  sua autoria.
- Coordenadores não criam nem editam questões. Eles consultam o banco e enviam
  solicitações de revisão ao professor responsável.
- O Professor consulta as matérias vinculadas ao cadastro e pode criar, editar e
  remover assuntos apenas dentro delas.
- O Coordenador do Colégio consulta os assuntos, mas não pode adicionar, editar
  ou excluir; essa responsabilidade pertence ao professor da matéria.
- Um assunto vinculado a uma questão ou material não pode ser excluído.
- O Coordenador do Colégio não usa a criação direta nem publica simulados. Ele
  solicita questões, avalia as entregas e agenda o resultado aprovado para a
  própria instituição.
- Cada professor indicado precisa ter a matéria vinculada ao seu cadastro.
- O Professor responde somente às matérias que lhe foram atribuídas, escolhendo
  uma questão do banco, do histórico ou criando uma nova.
- O agendamento exige ao menos uma questão por matéria e aprovação de todas as
  entregas; somente os alunos dos anos participantes recebem a notificação.
- O professor edita e exclui somente as publicações de revisão que criou.
- Tentativas e respostas pertencem ao aluno da sessão; depois da entrega, uma
  nova tentativa é bloqueada quando o simulado estiver configurado como único.
- O Professor corrige apenas respostas ligadas a questões de sua autoria.
- Anexos e imagens exigem autenticação e vínculo autorizado antes do acesso.
# Relatórios de desempenho

| Rota | Professor | Coord. Colégio | Coord. Instituto | T.I. |
| --- | --- | --- | --- | --- |
| `/relatorios/` | Bloqueado | Própria escola | Todas as escolas e ranking | Bloqueado |
| `/relatorios/escolas/<id>` | Bloqueado | Própria escola | Todas as escolas | Bloqueado |
| `/relatorios/escolas/<id>/series/<id>` | Bloqueado | Própria escola | Todas as escolas | Bloqueado |
| `/relatorios/escolas/<id>/series/<id>/turmas/<id>` | Bloqueado | Própria escola | Todas as escolas | Bloqueado |
