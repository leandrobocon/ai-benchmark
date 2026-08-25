# Metodologia

## Escopo

O benchmark avalia modelos de IA em tarefas práticas relacionadas a Moodle, Python e n8n.

Os mesmos testes podem ser executados em ambientes locais ou por API. A intenção é separar três dimensões: **qualidade**, **eficiência** e **custo**.

## Estrutura de um teste

Cada teste possui, conforme aplicável:

- identificador;
- domínio;
- tipo de tarefa;
- prompt;
- palavras-chave esperadas;
- indicação de que existe código a ser avaliado;
- marcador de código esperado.

O arquivo `prompts/benchmark.json` é a fonte canônica dos testes. Alterações nesse arquivo devem ser tratadas como mudança do conjunto de avaliação e acompanhadas por uma nova versão do benchmark quando afetarem comparações já publicadas.

## Ambientes de execução

### Local

O executor local pode usar LM Studio ou outro servidor compatível com a API OpenAI-compatible. Além das métricas retornadas pelo servidor, são registrados dados de tempo da execução.

### API

O executor de API atualmente possui um adaptador para OpenRouter. A mesma lista de testes é enviada aos modelos selecionados.

Para o OpenRouter, a API pode fornecer dados de uso por meio de `usage: {include: true}`. Dependendo do modelo e da resposta, podem estar disponíveis tokens de prompt, completion, reasoning e total, além do custo. citeturn0search4turn0search12

## Parâmetros

Toda comparação deve registrar os parâmetros relevantes da geração. No executor por OpenRouter, são suportados e registrados:

- modelo;
- `temperature`;
- `top_p`;
- `top_k`, quando aplicável;
- `seed`, quando aplicável;
- `max_tokens`;
- configuração de reasoning, quando aplicável;
- timeout;
- endpoint/provedor;
- conjunto e quantidade de testes.

Nem todo modelo ou provedor suporta todos os parâmetros. Um parâmetro ausente ou não suportado deve permanecer explícito no resultado, e não ser tratado como se tivesse sido aplicado.

## Qualidade

A avaliação automática atual é heurística. Os testes podem verificar a presença de palavras ou elementos esperados e, em determinados casos, a presença de código.

A pontuação deve ser entendida como um **indicador operacional do benchmark**, não como uma prova de correção da resposta.

Uma resposta pode conter todas as palavras esperadas e ainda apresentar erro técnico. Da mesma forma, uma resposta correta pode utilizar uma solução diferente da prevista pelos critérios atuais.

## Eficiência

A eficiência é observada separadamente da qualidade. As métricas podem incluir:

- tokens de entrada;
- tokens de saída;
- tokens de raciocínio, quando disponíveis;
- tokens totais;
- latência total;
- velocidade de geração, quando a infraestrutura fornecer dados suficientes.

Uma resposta mais longa ou mais rápida não deve ser considerada automaticamente melhor. Eficiência é uma dimensão de comparação, não um substituto para qualidade.

## Custo

Quando a API fornecer o custo efetivo da execução, esse valor deve ser registrado diretamente.

Quando o custo não estiver disponível, o resultado deve indicar custo indisponível. Não deve ser criado um valor estimado sem que a metodologia de cálculo esteja explicitamente documentada.

Para comparações futuras de modelos pagos, preços devem ser associados à data e à configuração utilizada, porque catálogos e preços podem mudar.

## OpenRouter e modelos gratuitos

O OpenRouter disponibiliza modelos gratuitos e um roteador `openrouter/free`. O catálogo é dinâmico. A página de preços consultada informa atualmente 25+ modelos gratuitos e limite de 50 requisições/dia no plano Free; a documentação publicada pelo próprio OpenRouter também informa 20 requisições por minuto e uma cota diária maior após a adição de créditos. Esses valores devem ser rechecados antes de cada campanha. citeturn0search0turn0search1turn0search2

Por causa desses limites, uma campanha inicial deve usar poucos testes por modelo. O benchmark fornece filtros para domínio, número de testes e número de modelos.

O roteador `openrouter/free` não deve ser usado como substituto de uma comparação individual entre modelos: ele seleciona modelos gratuitos disponíveis dinamicamente, portanto uma execução em `openrouter/free` não identifica um único modelo fixo. citeturn0search2

## Comparabilidade

Para comparar duas execuções, devem ser mantidas constantes, tanto quanto possível:

- versão do benchmark;
- conjunto de testes;
- modelo e versão;
- parâmetros de geração;
- contexto enviado ao modelo;
- hardware, no caso local;
- servidor e quantização, no caso local;
- provedor e configuração de roteamento, no caso de API;
- número de execuções.

Alterações nesses fatores podem modificar os resultados.

## Repetição e ranking

Uma execução isolada não é suficiente para sustentar uma conclusão forte de superioridade.

Antes de publicar rankings, o projeto deve executar cada condição relevante múltiplas vezes e registrar a distribuição dos resultados. A apresentação final poderá usar média, mediana e dispersão, conforme o comportamento observado.

O objetivo futuro é produzir comparações por domínio — Python, n8n e Moodle — e, separadamente, indicadores de qualidade, eficiência e custo.

## Boas práticas para publicação de resultados

Um resultado público deve informar pelo menos:

1. versão do benchmark;
2. modelo e versão, quando disponível;
3. provedor e ambiente;
4. parâmetros de geração;
5. hardware, quando relevante;
6. conjunto de testes;
7. data do teste;
8. número de execuções;
9. tokens e latência disponíveis;
10. custo e fonte do preço, quando aplicável;
11. método de pontuação;
12. limitações conhecidas.

## Segurança e privacidade

Execuções internas e resultados públicos devem permanecer separados. Nunca devem ser publicados tokens, chaves, endpoints internos, dados reais de usuários ou prompts que contenham informação institucional não pública.

## Evolução da metodologia

A próxima evolução é substituir gradualmente avaliações baseadas apenas em palavras-chave por critérios de correção técnica, validação executável quando possível e avaliação humana estruturada.

Até que essa evolução seja implementada, qualquer ranking deve ser apresentado como resultado do benchmark sob suas condições específicas, e não como uma verdade universal sobre os modelos.
