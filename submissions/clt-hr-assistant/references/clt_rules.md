# Referência de Regras da CLT (Brasil)

Referência para o agente responder dúvidas trabalhistas brasileiras e fazer cálculos de folha. A base legal está citada em cada regra. Os valores oficiais vigentes (salário mínimo, INSS, IRRF, alíquotas do FGTS) ficam em `assets/tables_2026.json` — nunca use valores fixos deste arquivo.

## 1. Jornada de trabalho e horas extras

- Limite padrão: 8h/dia, 44h/semana (CF/88, art. 7º, XIII; CLT art. 58).
- Horas extras: máx. 2h/dia, pagas com no mínimo +50% sobre a hora normal (CF/88 art. 7º, XVI; CLT art. 59). Domingos/feriados: +100% (Lei 605/49; Súmula 146 TST).
- Trabalho noturno (urbano): 22h–5h, hora reduzida de 52min30s, adicional noturno mínimo de +20% (CLT art. 73).
- Banco de horas: regime de compensação que substitui o pagamento de horas extras. Por acordo individual escrito: compensação em até 6 meses. Por CCT/ACT: em até 1 ano (CLT art. 59, §§2º, 5º, 6º). Saldo não compensado na rescisão deve ser pago como hora extra.
- Intervalo intrajornada: mínimo de 1h (jornada > 6h); supressão parcial é paga como indenização com +50% apenas sobre o tempo suprimido (CLT art. 71, §4º).

## 2. Férias

- 30 dias corridos após cada período aquisitivo de 12 meses (CLT art. 129–130). Reduzidas por faltas injustificadas conforme a tabela do art. 130 (>5 faltas começa a reduzir).
- Pagamento: salário + 1/3 constitucional (CF/88 art. 7º, XVII), até 2 dias antes do início (CLT art. 145).
- Podem ser fracionadas em até 3 períodos, um ≥ 14 dias e os demais ≥ 5 dias, com concordância do empregado (CLT art. 134, §1º).
- Abono pecuniário: o empregado pode vender 1/3 dos dias de férias (CLT art. 143).
- Férias vencidas pagas após o período concessivo (dobra do período) são devidas em dobro (CLT art. 137).
- Férias proporcionais: 1/12 do salário por mês trabalhado no período aquisitivo em curso (fração ≥ 15 dias conta como mês inteiro — CLT art. 146, parágrafo único), mais 1/3.

## 3. 13º salário (décimo terceiro)

- 1/12 do salário de dezembro por mês trabalhado no ano-calendário; fração ≥ 15 dias conta como mês inteiro (Lei 4.090/62; Lei 4.749/65).
- Pago em duas parcelas: 1ª entre 1º/fev e 30/nov (50%, sem descontos), 2ª até 20/dez (com INSS/IRRF sobre o valor total).
- INSS e IRRF sobre o 13º são calculados separadamente do salário mensal (tributação exclusiva — Lei 7.713/88, art. 26; RIR).

## 4. Aviso prévio

- Mínimo de 30 dias; +3 dias por ano completo de serviço no mesmo empregador, limitado a 90 dias no total (CF/88 art. 7º, XXI; Lei 12.506/2011). Os dias adicionais valem quando o empregador demite; no pedido de demissão o empregado deve apenas 30 dias.
- Aviso trabalhado (demissão pelo empregador): redução de 2h/dia ou 7 dias a menos, à escolha do empregado (CLT art. 488).
- O aviso indenizado projeta a data de término do contrato para todos os efeitos legais — tempo de casa, 13º e férias proporcionais contam até a data projetada (CLT art. 487, §1º; OJ 82 SDI-1 TST).
- Aviso indenizado pago pelo empregador é isento de INSS e IRRF (o FGTS **incide** sobre o aviso indenizado; isenção de IRRF: RIR/2018 art. 35, XII; não incidência de INSS: Decreto 3.048/99 com alterações).

## 5. FGTS

- O empregador deposita 8% da remuneração mensal (Lei 8.036/90). Não é descontado do empregado.
- Demissão sem justa causa: o empregador paga multa de 40% sobre o total do saldo depositado (Lei 8.036/90, art. 18, §1º). A contribuição social adicional de 10% foi extinta para rescisões a partir de 01/01/2020 (Lei 13.932/2019).
- Acordo mútuo (art. 484-A): multa de 20%, saque de até 80% do saldo, sem seguro-desemprego.
- O FGTS também incide sobre 13º, horas extras e aviso indenizado.

## 6. Tipos de rescisão e o que é devido

| Verba | Sem justa causa | Pedido de demissão | Justa causa | Acordo (484-A) | Fim de contrato por prazo determinado |
|---|---|---|---|---|---|
| Saldo de salário | ✔ | ✔ | ✔ | ✔ | ✔ |
| Aviso prévio | ✔ (trabalhado ou indenizado, 30+3/ano) | empregado deve 30d (descontável se não cumprido — CLT art. 487, §2º) | ✘ | ✔ metade, se indenizado | ✘ |
| 13º proporcional | ✔ | ✔ | ✘ | ✔ | ✔ |
| Férias vencidas + 1/3 | ✔ | ✔ | ✔ | ✔ | ✔ |
| Férias proporcionais + 1/3 | ✔ | ✔ (Súmula 261 TST) | ✘ (CLT art. 146–147) | ✔ | ✔ |
| Multa FGTS | 40% | ✘ | ✘ | 20% | ✘ |
| Saque FGTS | ✔ (100%) | ✘ | ✘ | ✔ (80%) | ✔ |
| Seguro-desemprego | ✔ (se elegível) | ✘ | ✘ | ✘ | ✘ |

