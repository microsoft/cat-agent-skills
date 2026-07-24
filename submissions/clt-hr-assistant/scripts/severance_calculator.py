#!/usr/bin/env python3
"""Calculadora de verbas rescisórias (Brasil) com memória de cálculo completa.

Implementa as regras da CLT para os cinco tipos comuns de rescisão, usando as
tabelas oficiais empacotadas em assets/tables_2026.json (opcionalmente
validadas/atualizadas por fetch_current_values.py). Gera uma "memória de
cálculo": uma linha por verba, os descontos (INSS/IRRF) e o total líquido.

Exemplos
--------
    python severance_calculator.py \
        --salary 3500 --hire-date 2022-03-01 --end-date 2026-07-24 \
        --type sem_justa_causa --notice indemnified --dependents 1

    python severance_calculator.py --salary 4200 --hire-date 2020-01-10 \
        --end-date 2026-07-31 --type pedido_demissao --notice worked --json

Tipos de rescisão: sem_justa_causa | pedido_demissao | justa_causa |
                   acordo_mutuo | termino_contrato

Simplificações (sinalizadas na saída): o saldo do FGTS, quando não informado,
é estimado como 8% x salário x meses trabalhados; médias de variáveis devem
ser passadas já consolidadas em --salary ou via --avg-variables; convenções e
acordos coletivos (CCT/ACT) não são considerados.
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

TABLES_PATH = Path(__file__).resolve().parent.parent / "assets" / "tables_2026.json"

TYPES = (
    "sem_justa_causa",
    "pedido_demissao",
    "justa_causa",
    "acordo_mutuo",
    "termino_contrato",
)


# ----------------------------------------------------------------------------
# Auxiliares de datas
# ----------------------------------------------------------------------------
def parse_date(s):
    return date.fromisoformat(s)


def complete_years(start, end):
    years = end.year - start.year
    if (end.month, end.day) < (start.month, start.day):
        years -= 1
    return max(0, years)


def add_months(d, months):
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
                      else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def months_with_15_days(period_start, period_end):
    """Conta meses entre as datas (fração >= 15 dias conta como mês inteiro)."""
    if period_end < period_start:
        return 0
    months = 0
    cursor = period_start
    while cursor <= period_end:
        nxt = add_months(cursor, 1)
        segment_end = min(period_end, nxt - timedelta(days=1))
        days = (segment_end - cursor).days + 1
        if days >= 15:
            months += 1
        cursor = nxt
    return min(months, 12)


# ----------------------------------------------------------------------------
# Cálculos tributários
# ----------------------------------------------------------------------------
def calc_inss(base, tables):
    """Contribuição progressiva do empregado ao INSS, limitada ao teto."""
    if base <= 0:
        return 0.0
    brackets = tables["inss"]["brackets"]
    ceiling = tables["inss"]["ceiling_salary"]
    base = min(base, ceiling)
    total, prev_top = 0.0, 0.0
    for br in brackets:
        top = br["up_to"]
        if base > prev_top:
            total += (min(base, top) - prev_top) * br["rate"]
            prev_top = top
        else:
            break
    return round(total, 2)


def calc_irrf(taxable_income, inss_paid, dependents, tables):
    """IRRF com desconto legal vs. simplificado e redutor da Lei 15.270/2025.

    taxable_income: rendimento tributável bruto mensal (antes do INSS).
    Retorna (imposto, dicionário de detalhes).
    """
    irrf = tables["irrf"]
    if taxable_income <= 0:
        return 0.0, {"base": 0.0, "method": "n/a", "reduction": 0.0}

    legal_deductions = inss_paid + dependents * irrf["dependent_deduction_monthly"]
    simplified = irrf["simplified_discount_monthly"]
    use_simplified = simplified > legal_deductions
    base = taxable_income - (simplified if use_simplified else legal_deductions)
    base = max(0.0, base)

    tax = 0.0
    for br in irrf["brackets"]:
        top = br["up_to"]
        if top is None or base <= top:
            tax = base * br["rate"] - br["deduction"]
            break
    tax = max(0.0, tax)

    # Lei 15.270/2025: redutor para rendimento tributável mensal até o limite
    law = irrf["law_15270_2025"]
    reduction = 0.0
    if taxable_income <= law["phase_out_up_to"]:
        reduction = max(0.0, 978.62 - 0.133145 * taxable_income)
        reduction = min(reduction, tax)
    tax = round(max(0.0, tax - reduction), 2)
    return tax, {
        "base": round(base, 2),
        "method": "desconto_simplificado" if use_simplified else "deducoes_legais",
        "reduction": round(reduction, 2),
    }


# ----------------------------------------------------------------------------
# Rescisão
# ----------------------------------------------------------------------------
def notice_days_for(ttype, notice_mode, years, tables):
    np = tables["notice_period"]
    if ttype in ("justa_causa", "termino_contrato") or notice_mode == "none":
        return 0
    if ttype == "pedido_demissao":
        return np["base_days"]  # o empregado deve apenas 30 dias
    days = np["base_days"] + np["extra_days_per_year"] * years
    return min(days, np["max_days"])


def calculate(args, tables):
    salary = args.salary + args.avg_variables
    hire, end = args.hire_date, args.end_date
    if end <= hire:
        sys.exit("ERRO: a data de desligamento deve ser posterior à admissão")

    years = complete_years(hire, end)
    notice_days = notice_days_for(args.type, args.notice, years, tables)
    indemnified = args.notice == "indemnified" and notice_days > 0

    # O aviso indenizado projeta o fim do contrato (CLT art. 487 §1º)
    projected_end = end + timedelta(days=notice_days) if indemnified else end

    lines, notes = [], []
    exempt_total, taxable_salary_part = 0.0, 0.0

    # --- Saldo de salário -----------------------------------------------------
    days_in_month = end.day
    saldo = round(salary / 30 * min(days_in_month, 30), 2)
    lines.append(("Saldo de salário", f"{salary:.2f}/30 × {min(days_in_month,30)} dias", saldo, "taxable"))
    taxable_salary_part += saldo

    # --- Aviso prévio ---------------------------------------------------------
    if indemnified:
        aviso = round(salary / 30 * notice_days, 2)
        if args.type == "acordo_mutuo":
            aviso = round(aviso / 2, 2)
            lines.append(("Aviso prévio indenizado (metade — art. 484-A)",
                          f"({salary:.2f}/30 × {notice_days}d) ÷ 2", aviso, "exempt"))
        else:
            lines.append(("Aviso prévio indenizado",
                          f"{salary:.2f}/30 × {notice_days} dias (30 + 3/ano, máx. 90)",
                          aviso, "exempt"))
        exempt_total += aviso
    elif args.type == "pedido_demissao" and args.notice == "none":
        desconto = round(salary, 2)
        lines.append(("Desconto: aviso prévio não cumprido (CLT art. 487 §2º)",
                      "− 30 dias de salário", -desconto, "deduction"))
        notes.append("O empregado não cumpriu o aviso; 30 dias descontados (o empregador pode dispensar o desconto).")

    # --- 13º proporcional -----------------------------------------------------
    if args.type != "justa_causa":
        year_start = date(projected_end.year, 1, 1)
        start_13 = max(hire, year_start)
        months_13 = months_with_15_days(start_13, projected_end)
        val_13 = round(salary / 12 * months_13, 2)
        if val_13 > 0:
            lines.append((f"13º proporcional ({months_13}/12)",
                          f"{salary:.2f}/12 × {months_13}", val_13, "taxable_13"))

    # --- Férias vencidas ------------------------------------------------------
    if args.vested_vacations > 0:
        fv = round(salary * args.vested_vacations, 2)
        terco_fv = round(fv / 3, 2)
        lines.append((f"Férias vencidas ({args.vested_vacations} período(s))",
                      f"{salary:.2f} × {args.vested_vacations}", fv, "exempt"))
        lines.append(("1/3 sobre férias vencidas", f"{fv:.2f} ÷ 3", terco_fv, "exempt"))
        exempt_total += fv + terco_fv
        notes.append("Se o período concessivo expirou, as férias vencidas são devidas em DOBRO (CLT art. 137) — não aplicado aqui.")

    # --- Férias proporcionais -------------------------------------------------
    if args.type != "justa_causa":
        # o período aquisitivo em curso começa no último aniversário de admissão
        anniv = add_months(hire, 12 * complete_years(hire, projected_end))
        months_fp = months_with_15_days(anniv, projected_end)
        fp = round(salary / 12 * months_fp, 2)
        terco_fp = round(fp / 3, 2)
        if fp > 0:
            lines.append((f"Férias proporcionais ({months_fp}/12)",
                          f"{salary:.2f}/12 × {months_fp}", fp, "exempt"))
            lines.append(("1/3 sobre férias proporcionais", f"{fp:.2f} ÷ 3", terco_fp, "exempt"))
            exempt_total += fp + terco_fp

    # --- Multa FGTS -----------------------------------------------------------
    fgts = tables["fgts"]
    fine_rate = {"sem_justa_causa": fgts["dismissal_fine_rate"],
                 "acordo_mutuo": fgts["mutual_agreement_fine_rate"]}.get(args.type, 0.0)
    if fine_rate > 0:
        if args.fgts_balance is not None:
            balance = args.fgts_balance
            balance_note = "saldo informado"
        else:
            # estimativa grosseira: 8% por mês ao longo de todo o contrato
            months_total = (projected_end.year - hire.year) * 12 + (projected_end.month - hire.month)
            balance = round(salary * fgts["monthly_rate"] * max(1, months_total), 2)
            balance_note = "ESTIMADO (8% × salário × meses) — substitua pelo extrato real"
        fine = round(balance * fine_rate, 2)
        lines.append((f"Multa FGTS {int(fine_rate*100)}%",
                      f"{fine_rate:.0%} × R$ {balance:.2f} ({balance_note})", fine, "exempt"))
        exempt_total += fine

    # --- Descontos ------------------------------------------------------------
    inss_salary = calc_inss(taxable_salary_part, tables)
    irrf_salary, irrf_info = calc_irrf(taxable_salary_part, inss_salary,
                                       args.dependents, tables)

    val_13_total = sum(v for (_, _, v, kind) in lines if kind == "taxable_13")
    inss_13 = calc_inss(val_13_total, tables)
    irrf_13, irrf_13_info = calc_irrf(val_13_total, inss_13, args.dependents, tables)

    gross = sum(v for (_, _, v, kind) in lines if kind != "deduction")
    discounts_notice = sum(-v for (_, _, v, kind) in lines if kind == "deduction")
    total_deductions = inss_salary + irrf_salary + inss_13 + irrf_13 + discounts_notice
    net = round(gross - total_deductions, 2)

    return {
        "inputs": {
            "salary_base": salary, "hire_date": str(hire), "end_date": str(end),
            "projected_end": str(projected_end), "type": args.type,
            "notice": args.notice, "notice_days": notice_days,
            "dependents": args.dependents, "reference_year": tables.get("reference_year"),
        },
        "lines": [{"verba": n, "formula": f, "value": v, "tax_kind": k}
                  for (n, f, v, k) in lines],
        "deductions": {
            "inss_salary": inss_salary,
            "irrf_salary": irrf_salary, "irrf_salary_info": irrf_info,
            "inss_13": inss_13, "irrf_13": irrf_13, "irrf_13_info": irrf_13_info,
            "notice_discount": round(discounts_notice, 2),
        },
        "totals": {"gross": round(gross, 2),
                   "deductions": round(total_deductions, 2), "net": net},
        "notes": notes + [
            "Aviso indenizado, férias indenizadas + 1/3 e multa do FGTS são isentos de INSS/IRRF.",
            "O 13º é tributado separadamente (tributação exclusiva).",
            "Apenas estimativa — verifique regras de CCT/ACT e confirme com o contador da empresa.",
        ],
    }


def print_report(r):
    print("=" * 72)
    print("MEMÓRIA DE CÁLCULO — VERBAS RESCISÓRIAS")
    print("=" * 72)
    i = r["inputs"]
    print(f"Tipo: {i['type']} | Admissão: {i['hire_date']} | Desligamento: {i['end_date']}")
    print(f"Aviso: {i['notice']} ({i['notice_days']} dias) | Projeção: {i['projected_end']}"
          f" | Salário-base: R$ {i['salary_base']:,.2f} | Tabelas: {i['reference_year']}")
    print("-" * 72)
    for ln in r["lines"]:
        print(f"{ln['verba']:<52} R$ {ln['value']:>12,.2f}")
        print(f"    → {ln['formula']}")
    d = r["deductions"]
    print("-" * 72)
    print(f"{'(-) INSS sobre verbas salariais':<52} R$ {d['inss_salary']:>12,.2f}")
    print(f"{'(-) IRRF sobre verbas salariais':<52} R$ {d['irrf_salary']:>12,.2f}"
          f"   [base R$ {d['irrf_salary_info']['base']:,.2f}, redutor Lei 15.270:"
          f" R$ {d['irrf_salary_info']['reduction']:,.2f}]")
    print(f"{'(-) INSS sobre 13º':<52} R$ {d['inss_13']:>12,.2f}")
    print(f"{'(-) IRRF sobre 13º':<52} R$ {d['irrf_13']:>12,.2f}")
    if d["notice_discount"]:
        print(f"{'(-) Aviso prévio não cumprido':<52} R$ {d['notice_discount']:>12,.2f}")
    t = r["totals"]
    print("=" * 72)
    print(f"{'TOTAL BRUTO':<52} R$ {t['gross']:>12,.2f}")
    print(f"{'TOTAL DESCONTOS':<52} R$ {t['deductions']:>12,.2f}")
    print(f"{'TOTAL LÍQUIDO':<52} R$ {t['net']:>12,.2f}")
    print("=" * 72)
    for n in r["notes"]:
        print(f"* {n}")


def main():
    p = argparse.ArgumentParser(
        description="Calculadora de verbas rescisórias (Brasil).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("--salary", type=float, required=True,
                   help="salário bruto mensal (R$)")
    p.add_argument("--avg-variables", type=float, default=0.0,
                   help="média mensal das variáveis habituais (horas extras, comissões)")
    p.add_argument("--hire-date", type=parse_date, required=True,
                   help="data de admissão, AAAA-MM-DD")
    p.add_argument("--end-date", type=parse_date, required=True,
                   help="último dia trabalhado, AAAA-MM-DD")
    p.add_argument("--type", choices=TYPES, required=True,
                   help="tipo de rescisão")
    p.add_argument("--notice", choices=("worked", "indemnified", "none"),
                   default="indemnified",
                   help="aviso prévio: worked=trabalhado, indemnified=indenizado, none=não cumprido")
    p.add_argument("--vested-vacations", type=int, default=0,
                   help="períodos completos de férias vencidas não gozadas")
    p.add_argument("--dependents", type=int, default=0,
                   help="dependentes para IRRF")
    p.add_argument("--fgts-balance", type=float, default=None,
                   help="saldo do FGTS (R$); estimado se omitido")
    p.add_argument("--tables", type=Path, default=TABLES_PATH,
                   help="caminho do JSON de tabelas (padrão: assets empacotado)")
    p.add_argument("--json", action="store_true",
                   help="saída em JSON em vez do relatório")
    args = p.parse_args()

    if args.salary < 0 or args.avg_variables < 0 or args.vested_vacations < 0 or args.dependents < 0:
        p.error("--salary, --avg-variables, --vested-vacations e --dependents devem ser >= 0")
    if args.fgts_balance is not None and args.fgts_balance < 0:
        p.error("--fgts-balance deve ser >= 0")
    with open(args.tables, encoding="utf-8") as fh:
        tables = json.load(fh)

    result = calculate(args, tables)
    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print_report(result)


if __name__ == "__main__":
    main()
