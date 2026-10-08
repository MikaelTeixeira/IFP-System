# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Cinco perfis compartilham uma única aplicação, com uso equilibrado entre computador e celular:

- **Aluno**: consulta e responde simulados liberados, vê resultados, avisos e materiais de revisão, inclusive pelo celular.
- **Professor**: mantém o próprio banco de questões, responde solicitações de simulado, publica materiais para as turmas e corrige respostas abertas.
- **Coordenação do Colégio**: gerencia a estrutura da própria escola, solicita simulados com prazo, aprova ou pede revisão, agenda e avisa alunos.
- **Coordenação do Instituto**: acompanha todas as instituições, relatórios da rede e ranking das escolas, transfere professores.
- **Administrador/T.I.**: administra usuários e o ambiente.

## Product Purpose

Sistema de aplicação, acompanhamento e análise de avaliações do Instituto Fabiana Pinto. Organiza a estrutura acadêmica (municípios, instituições, séries, turmas, alunos, professores), o currículo, o banco de questões, o ciclo completo de simulados (solicitação, entrega, revisão, agendamento, aplicação, correção, resultado), a leitura de cartões-resposta e os relatórios hierárquicos de desempenho. Sucesso é cada perfil concluir sua tarefa sem atrito e a rede enxergar o desempenho de rede, escola, série e turma.

## Positioning

Ferramenta própria do instituto, que conecta coordenação da rede, escolas, professores e alunos no mesmo fluxo de avaliação, com escopo de dados recortado por perfil.

## Operating Context

Flask com templates Jinja, CSS próprio e JavaScript sem framework. Persistência local em MySQL. Login demonstrativo com acessos rápidos por perfil. Interface inteira em português brasileiro. Durante o simulado, o aluno tem proteções contra cópia, impressão e perda de foco.

## Capabilities and Constraints

- Rotas, permissões, formulários e comportamento existentes devem ser preservados em qualquer redesenho.
- Sem dependência obrigatória de framework de frontend; dependências novas só com benefício claro.
- Desktop e celular têm o mesmo peso.
- Autenticação real ainda está fora do escopo (login demonstrativo).

## Brand Commitments

- Nome: Instituto Fabiana Pinto. Linhas de atuação divulgadas: Educação, Saúde, Cultura, Gestão Social. Lema público: "Ética, inovação e resultados reais."
- Logo: círculo laranja com um "P" formado por linhas verticais paralelas, acompanhado de um ponto e ondas à esquerda. Fonte: perfil @institutofabianapinto no Instagram. Versão SVG vetorizada a partir dessa imagem até que o arquivo oficial seja fornecido; fonte única em `app/templates/macros/brand.html`, com favicons e ícones gerados por `scripts/gerar_icones.py`.
- Paleta da marca extraída da logo e das peças do Instagram (binding), aplicada em `app/static/css/tokens.css`: laranja da logo `#B86122`, marrom escuro das linhas da logo `#522304`, azul-marinho dos títulos institucionais `#2D3B57`, areia/dourado claro dos fundos das peças `#EADAB3`, e branco.

## Evidence on Hand

- Logo e peças públicas do Instagram (HUB EJA com Ibateguara, ações sociais, encontros online). Não há fotos licenciadas para uso no sistema; nenhuma foto de pessoas deve ser inventada ou reaproveitada sem autorização.
- Dados demonstrativos em `app/data/` e documentação em `docs/`.

## Product Principles

1. Cada perfil vê somente o que é seu, e a interface deixa claro em que escopo ele está.
2. A tarefa vem antes da expressão: estado, prazo e próxima ação sempre visíveis.
3. A marca do instituto está presente em todo o sistema, não só no login.
4. Funciona igualmente bem no computador e no celular.

## Accessibility & Inclusion

Português brasileiro em toda a interface. Informação importante nunca depende só de cor. Foco visível, alvos de toque confortáveis e contraste adequado para alunos e equipe.
