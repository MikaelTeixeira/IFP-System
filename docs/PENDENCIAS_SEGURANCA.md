# Pendências de segurança

Este documento reúne requisitos que permanecem pendentes antes de usar o
sistema com dados reais ou disponibilizá-lo fora do computador local.

## Acesso e sessão

- Substituir o login livre por autenticação real com senha protegida por hash.
- Vincular permissões a usuários persistidos, sem depender dos perfis rápidos.
- Remover a chave de sessão demonstrativa e exigir segredo forte por variável de ambiente.
- Configurar cookies `Secure`, `HttpOnly` e `SameSite` conforme o ambiente.
- Implementar expiração de sessão, recuperação de senha, bloqueio progressivo e
  limite de tentativas de acesso.
- Adicionar proteção CSRF a todos os formulários e requisições de alteração.
- Exigir HTTPS no ambiente publicado.

## Autorizações e auditoria

- Centralizar as permissões em uma política testável e persistida no banco.
- Registrar login, publicação, transferência, revisão, correção, exclusão e
  acesso a arquivos em uma trilha de auditoria imutável.
- Revisar o acesso das coordenações aos resultados e respostas dos alunos.
- Criar rotina de revogação imediata para usuários desativados.

## Arquivos

- Validar o conteúdo real do arquivo, além da extensão e do tipo informado pelo navegador.
- Integrar verificação antimalware antes de disponibilizar anexos.
- Definir cotas por usuário e instituição, retenção, backup e limpeza de arquivos órfãos.
- Impedir execução de arquivos e aplicar cabeçalhos seguros no download.
- Avaliar criptografia dos arquivos armazenados quando houver dados pessoais.

## Aplicação e navegador

- Adicionar Content Security Policy e cabeçalhos contra enquadramento, leitura
  indevida de tipo e vazamento de referência.
- Aplicar limites de requisição nas rotas de login, upload e salvamento automático.
- Validar entradas no servidor conforme regras de negócio completas.
- Executar análise de dependências, testes de segurança e revisão de código antes da publicação.
- As barreiras contra copiar, imprimir e usar Print Screen não impedem capturas
  feitas pelo sistema operacional, extensões, câmeras ou outro dispositivo.

## Banco e privacidade

- Usar usuário MySQL com privilégio mínimo, rotação de senha e segredo fora do projeto.
- Adotar migrações versionadas, backup criptografado e teste periódico de restauração.
- Definir retenção e descarte de CPF, respostas, notas, comentários e logs conforme a LGPD.
- Registrar consentimento ou base legal, finalidade de uso e atendimento aos
  direitos do titular.
- Criptografar dados sensíveis em trânsito e avaliar criptografia em repouso.

## Avaliações

- Fazer o servidor encerrar a tentativa ao atingir o limite de tempo e definir o
  tratamento de respostas incompletas nesse cenário.
- Proteger contra abertura concorrente da mesma tentativa em vários dispositivos.
- Registrar alterações de horário e garantir uma fonte de tempo confiável no servidor.
- Definir regras de reabertura excepcional, anulação e revisão de nota com auditoria.
