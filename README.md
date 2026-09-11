# Instituto Fabiana Pinto - Sistema de Avaliações

Frontend funcional de um sistema de aplicação, acompanhamento e análise de
avaliações. A primeira entrega será construída com Flask e cobrirá os blocos 1
a 4 definidos no planejamento do frontend.

## Estado atual

Os Blocos 1 e 2 foram concluídos. A aplicação já contém a fundação Flask, o
layout responsivo, os componentes compartilhados e os estados de erro.

## Executar localmente

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app run.py run --debug
```

A aplicação ficará disponível em `http://127.0.0.1:5000`.

## Documentação

- [Planejamento do frontend](docs/PLANEJAMENTO_FRONTEND.md)
- [Diário de desenvolvimento](docs/DIARIO_DESENVOLVIMENTO.md)
