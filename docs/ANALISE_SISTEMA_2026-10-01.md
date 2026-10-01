# Análise lógica e de persistência

> **Situação após a correção:** a migração descrita neste relatório foi executada.
> Estrutura acadêmica, currículo, questões, simulados, solicitações, materiais e
> indicadores agora estão no MySQL. A aplicação sincroniza contas com alunos e
> professores, bloqueia vínculos acadêmicos entre instituições diferentes,
> respeita contas desativadas nos acessos rápidos, rejeita prazos passados e usa
> o tempo do servidor nas tentativas. O registro de arquivo órfão identificado
> durante a análise foi removido. As restrições que dependem de autenticação real,
> HTTPS e controles de infraestrutura continuam em `PENDENCIAS_SEGURANCA.md`.

**Data:** 1º de outubro de 2026  
**Escopo:** aplicação Flask, regras de acesso, fluxos acadêmicos, simulados,
arquivos, notificações, relatórios e integração com o MySQL local.

## Conclusão no momento da análise, antes da correção

O sistema funciona como protótipo navegável e a suíte automatizada está estável,
mas o domínio ainda está dividido entre MySQL e listas em memória. Essa divisão
faz com que partes relacionadas tenham comportamentos diferentes após reiniciar
o Flask. O sistema não deve receber dados reais enquanto autenticação, estrutura
acadêmica, currículo, questões, simulados e publicações não forem unificados na
camada persistente.

O MySQL local está conectado e respondeu durante a análise. Foram encontradas
oito tabelas e os seguintes registros: 3 municípios, 4 instituições, 7 usuários,
4 notificações e 1 arquivo. Não havia tentativas, respostas ou eventos de revisão
no momento da consulta.

## Matriz de persistência atual

| Domínio | Situação | Observação |
| --- | --- | --- |
| Municípios | MySQL | Cadastro, edição e situação são persistidos. |
| Instituições | MySQL | Cadastro, edição e situação são persistidos. |
| Usuários administrativos | MySQL | Cadastro e situação são persistidos, mas não controlam o login. |
| Tentativas e respostas | MySQL | Persistidas, porém referenciam alunos, simulados e questões em memória. |
| Notificações | MySQL | Persistidas, mas podem apontar para conteúdos que desapareceram. |
| Histórico de revisão | MySQL | Eventos persistem; o estado atual da questão não persiste. |
| Metadados de arquivos | MySQL | O vínculo com a publicação ou questão fica em memória. |
| Arquivos físicos | Pasta local | Permanecem em `instance/uploads`. |
| Séries, turmas, alunos e professores | Memória | Alterações desaparecem ao reiniciar. |
| Matérias e assuntos | Memória | Alterações desaparecem ao reiniciar. |
| Questões e estado da revisão | Memória | Alterações desaparecem ao reiniciar. |
| Simulados e solicitações | Memória | Alterações desaparecem ao reiniciar. |
| Publicações de revisão | Memória | Alterações desaparecem ao reiniciar. |
| Frequência, faltas e histórico dos relatórios | Demonstrativo | Valores não vêm do banco. |

## Achados prioritários

### 1. Persistência parcial gera registros órfãos

O banco persiste notificações, arquivos, tentativas e histórico, enquanto seus
registros principais ficam em memória. Depois de uma reinicialização, uma
publicação, questão, solicitação ou simulado criado durante a sessão desaparece,
mas seus registros auxiliares continuam no MySQL.

A consulta real encontrou um arquivo persistido para `rev-002`, publicação que
já não existe na lista de materiais carregada pela aplicação. O arquivo físico
também continua no disco. Isso confirma um órfão produzido pelo funcionamento
atual, não apenas uma possibilidade teórica.

**Prioridade:** bloqueadora para uso real.

### 2. Usuários do MySQL não controlam a autenticação

O login usa cinco perfis fixos em código. Cadastrar um usuário no MySQL não cria
um acesso utilizável, e desativar uma conta não revoga o perfil rápido associado.
Em cenário isolado, `usr-003` foi marcado como **Inativo** no banco e o acesso
rápido do Professor continuou abrindo normalmente o painel de Rafael.

**Prioridade:** bloqueadora para autenticação real.

### 3. Cadastro acadêmico e conta de usuário são cadastros independentes

Aluno e Professor existem em listas acadêmicas, enquanto as contas ficam em
`user_accounts`. Não há chave que conecte os dois registros. Como consequência:

- criar Professor ou Aluno não cria uma conta;
- criar conta de Professor ou Aluno não cria o registro acadêmico;
- editar CPF, e-mail, situação ou instituição em um lado não atualiza o outro;
- a transferência de Professor altera apenas o registro acadêmico.

O teste isolado transferiu `pro-001` para `inst-002`; a conta `usr-003` permaneceu
em `inst-001`. O perfil fixo do Professor também preserva as turmas antigas.

**Prioridade:** alta.

### 4. Unicidade de CPF e e-mail não é global

A criação de usuários consulta o MySQL e os cadastros acadêmicos. A criação de
Aluno ou Professor consulta apenas as listas acadêmicas. Foi possível criar um
Professor usando o CPF já cadastrado para a Coordenadora do Colégio no MySQL.

As restrições únicas da tabela `user_accounts` não protegem as listas de alunos
e professores porque elas não são tabelas.

**Prioridade:** alta.

### 5. Relações acadêmicas podem cruzar instituições

