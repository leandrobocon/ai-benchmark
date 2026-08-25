# AI Benchmark

Benchmark prático para avaliação de modelos de inteligência artificial em tarefas de engenharia.

## Objetivo

Este projeto compara modelos de IA em tarefas práticas relacionadas a **Moodle, Python e n8n**, usando o mesmo conjunto versionado de testes em ambientes locais e por API.

A ideia é medir três dimensões separadamente:

- **Qualidade:** desempenho segundo os critérios do teste;
- **Eficiência:** tokens consumidos e tempo de execução;
- **Custo:** custo informado pela API ou calculado a partir da precificação registrada para aquela execução.

O projeto nasceu de necessidades práticas de avaliação de modelos executados localmente e está sendo ampliado para comparações reproduzíveis por API.

## Princípios

- **Reprodutibilidade:** os testes ficam versionados no repositório.
- **Transparência:** metodologia, parâmetros e limitações acompanham os resultados.
- **Separação de dados:** configurações, credenciais e informações de ambientes privados não fazem parte do conjunto público.
- **Evidência antes de ranking:** resultados devem ser acompanhados das condições em que foram obtidos.
- **Sem vencedor universal:** um modelo pode ser melhor para uma categoria e pior para outra.

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
├── benchmark_v2.py           # executor modular para ambientes locais
├── benchmark_api.py          # executor por API
├── evaluator.py              # avaliação heurística isolada
├── providers/
│   ├── __init__.py
│   └── openrouter.py         # adaptador OpenRouter
├── prompts/
│   └── benchmark.json        # conjunto canônico de testes
├── docs/
│   └── metodologia.md        # metodologia e limitações
├── resultados/
│   └── README.md             # política para resultados públicos
└── README.md
```

O conjunto de testes é compartilhado entre execução local e API. O provedor é separado da lógica do benchmark, permitindo adicionar outros adaptadores sem duplicar os testes.

## Requisitos

- Python 3.10+ recomendado;
- `requests`;
- para execução local: um servidor compatível com a API OpenAI-compatible, como LM Studio;
- para OpenRouter: uma variável `OPENROUTER_API_KEY` configurada no ambiente.

Instalação:

```bash
python -m pip install requests
```

## Execução local

Listar automaticamente os modelos disponíveis no endpoint:

```bash
python benchmark_v2.py
```

Executar um modelo específico:

```bash
python benchmark_v2.py --model NOME_DO_MODELO
```

## Execução por OpenRouter

O executor usa a API compatível com OpenAI do OpenRouter e registra, quando fornecidos pela API, tokens de entrada, tokens de saída, tokens de raciocínio, tokens totais e custo.

Configuração:

```bash
export OPENROUTER_API_KEY="sua-chave"
```

Listar e executar somente modelos cujo preço de entrada e saída no catálogo seja `$0`:

```bash
python benchmark_api.py --free-only --limit-models 1 --limit-tests 3
```

Executar um modelo específico:

```bash
python benchmark_api.py --model ID_DO_MODELO --limit-tests 3
```

Executar somente um domínio:

```bash
python benchmark_api.py --free-only --domain Python --limit-tests 5
```

### Por que começar com poucos testes?

O catálogo gratuito do OpenRouter possui limites de requisições. Na consulta atual, a página de preços informa **50 requisições/dia no plano Free**, enquanto a documentação do próprio OpenRouter informa que a cota de modelos gratuitos pode subir para **1.000 requisições/dia após a adição de pelo menos US$ 10 em créditos**; ambos mantêm limite de 20 requisições por minuto. Esses limites podem mudar, portanto devem ser conferidos antes de uma campanha de testes. citeturn0search0turn0search1

Como o conjunto atual possui 30 testes, executar todos os testes contra vários modelos gratuitos pode consumir rapidamente a cota. Por isso, o executor oferece `--limit-tests`, `--limit-models` e `--domain`.

## Parâmetros registrados

Para tornar as comparações auditáveis, a execução por API registra a configuração utilizada, incluindo:

- modelo solicitado e modelo retornado;
- versão do benchmark;
- endpoint/provedor;
- timeout;
- `max_tokens`;
- `temperature`;
- `top_p`;
- `top_k`, quando utilizado;
- `seed`, quando utilizado;
- configuração de reasoning, quando utilizada;
- conjunto e quantidade de testes;
- tokens de entrada;
- tokens de saída;
- tokens de raciocínio, quando fornecidos;
- tokens totais;
- custo informado pela API, quando fornecido;
- latência total;
- motivo de finalização;
- identificador da resposta, quando fornecido.

No OpenRouter, a própria API documenta o retorno de dados de uso mediante `usage: {include: true}`. A precificação é específica por modelo e pode distinguir prompt, completion e reasoning tokens. citeturn0search4turn0search12

## Custo

O benchmark não assume que um modelo gratuito continuará gratuito nem grava um preço permanente como propriedade do modelo.

Para cada execução, a prioridade é registrar o custo retornado pela API. Quando essa informação não estiver disponível, o resultado deve indicar custo indisponível em vez de inventar uma estimativa.

Para modelos pagos, uma futura camada de cálculo poderá utilizar a precificação capturada no momento da execução. Isso é importante porque preços e disponibilidade podem mudar.

## Avaliação

A versão atual utiliza uma **heurística v0.1**. Parte da pontuação considera a presença de critérios declarados no teste; testes que solicitam código também verificam um marcador de código.

Essa pontuação é útil para triagem e comparação dentro de condições controladas, mas **não representa uma medida absoluta da qualidade de um modelo**.

Uma resposta pode conter todos os termos esperados e ainda estar tecnicamente errada. Da mesma forma, uma resposta correta pode usar uma abordagem diferente da prevista pelo teste. Avaliações públicas mais fortes deverão incorporar critérios de correção técnica e, quando apropriado, revisão humana.

## Resultados e futuro ranking

A intenção futura é publicar comparações por domínio, por exemplo:

- melhor desempenho observado em Python;
- melhor desempenho observado em n8n;
- melhor desempenho observado em Moodle;
- melhor relação entre qualidade, eficiência e custo.

Essas conclusões somente devem ser publicadas depois que a metodologia, a repetibilidade e as condições de execução forem suficientemente validadas.

O projeto não pretende declarar um vencedor universal. Um ranking deve sempre informar versão do benchmark, data, modelos, parâmetros, número de execuções e condições relevantes.

## Segurança e privacidade

Este repositório é público. Não devem ser publicados:

- tokens, senhas ou chaves;
- endpoints internos;
- endereços IP ou nomes de hosts privados;
- dados reais de usuários;
- prompts contendo informação institucional não pública;
- configurações específicas que exponham ambientes privados.

Nunca coloque `OPENROUTER_API_KEY` ou qualquer outra chave diretamente em arquivos versionados.

## Limitações

Os resultados dependem do modelo, versão, quantização, contexto, parâmetros, hardware, servidor, provedor, roteamento e versão das ferramentas utilizadas.

Modelos gratuitos podem ter disponibilidade, limites e contexto diferentes das variantes pagas. No OpenRouter, o conjunto de modelos gratuitos é dinâmico. citeturn0search2turn0search5

Uma execução isolada não é suficiente para sustentar uma afirmação forte de superioridade. Campanhas públicas devem considerar múltiplas execuções e condições controladas.

## Evolução

1. estabilizar a execução local;
2. validar a execução por OpenRouter;
3. testar modelos gratuitos em amostras pequenas;
4. registrar tokens, latência e custo;
5. melhorar a avaliação técnica;
6. repetir execuções para avaliar consistência;
7. adicionar outros provedores por adaptadores;
8. publicar resultados versionados;
9. criar o quadro comparativo no site.

## Autor

**Leandro Engler Bocon**

Projeto pessoal de experimentação e avaliação de modelos de inteligência artificial.
