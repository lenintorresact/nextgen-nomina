"""Generación de documentos PDF de nómina (rol de pagos) con ReportLab.

Produce dos documentos a partir del cálculo del `PayrollEngine`:
- `build_payslip_pdf`: rol de pagos individual de un empleado en un período.
- `build_consolidated_pdf`: rol de pagos consolidado de toda la empresa.

Las funciones devuelven los bytes del PDF (para servir como descarga).
"""
from io import BytesIO
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)

# Paleta alineada con el tema "Menta fresca" del frontend.
_MINT = colors.HexColor("#16B69E")
_MINT_DARK = colors.HexColor("#0E9A85")
_MINT_SOFT = colors.HexColor("#DFF4EF")
_INK = colors.HexColor("#1F2A2A")
_LINE = colors.HexColor("#E7F0EC")


def _money(value: float) -> str:
    return f"${(value or 0):,.2f}"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Brand", parent=styles["Title"], textColor=_MINT_DARK, fontSize=18))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], textColor=_INK, fontSize=9))
    styles.add(ParagraphStyle("H2", parent=styles["Heading2"], textColor=_INK, fontSize=11))
    return styles


def _header(company: Dict, title: str, period: str, styles) -> List:
    name = company.get("name", "Empresa")
    ruc = company.get("ruc", "")
    return [
        Paragraph(name, styles["Brand"]),
        Paragraph(f"RUC: {ruc}", styles["Sub"]),
        Paragraph(f"<b>{title}</b> &nbsp;·&nbsp; Período {period}", styles["Sub"]),
        Spacer(1, 6 * mm),
    ]


def _two_column_section(title: str, rows: List, total_label: str, total: float, styles) -> Table:
    """Una sección (Ingresos o Descuentos) como tabla concepto/monto con total."""
    data = [[title, ""]]
    for concept, amount in rows:
        data.append([concept, _money(amount)])
    data.append([total_label, _money(total)])

    table = Table(data, colWidths=[110 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _MINT_SOFT),
        ("TEXTCOLOR", (0, 0), (-1, 0), _MINT_DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, -2), (-1, -2), 0.5, _LINE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def build_payslip_pdf(company: Dict, employee, calc: Dict, period: str) -> bytes:
    """Rol de pagos individual de un empleado para un período YYYY-MM."""
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)

    elements = _header(company, "ROL DE PAGOS", period, styles)
    elements.append(Paragraph(
        f"<b>{employee.first_name} {employee.last_name}</b> &nbsp;·&nbsp; "
        f"Cédula {employee.cedula} &nbsp;·&nbsp; Sueldo base {_money(employee.salary)}",
        styles["Sub"],
    ))
    elements.append(Spacer(1, 5 * mm))

    earnings = calc.get("earnings_breakdown", {})
    deductions = calc.get("deductions_breakdown", {})
    total_earnings = sum(earnings.values())
    total_deductions = sum(deductions.values())

    elements.append(_two_column_section(
        "INGRESOS", list(earnings.items()), "Total ingresos", total_earnings, styles))
    elements.append(Spacer(1, 4 * mm))
    elements.append(_two_column_section(
        "DESCUENTOS", list(deductions.items()), "Total descuentos", total_deductions, styles))
    elements.append(Spacer(1, 4 * mm))

    net = Table([["LÍQUIDO A RECIBIR", _money(calc.get("net_salary", 0))]],
                colWidths=[110 * mm, 40 * mm])
    net.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _MINT),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(net)
    elements.append(Spacer(1, 6 * mm))

    # Provisiones / costo del empleador (informativo, no afecta el líquido).
    prov_rows = [
        ("Décimo Tercero (13º)", calc.get("thirteenth_salary", 0)),
        ("Décimo Cuarto (14º)", calc.get("fourteenth_salary", 0)),
        ("Fondos de Reserva", calc.get("reserve_funds", 0)),
        ("Provisión de Vacaciones", calc.get("vacation_provision", 0)),
        ("Aporte Patronal IESS", calc.get("iess_employer", 0)),
    ]
    elements.append(Paragraph("Provisiones y aportes (costo del empleador)", styles["H2"]))
    prov = Table([[c, _money(v)] for c, v in prov_rows], colWidths=[110 * mm, 40 * mm])
    prov.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#7B8A86")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, _LINE),
    ]))
    elements.append(prov)

    elements.append(Spacer(1, 16 * mm))
    sign = Table([["_______________________", "_______________________"],
                  ["Empleador", "Empleado"]], colWidths=[75 * mm, 75 * mm])
    sign.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(sign)

    doc.build(elements)
    return buffer.getvalue()


def build_consolidated_pdf(company: Dict, rows: List[Dict], period: str, totals: Dict) -> bytes:
    """Rol de pagos consolidado: una fila por empleado más totales de la empresa.

    `rows`: lista de dicts con first_name, last_name, base_salary y el cálculo.
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)

    elements = _header(company, "ROL DE PAGOS CONSOLIDADO", period, styles)

    header = ["Empleado", "Sueldo base", "Ingresos", "IESS", "Imp. Renta", "Líquido"]
    data = [header]
    for r in rows:
        earnings = r.get("earnings_breakdown", {})
        data.append([
            f"{r.get('first_name', '')} {r.get('last_name', '')}",
            _money(r.get("base_salary", 0)),
            _money(sum(earnings.values())),
            _money(r.get("iess_employee", 0)),
            _money(r.get("income_tax", 0)),
            _money(r.get("net_salary", 0)),
        ])
    data.append([
        "TOTALES",
        "",
        "",
        _money(totals.get("iess_employee", 0)),
        _money(totals.get("income_tax", 0)),
        _money(totals.get("net_salary", 0)),
    ])

    table = Table(data, colWidths=[55 * mm, 24 * mm, 24 * mm, 22 * mm, 23 * mm, 24 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _MINT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), _MINT_SOFT),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FBF9")]),
    ]))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
