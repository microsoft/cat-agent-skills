# Assistente CLT para RH

Skill para Copilot Studio / Cowork / Scout que transforma o agente em um assistente de legislação trabalhista brasileira (CLT) para equipes de RH e Departamento Pessoal. Responde dúvidas do dia a dia (férias, 13º, aviso prévio, banco de horas, jornada, tipos de rescisão) com citação da base legal, e calcula verbas rescisórias com **memória de cálculo** completa — incluindo INSS, IRRF (com a nova isenção da Lei 15.270/2025 até R$ 5.000) e multa do FGTS.

## O que ela faz

- Responde dúvidas da CLT citando o artigo, a lei ou a súmula por trás de cada regra.
- Calcula rescisões para os 5 tipos comuns: demissão sem justa causa, pedido de demissão, justa causa, acordo mútuo (art. 484-A) e término de contrato por prazo determinado.
- Calcula férias, 13º proporcional e aviso prévio (30 + 3 dias/ano, limitado a 90).
- Aplica o tratamento tributário correto: INSS e IRRF apenas sobre verbas tributáveis; aviso indenizado, férias indenizadas + 1/3 e multa do FGTS são isentos; 13º tributado separadamente.
- Mantém os valores atualizados: um script busca o salário mínimo oficial ao vivo na API do Banco Central do Brasil e sinaliza quando as tabelas empacotadas ficam desatualizadas.

## Estrutura da pasta

```
clt-hr-assistant/
├── metadata.json                  # metadados para a galeria
├── SKILL.md                       # instruções de execução para o agente
├── README.md                      # este arquivo (para humanos)
├── scripts/
│   ├── fetch_current_values.py    # salário mínimo ao vivo (API BCB) + checagem de defasagem
│   └── severance_calculator.py    # verbas rescisórias com memória de cálculo
├── references/
│   └── clt_rules.md               # regras da CLT com citações legais
└── assets/
    └── tables_2026.json           # tabelas oficiais de 2026 (mínimo, INSS, IRRF, FGTS)
```

## Como funciona a estratégia de "valores vigentes"

O Brasil publica as tabelas de INSS e IRRF apenas como páginas web/PDFs — não existe API oficial estruturada. Por isso a skill usa duas camadas:

1. **Camada ao vivo** — `fetch_current_values.py` consulta a API SGS do Banco Central do Brasil (série 1619, oficial) para obter o salário mínimo vigente. Como a primeira faixa do INSS sempre termina exatamente no salário mínimo, uma divergência com as tabelas empacotadas indica que elas estão defasadas, e o script avisa (código de saída 1).
2. **Camada empacotada** — `assets/tables_2026.json` carrega as tabelas oficiais completas de 2026. Quando a checagem ao vivo apontar defasagem (normalmente todo janeiro), basta atualizar este único arquivo com os valores do novo decreto/portaria.

Em plataformas sem execução de código (Copilot Studio), o agente usa as tabelas empacotadas diretamente e informa o ano de referência nas respostas.

## Exemplos de uso

Pergunte ao agente coisas como:

- "Quantos dias de aviso prévio tem um funcionário com 6 anos de casa?"
- "Calcule a rescisão: salário R$ 3.500, admitido em 01/03/2022, demitido sem justa causa em 24/07/2026, aviso indenizado, 1 dependente."
- "Posso parcelar as férias em 3 períodos? Quais os limites?"
- "Qual a multa se a empresa atrasar o pagamento da rescisão?"

Rodando a calculadora diretamente:

```bash
python scripts/severance_calculator.py \
  --salary 3500 --hire-date 2022-03-01 --end-date 2026-07-24 \
  --type sem_justa_causa --notice indemnified --dependents 1
```

## Manutenção anual

Todo janeiro, após o novo decreto (salário mínimo), a portaria (INSS) e a publicação da Receita Federal (IRRF):

1. Atualize `assets/tables_2026.json` (e os campos de ano de referência).
2. Rode `python scripts/fetch_current_values.py` — ele deve reportar `OK`.

## Fontes oficiais utilizadas (valores de 2026 — todas do governo)

- Salário mínimo R$ 1.621,00 — [Decreto nº 12.797/2025 (Planalto)](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm) e [Banco Central, série SGS 1619](https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados/ultimos/1?formato=json)
- Tabela e teto do INSS (R$ 8.475,55) — Portaria Interministerial MPS/MF nº 13, de 09/01/2026; [tabela oficial no gov.br/INSS](https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/tabela-de-contribuicao-mensal)
- Tabela progressiva mensal do IRRF — [Lei nº 15.191/2025 (Câmara dos Deputados)](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15191-11-agosto-2025-797839-publicacaooriginal-176105-pl.html)
- Redutor do IR 2026 (isenção até R$ 5.000) — [Lei nº 15.270/2025 (Câmara dos Deputados)](https://www2.camara.leg.br/legin/fed/lei/2025/lei-15270-26-novembro-2025-798354-publicacaooriginal-177117-pl.html) e [orientação de cálculo da Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/dezembro/receita-federal-orienta-fontes-pagadoras-e-contribuintes-a-calcular-a-reducao-do-imposto-de-renda-a-partir-de-1o-de-janeiro-de-2026)
- Dedução por dependente (R$ 189,59/mês) — Lei nº 9.250/1995, art. 4º, III (redação da Lei nº 13.149/2015)

## Aviso legal

Esta skill fornece estimativas e orientação geral com base na CLT e em tabelas oficiais públicas. Não constitui consultoria jurídica. Convenções e acordos coletivos (CCT/ACT), situações de estabilidade e decisões judiciais podem alterar os resultados — confirme sempre com o contador ou advogado trabalhista da empresa.

---
Autor: Michael Ferro Pereira
