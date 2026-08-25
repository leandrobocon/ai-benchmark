# AI Benchmark

Benchmark prático para avaliação de modelos de inteligência artificial em tarefas de engenharia.

## Objetivo

Este projeto compara modelos de IA em tarefas práticas relacionadas a **Moodle, Python e n8n**, utilizando testes reproduzíveis e critérios explícitos.

O benchmark nasceu de necessidades práticas de avaliação de modelos executados localmente e pode ser adaptado para outros modelos, tarefas e ambientes.

## Princípios

- **Reprodutibilidade:** os testes ficam versionados no repositório.
- **Transparência:** a metodologia e as limitações são documentadas.
- **Separação de dados:** configurações, credenciais e informações de ambientes privados não fazem parte do conjunto público.
- **Evidência antes de ranking:** resultados devem ser acompanhados das condições em que foram obtidos.

## Domínios atuais

### Moodle

Conhecimento, estrutura de plugins, PHP, XMLDB, API `$DB`, web services, eventos, capabilities, arquivos de idioma e análise de problemas de segurança.

### Python

Integração com APIs, autenticação, JSON, HTTP, retries, CSV, programação assíncrona, variáveis de ambiente, logging, validação e rate limiting.

### n8n

Workflows, Code nodes, expressões, HTTP Request, condicionais, tratamento de erros, loops, credenciais, agendamento e agentes de IA.

## Estrutura

```text
.
├── benchmark.py              # executor original
├── benchmark_auto.py         # executor original/automático
├── run_benchmark.py          # executor original priorizado
├── benchmark_v2.py           # executor modular
├── evaluator.py              # avaliação heurística isolada
├── prompts/
│   └── benchmark.json        # conjunto canônico de testes
├── docs/
│   └── metodologia.md       # metodologia e limitações
├── resultados/
│   └── README.md             # política para resultados públicos
└── README.md
```

A versão modular utiliza `prompts/benchmark.json` como fonte única dos testes e `evaluator.py` como módulo de avaliação. Isso permite acrescentar ou alterar testes sem duplicar a definição dos prompts dentro dos executores.

## Requisitos

- Python 3.10+ recomendado;
- `requests`;
- um servidor compatível com a API OpenAI-compatible utilizada pelo executor. A configuração padrão aponta para o LM Studio em `http://localhost:1234`.

Instalação da dependência:

```bash
python -m pip install requests
```

## Execução modular

Listar automaticamente os modelos disponíveis no endpoint:

```bash
python benchmark_v2.py
```

Executar um modelo específico:

```bash
python benchmark_v2.py --model NOME_DO_MODELO
```

Executar somente um domínio:

```bash
python benchmark_v2.py --domain Moodle
python benchmark_v2.py --domain Python --domain n8n
```

Alterar o endpoint:

```bash
python benchmark_v2.py --base http://localhost:1234
```

Não gravar as respostas completas no arquivo de resultado:

```bash
python benchmark_v2.py --no-save-responses
```

Os parâmetros também podem ser controlados por variáveis de ambiente `LMSTUDIO_BASE`, `AI_BENCHMARK_TIMEOUT` e `AI_BENCHMARK_MAX_TOKENS`.

## Avaliação

A versão atual utiliza uma **heurística v0.1**. Parte da pontuação considera a presença de critérios declarados no teste; testes que solicitam código também verificam um marcador de código. Para tarefas que não solicitam código, existe uma pequena contribuição baseada no tamanho da resposta.

Essa pontuação é útil para triagem e comparação dentro de condições controladas, mas **não representa uma medida absoluta da qualidade de um modelo**.

Uma resposta pode conter todos os termos esperados e ainda estar tecnicamente errada. Da mesma forma, uma resposta correta pode usar uma abordagem diferente da prevista pelo teste. Por isso, avaliações importantes devem incluir revisão técnica humana ou avaliadores mais específicos.

## Resultados

Os executores salvam resultados localmente em `resultados/`. Antes de publicar um resultado, devem ser removidos dados sensíveis e informações específicas de ambientes privados.

Resultados públicos devem informar, no mínimo:

- versão do benchmark;
- versão/configuração do executor;
- modelo e versão, quando disponível;
- hardware relevante;
- parâmetros relevantes de geração;
- conjunto de testes executado;
- data da execução;
- limitações conhecidas.

## Segurança e privacidade

Este repositório é público. Não devem ser publicados:

- tokens, senhas ou chaves;
- endpoints internos;
- endereços IP ou nomes de hosts privados;
- dados reais de usuários;
- prompts contendo informação institucional não pública;
- configurações específicas que exponham ambientes privados.

O benchmark público deve permanecer independente das configurações utilizadas em ambientes internos.

## Limitações

Este projeto não pretende estabelecer um ranking universal de modelos.

Os resultados dependem do modelo, quantização, hardware, contexto, parâmetros, servidor e versão das ferramentas utilizadas. Comparações somente são significativas quando as condições de execução são documentadas.

## Evolução

Próximas etapas possíveis:

1. adicionar casos de teste sem alterar o executor;
2. criar categorias de correção técnica por teste;
3. adicionar validações específicas para código quando forem confiáveis;
4. permitir avaliação humana estruturada;
5. comparar velocidade e qualidade separadamente;
6. publicar resultados reproduzíveis e versionados;
7. criar conjuntos de testes independentes por domínio.

## Autor

**Leandro Engler Bocon**

Projeto pessoal de experimentação e avaliação de modelos de inteligência artificial.