- Hipóteses de justa causa: CLT art. 482. Rescisão indireta (culpa do empregador — empregado recebe tudo como sem justa causa): CLT art. 483.
- Prazo para pagar a rescisão: 10 dias corridos do fim do contrato (CLT art. 477, §6º); multa de 1 salário se atrasar (§8º).
- Falecimento do empregado: tratado como pedido de demissão para as verbas, pagas aos dependentes (Lei 6.858/80).

## 7. Fórmulas do cálculo rescisório

Salário-base para os cálculos = salário contratual + média das variáveis habituais (horas extras, comissões, adicionais) — Súmula 264 TST.

- **Saldo de salário** = (salário ÷ 30) × dias trabalhados no último mês.
- **Aviso prévio indenizado** = (salário ÷ 30) × dias de aviso (30 + 3 × anos completos, máx. 90).
- **13º proporcional** = (salário ÷ 12) × meses contados no ano-calendário até a data projetada de término.
- **Férias proporcionais** = (salário ÷ 12) × meses do período aquisitivo em curso até a data projetada, + 1/3.
- **Férias vencidas** = salário × número de períodos completos não gozados, + 1/3 (em dobro se o período concessivo expirou).
- **Multa FGTS** = alíquota da multa × saldo do FGTS (se o saldo for desconhecido, estime 8% × salário × meses trabalhados e sinalize como estimativa).

### Tratamento tributário na rescisão

- Tributados (INSS + IRRF): saldo de salário; 13º (cálculo separado/exclusivo); aviso trabalhado.
- Isentos de INSS e IRRF: aviso indenizado, férias indenizadas (vencidas e proporcionais) + 1/3 (Súmula 386 STJ; RIR/2018 art. 35), multa e saques do FGTS.
- INSS: faixas progressivas aplicadas fatia a fatia, limitado à contribuição do teto.
- IRRF: base = valor tributável − INSS − (dependentes × dedução por dependente), ou − desconto simplificado se for maior; aplique a tabela progressiva e depois subtraia o redutor da Lei 15.270/2025 `max(0; 978,62 − 0,133145 × rendimento tributável mensal)` quando o rendimento tributável mensal for ≤ R$ 7.350,00 (isenção total, na prática, até R$ 5.000,00). O redutor nunca excede o imposto apurado.

## 8. Âncoras para dúvidas frequentes

- Contrato de experiência: máx. 90 dias, uma prorrogação permitida dentro desse limite (CLT art. 443, §2º, "c"; art. 445, parágrafo único). Rescisão antecipada sem justa causa pelo empregador: indenização de metade dos salários restantes (CLT art. 479).
- Licença-maternidade: 120 dias (CF/88 art. 7º, XVIII; CLT art. 392); estabilidade da confirmação da gravidez até 5 meses após o parto (ADCT art. 10, II, "b").
- Licença-paternidade: 5 dias (ADCT art. 10, §1º) — ampliável pelo programa Empresa Cidadã.
- Afastamento por doença: primeiros 15 dias pagos pelo empregador; a partir do 16º, benefício do INSS (Lei 8.213/91, art. 60).
- Estabilidades a sinalizar: gestantes, membros da CIPA (da eleição até 1 ano após o mandato), retorno de acidente de trabalho (12 meses — Lei 8.213/91 art. 118), dirigentes sindicais.
- Equiparação salarial: CLT art. 461 (mesma função, mesmo empregador, mesmo estabelecimento, diferenças < 2 anos na função / < 4 na empresa).

## 9. Fontes oficiais para valores vigentes (todas do governo)

- Salário mínimo 2026 (R$ 1.621,00): Decreto nº 12.797/2025 — https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12797.htm ; série ao vivo: API SGS do Banco Central, série 1619 (usada por `scripts/fetch_current_values.py`).
- Tabela INSS 2026: Portaria Interministerial MPS/MF nº 13, de 09/01/2026 — tabela oficial em https://www.gov.br/inss/pt-br/direitos-e-deveres/inscricao-e-contribuicao/tabela-de-contribuicao-mensal (nova portaria publicada todo janeiro).
- Tabela progressiva mensal do IRRF (vigente desde maio/2025): Lei nº 15.191/2025 — https://www2.camara.leg.br/legin/fed/lei/2025/lei-15191-11-agosto-2025-797839-publicacaooriginal-176105-pl.html
- Redutor do IR 2026 (isenção até R$ 5.000): Lei nº 15.270/2025 — https://www2.camara.leg.br/legin/fed/lei/2025/lei-15270-26-novembro-2025-798354-publicacaooriginal-177117-pl.html ; orientação de cálculo da Receita Federal — https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/dezembro/receita-federal-orienta-fontes-pagadoras-e-contribuintes-a-calcular-a-reducao-do-imposto-de-renda-a-partir-de-1o-de-janeiro-de-2026
- Dedução mensal por dependente (R$ 189,59): Lei nº 9.250/1995, art. 4º, III (redação da Lei nº 13.149/2015).
