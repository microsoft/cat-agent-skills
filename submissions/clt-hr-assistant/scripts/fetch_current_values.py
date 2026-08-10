#!/usr/bin/env python3
"""Busca valores oficiais vigentes da folha brasileira e valida as tabelas locais.

Estratégia
----------
1. Salário mínimo: buscado ao vivo na API SGS do Banco Central do Brasil
   (série 1619 - "Salário mínimo"), fonte oficial, estruturada e estável:
   https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados/ultimos/1?formato=json
2. Tabelas de INSS e IRRF: o Brasil publica essas tabelas apenas como páginas
   web / PDFs (sem API oficial estruturada), por isso elas ficam empacotadas em
   assets/tables_2026.json. Este script VALIDA o pacote contra o salário mínimo
   ao vivo: a primeira faixa do INSS deve terminar exatamente no salário mínimo
   vigente. Se não terminar, as tabelas são marcadas como DESATUALIZADAS e o
   agente deve confirmar os valores vigentes no gov.br (Receita Federal / INSS)
   antes de calcular.

Uso
---
    python fetch_current_values.py            # resumo legível
    python fetch_current_values.py --json     # JSON consolidado no stdout
    python fetch_current_values.py --offline  # pula a busca ao vivo (só o pacote)

Códigos de saída: 0 = OK, 1 = tabelas desatualizadas ou pacote ausente,
2 = rede indisponível (o pacote ainda é impresso; trate os valores como
dados do "ano de referência").
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

BCB_MIN_WAGE_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados/ultimos/1?formato=json"
)
BUNDLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "tables_2026.json"


def fetch_minimum_wage(timeout: int = 15):
    """Retorna (valor, data_de_referencia) da API SGS do BCB, ou lança exceção."""
    req = urllib.request.Request(
        BCB_MIN_WAGE_URL, headers={"User-Agent": "clt-hr-assistant/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    latest = data[-1]
    # A SGS retorna, por exemplo: [{"data": "01/01/2026", "valor": "1621.00"}]
    return float(str(latest["valor"]).replace(",", ".")), latest["data"]


def load_bundle():
    if not BUNDLE_PATH.exists():
        sys.stderr.write(f"ERRO: tabelas empacotadas não encontradas em {BUNDLE_PATH}\n")
        sys.exit(1)
    with open(BUNDLE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="imprime o JSON consolidado")
    parser.add_argument("--offline", action="store_true", help="pula a busca ao vivo")
    args = parser.parse_args()

    bundle = load_bundle()
    result = dict(bundle)
    result["live_check"] = {"performed": False, "stale": None, "notes": []}
    exit_code = 0

    if not args.offline:
        try:
            live_wage, live_date = fetch_minimum_wage()
            result["live_check"]["performed"] = True
            result["live_check"]["live_minimum_wage"] = live_wage
            result["live_check"]["live_reference_date"] = live_date
            first_bracket_top = bundle["inss"]["brackets"][0]["up_to"]
            stale = (
                abs(live_wage - bundle["minimum_wage"]) > 0.01
                or abs(live_wage - first_bracket_top) > 0.01
            )
            result["live_check"]["stale"] = stale
            if stale:
                exit_code = 1
                result["minimum_wage"] = live_wage
                result["live_check"]["notes"].append(
                    "TABELAS DESATUALIZADAS: o salário mínimo ao vivo (R$ %.2f, %s) "
                    "não bate com as tabelas empacotadas (ano de referência %s). O "
                    "salário mínimo foi atualizado a partir do valor ao vivo, mas as "
                    "faixas de INSS/IRRF podem estar defasadas. Confirme as tabelas "
                    "vigentes no gov.br (Receita Federal / INSS) antes de calcular e "
                    "atualize assets/tables_2026.json."
                    % (live_wage, live_date, bundle.get("reference_year"))
                )
            else:
                result["live_check"]["notes"].append(
                    "OK: as tabelas empacotadas estão consistentes com o salário "
                    "mínimo oficial ao vivo (R$ %.2f, %s)." % (live_wage, live_date)
                )
        except Exception as exc:  # rede bloqueada, timeout, mudança na API...
            exit_code = 2
            result["live_check"]["notes"].append(
                "Busca ao vivo indisponível (%s: %s). Usando as tabelas empacotadas "
                "do ano de referência %s - informe isso na resposta."
                % (type(exc).__name__, exc, bundle.get("reference_year"))
            )

    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"Ano de referência das tabelas    : {bundle.get('reference_year')}")
        print(f"Salário mínimo                   : R$ {result['minimum_wage']:,.2f}")
        print(f"Teto salarial do INSS            : R$ {bundle['inss']['ceiling_salary']:,.2f}")
        print(f"Contribuição máxima do INSS      : R$ {bundle['inss']['max_contribution']:,.2f}")
        irrf = bundle["irrf"]
        print(f"IRRF isento até (tabela)         : R$ {irrf['brackets'][0]['up_to']:,.2f}")
        law = irrf["law_15270_2025"]
        print(f"Isenção total IRRF (Lei 15.270)  : R$ {law['full_exemption_up_to']:,.2f}")
        print(f"Redutor IRRF aplicável até       : R$ {law['phase_out_up_to']:,.2f}")
        for note in result["live_check"]["notes"]:
            print(f"\n[{'!' if exit_code else 'i'}] {note}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