As rotas aceitam `instituicao_id`, `serie_id`, `turma_id` e matérias como campos
independentes. Não há validação completa das relações no servidor. O cenário de
teste criou um aluno em `inst-002` vinculado a `tur-001`, que pertence a
`inst-001`, e a requisição foi aceita.

Também é possível manter no Professor transferido uma matéria local da escola
anterior. A Coordenação do Instituto pode selecionar uma matéria institucional
de outra escola ao editar um Professor.

**Prioridade:** alta.

### 6. Data, prazo e cronômetro não são regras de servidor

O status **Publicado** ou **Agendado** já libera o simulado; a data de aplicação
não é comparada com o horário atual. Em 1º de outubro, o aluno conseguiu iniciar
o simulado datado para 15 de outubro.

O servidor calcula o tempo restante, mas aceita salvamento e entrega quando ele
chega a zero. Um cenário com 50 minutos decorridos em um simulado de 40 minutos
foi entregue com sucesso e recebeu **Resultado disponível**.

O prazo informado pela coordenação também é apenas exibido. Uma solicitação com
prazo em 1º de janeiro de 2000 foi aceita. A data de agendamento pode ser passada.

**Prioridade:** alta para aplicação de avaliações.

### 7. Simulados e questões continuam editáveis por referência

Um simulado armazena somente os identificadores das questões. Não existe versão
ou cópia imutável da questão aplicada. Editar enunciado, alternativas ou gabarito
altera também simulados publicados e a visualização de tentativas anteriores.

O simulado publicado também pode ser editado sem bloqueio por situação ou pela
existência de tentativas. Isso pode mudar duração, público e composição depois
do início da aplicação. Os relatórios normalizam a nota usando a quantidade
atual de questões, portanto uma edição posterior pode alterar a média exibida.

**Prioridade:** alta.

### 8. Revisões concorrentes compartilham um único estado na questão

O estado, a observação e o solicitante da revisão ficam no objeto da questão. Se
a mesma questão participar de solicitações diferentes, uma nova solicitação pode
sobrescrever a anterior. Ao editar a questão, todas as entregas que aguardavam
revisão podem passar para **Reenviada**, mesmo quando tinham orientações distintas.

O histórico permanece no banco, mas o estado atual volta ao valor inicial após
reiniciar a aplicação.

**Prioridade:** média-alta.

### 9. Relatórios misturam resultados reais e valores simulados

As médias gerais podem usar tentativas concluídas. Frequência, faltas e evolução
mensal vêm de constantes. O ranking de alunos da turma também é calculado por
variações artificiais em torno da média, e não pelas tentativas individuais.

Uma escola sem turmas e sem estudantes aparece com média **7,3** e frequência
**91,9%**. O aviso de dados demonstrativos aparece na visão da rede e da escola,
mas não acompanha as páginas de série e turma.

**Prioridade:** alta antes de apresentar o relatório como indicador oficial.

### 10. Integridade e evolução do banco ainda são frágeis

Tentativas, arquivos, notificações e revisões guardam identificadores de entidades
que não possuem tabela, por isso não têm chaves estrangeiras. A aplicação executa
`create_all()` ao iniciar e altera um índice por SQL direto, sem migrações
versionadas. Erros de unicidade ou chave estrangeira não são tratados nas rotas;
em alguns fluxos a lista em memória é alterada antes do `commit`, podendo divergir
do banco quando a transação falhar.

Os identificadores sequenciais são calculados com `max + 1`, sem proteção contra
duas requisições simultâneas.

**Prioridade:** média-alta.

## Validações executadas

- Conexão real com o MySQL e inspeção das tabelas e quantidades.
- Verificação de chaves estrangeiras e referências entre os dois armazenamentos.
- Busca por arquivos persistidos sem entidade proprietária.
- Cenários isolados de autenticação, prazo, cronômetro, CPF, vínculo acadêmico,
  duração de simulado, transferência e relatório sem estudantes.
- Compilação dos módulos Python.
- Verificação sintática do JavaScript.
- Suíte automatizada: **64 testes aprovados**.

Os testes atuais confirmam os fluxos demonstrativos, mas não cobrem reinício do
servidor, consistência entre conta e cadastro acadêmico, relações entre escolas,
datas de aplicação, expiração do tempo ou imutabilidade de avaliações publicadas.

## Ordem recomendada de correção

1. Criar tabelas para pessoas, vínculos acadêmicos, currículo, questões,
   simulados, solicitações, entregas e publicações.
2. Substituir os perfis fixos por autenticação ligada a `user_accounts`, incluindo
   senha com hash e revogação por situação.
3. Unificar conta e pessoa acadêmica por identificadores e transações únicas.
4. Adicionar chaves estrangeiras, restrições de escopo e validações relacionais.
5. Criar versões imutáveis de questões para cada simulado publicado.
6. Aplicar data, janela de acesso, prazo e cronômetro no servidor.
7. Migrar arquivos e notificações somente depois que suas entidades proprietárias
   estiverem persistidas, com rotina de limpeza de órfãos.
8. Fazer relatórios consumirem apenas dados persistidos e mostrar ausência de
   dados em vez de criar médias para escolas vazias.
9. Introduzir Alembic ou Flask-Migrate e remover alterações de esquema no startup.
10. Acrescentar testes de integração com MySQL, reinício, concorrência e falhas de
    transação.
