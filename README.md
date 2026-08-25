# AI Benchmark

Benchmark prático para avaliação de modelos de inteligência artificial em tarefas de engenharia.

## Objetivo

Este projeto foi criado para comparar modelos de IA em tarefas práticas relacionadas a **Moodle, Python e n8n**, utilizando testes reproduzíveis e critérios explícitos.

O benchmark nasceu de necessidades práticas de avaliação de modelos executados localmente e pode ser adaptado para outros modelos, tarefas e ambientes.

## O que é avaliado

Os testes atuais cobrem diferentes tipos de tarefa, incluindo:

- conhecimento e estrutura de Moodle;
- PHP e APIs do Moodle;
- banco de dados, eventos, capabilities e web services;
- integração de APIs com Python;
- autenticação, JSON, HTTP e tratamento de erros;
- programação assíncrona, logging, validação e rate limiting;
- workflows n8n, Code nodes, expressões, HTTP Request e tratamento de erros.

## Como funciona

Cada teste possui um prompt e critérios de avaliação definidos para o domínio da tarefa. O executor envia os prompts ao modelo e registra informações da execução, incluindo tempo e métricas de geração quando disponíveis.

A pontuação automática atual utiliza **heurísticas**, como presença de termos esperados e, em determinados testes, presença de código. Isso significa que a pontuação não deve ser interpretada como uma medida absoluta da qualidade ou capacidade de um modelo.

## Execução

O projeto atual foi desenvolvido para trabalhar com uma API compatível com o ambiente local utilizado pelo benchmark.

Antes de executar, verifique a configuração em `benchmark.py` e os requisitos do ambiente.

Exemplos:

```bash
python benchmark.py
```

ou, conforme o fluxo escolhido:

```bash
python run_benchmark.py
```

## Estrutura atual

```text
.
├── benchmark.py
├── benchmark_auto.py
├── run_benchmark.py
├── docs/
│   └── metodologia.md
├── resultados/
│   └── README.md
└── README.md
```

## Resultados

Resultados de ambientes internos não fazem parte deste repositório. Resultados publicados devem ser acompanhados da versão do benchmark, modelo utilizado e condições relevantes do teste.

## Limitações

Este projeto não pretende estabelecer um ranking universal de modelos.

A metodologia atual possui limitações importantes:

- parte da avaliação é baseada em heurísticas;
- palavras-chave não equivalem a correção técnica;
- respostas tecnicamente corretas podem utilizar abordagens diferentes das previstas pelo teste;
- resultados dependem do modelo, configuração, hardware, contexto e parâmetros de execução;
- comparações entre modelos somente são significativas quando as condições de execução são documentadas.

Essas limitações fazem parte do projeto e serão consideradas na evolução da metodologia.

## Evolução planejada

- separar prompts da lógica de execução;
- centralizar a avaliação em um módulo próprio;
- publicar metodologia detalhada;
- adicionar resultados reproduzíveis;
- permitir novos conjuntos de testes sem alterar o executor;
- ampliar a avaliação para além de palavras-chave, incluindo critérios de correção técnica quando possível.

## Autor

**Leandro Engler Bocon**

Projeto pessoal de experimentação e avaliação de modelos de inteligência artificial.
