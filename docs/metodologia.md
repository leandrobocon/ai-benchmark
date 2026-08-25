# Metodologia

## Escopo

O benchmark avalia modelos de IA em tarefas práticas relacionadas a Moodle, Python e n8n.

Os testes foram escolhidos para representar problemas de engenharia de software, integração e automação, em vez de medir somente conhecimento factual.

## Estrutura de um teste

Cada teste possui, conforme aplicável:

- identificador;
- domínio;
- tipo de tarefa;
- prompt;
- palavras-chave esperadas;
- indicação de que existe código a ser avaliado;
- marcador de código esperado.

## Execução

O executor envia o prompt ao modelo configurado e registra as informações disponíveis da execução.

Quando suportado pelo ambiente, são registrados dados como:

- tempo total;
- tempo até o primeiro token;
- tokens de entrada;
- tokens de saída;
- velocidade de geração.

## Pontuação atual

A avaliação automática atual é heurística. Os testes podem verificar a presença de palavras ou elementos esperados e, em determinados casos, a presença de código.

A pontuação deve ser entendida como um **indicador operacional do benchmark**, não como uma prova de correção da resposta.

Uma resposta pode conter todas as palavras esperadas e ainda apresentar erro técnico. Da mesma forma, uma resposta correta pode utilizar uma solução diferente da prevista pelos critérios atuais.

## Comparabilidade

Para comparar duas execuções, devem ser mantidas constantes, tanto quanto possível:

- versão do benchmark;
- conjunto de testes;
- modelo;
- parâmetros de geração;
- contexto enviado ao modelo;
- hardware;
- configuração do servidor/modelo;
- número de execuções.

Alterações nesses fatores podem modificar os resultados.

## Boas práticas para publicação de resultados

Um resultado público deve informar pelo menos:

1. versão do benchmark;
2. modelo testado;
3. ambiente de execução;
4. configuração relevante;
5. data do teste;
6. número de execuções;
7. método de pontuação;
8. limitações conhecidas.

## Evolução da metodologia

A próxima evolução planejada é separar os dados dos testes da lógica de execução e substituir gradualmente avaliações baseadas apenas em palavras-chave por critérios que considerem correção técnica, quando houver uma forma objetiva de fazê-lo.

Até que essa evolução seja implementada, o projeto deve apresentar os resultados com a ressalva de que a avaliação automática é heurística.
