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


# Columnas de la planilla de aportes IESS. Editable: cada columna es
# (etiqueta, función(row, c) -> valor). `c` es el LegalYear con las tasas.
# `row` trae cedula, first_name, last_name, days, taxable, reserve_funds.
PLANILLA_COLUMNS = [
    ("Cédula", lambda r, c: r.get("cedula", "")),
    ("Empleado", lambda r, c: f"{r.get('first_name', '')} {r.get('last_name', '')}"),
    ("Días", lambda r, c: str(r.get("days", 30))),
    ("Sueldo imponible", lambda r, c: _money(r.get("taxable", 0))),
    ("Ap. personal 9.45%", lambda r, c: _money(r.get("taxable", 0) * c.iess_employee)),
    ("Ap. patronal 11.15%", lambda r, c: _money(r.get("taxable", 0) * c.iess_employer_iess)),
    ("IECE 0.5%", lambda r, c: _money(r.get("taxable", 0) * c.iece_rate)),
    ("SECAP 0.5%", lambda r, c: _money(r.get("taxable", 0) * c.secap_rate)),
    ("F. reserva 8.33%", lambda r, c: _money(r.get("reserve_funds", 0))),
    ("Total", lambda r, c: _money(
        r.get("taxable", 0) * (c.iess_employee + c.iess_employer) + r.get("reserve_funds", 0)
    )),
]


def build_planilla_iess_pdf(company: Dict, rows: List[Dict], period: str, constants) -> bytes:
    """Planilla de aportes IESS (PDF legible): desglose por empleado y totales.

    Columnas definidas en PLANILLA_COLUMNS (editable). `constants` es el LegalYear
    con las tasas vigentes; `rows` trae por empleado cedula/nombre/days/taxable/
    reserve_funds (días por defecto 30: el run mensual no registra días trabajados).
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm)

    elements = _header(company, "PLANILLA DE APORTES IESS", period, styles)
    elements.append(Paragraph(
        "Pago hasta el día 15 del mes siguiente. Aporte patronal total 12.15% "
        "(11.15% IESS + 0.5% IECE + 0.5% SECAP).", styles["Sub"]))
    elements.append(Spacer(1, 4 * mm))

    header = [c[0] for c in PLANILLA_COLUMNS]
    data = [header]
    # Totales de las columnas numéricas (todas menos Cédula/Empleado/Días).
    numeric_totals = [0.0] * len(PLANILLA_COLUMNS)
    for r in rows:
        taxable = r.get("taxable", 0)
        reserve = r.get("reserve_funds", 0)
        data.append([fn(r, constants) for _, fn in PLANILLA_COLUMNS])
        numeric_totals[3] += taxable
        numeric_totals[4] += taxable * constants.iess_employee
        numeric_totals[5] += taxable * constants.iess_employer_iess
        numeric_totals[6] += taxable * constants.iece_rate
        numeric_totals[7] += taxable * constants.secap_rate
        numeric_totals[8] += reserve
        numeric_totals[9] += taxable * (constants.iess_employee + constants.iess_employer) + reserve

    total_row = ["TOTALES", "", ""] + [_money(v) for v in numeric_totals[3:]]
    data.append(total_row)

    col_widths = [22 * mm, 38 * mm, 9 * mm, 22 * mm, 20 * mm, 21 * mm, 14 * mm, 15 * mm, 19 * mm, 20 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _MINT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), _MINT_SOFT),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FBF9")]),
    ]))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


# Filas del Formulario 107 (comprobante de retenciones en relación de dependencia).
# Editable: cada fila es (casillero, etiqueta, clave en `data`). El nº de casillero
# es opcional — solo se imprimen los CONFIRMADOS contra la fuente oficial del SRI
# (303 sobresueldos/comisiones; 407 impuesto retenido). Los demás quedan en None
# hasta confirmar el instructivo oficial; completar aquí cuando se disponga de él.
FORM107_ROWS = [
    (None, "Ingresos gravados con este empleador", "ingresos_gravados"),
    ("303", "Sobresueldos, comisiones, bonos y otros ingresos gravados", "sobresueldos"),
    (None, "(-) Aporte personal IESS", "aporte_iess"),
    (None, "Base imponible gravada", "base_imponible"),
    (None, "Impuesto a la renta causado", "impuesto_causado_bruto"),
    (None, "(-) Rebaja por gastos personales", "rebaja_gastos"),
    (None, "Impuesto a la renta causado (neto)", "impuesto_causado_neto"),
    ("407", "Valor del impuesto retenido", "impuesto_retenido"),
    (None, "Impuesto asumido por el empleador", "impuesto_asumido"),
]


# Columnas del reporte de décimos (13º y 14º). Editable: (etiqueta, fn(row)).
# `row` trae cedula, first_name, last_name, thirteenth, fourteenth, forma_13, forma_14.
DECIMOS_COLUMNS = [
    ("Cédula", lambda r: r.get("cedula", "")),
    ("Empleado", lambda r: f"{r.get('first_name', '')} {r.get('last_name', '')}"),
    ("Décimo Tercero", lambda r: _money(r.get("thirteenth", 0))),
    ("Forma pago 13º", lambda r: r.get("forma_13", "")),
    ("Décimo Cuarto", lambda r: _money(r.get("fourteenth", 0))),
    ("Forma pago 14º", lambda r: r.get("forma_14", "")),
]


def build_decimos_pdf(company: Dict, rows: List[Dict], year: int,
                      projected: bool = False) -> bytes:
    """Reporte de décimos (13º y 14º) de la empresa para un ejercicio.

    Columnas en DECIMOS_COLUMNS (editable). Resumen interno / de conciliación; el
    archivo de carga oficial del SUT (Ministerio de Trabajo) se genera aparte una
    vez confirmada su plantilla. `projected` marca valores proyectados (sin roles).
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm)

    elements = _header(company, "REPORTE DE DÉCIMOS (13º Y 14º)", str(year), styles)
    elements.append(Paragraph(
        "13º: pago hasta el 24 de diciembre. 14º: hasta el 15 de marzo (Costa/Insular) "
        "o 15 de agosto (Sierra/Amazonía). Registro en el SUT según 9º dígito del RUC.",
        styles["Sub"]))
    if projected:
        elements.append(Paragraph(
            "<b>VALORES PROYECTADOS</b> (sin roles cerrados; estimado).", styles["Sub"]))
    elements.append(Spacer(1, 4 * mm))

    header = [c[0] for c in DECIMOS_COLUMNS]
    data = [header]
    total_13 = total_14 = 0.0
    for r in rows:
        data.append([fn(r) for _, fn in DECIMOS_COLUMNS])
        total_13 += r.get("thirteenth", 0)
        total_14 += r.get("fourteenth", 0)
    data.append(["TOTALES", "", _money(total_13), "", _money(total_14), ""])

    table = Table(data, colWidths=[24 * mm, 48 * mm, 28 * mm, 26 * mm, 28 * mm, 26 * mm],
                  repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _MINT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), _MINT_SOFT),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F7FBF9")]),
    ]))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()


def build_form107_pdf(company: Dict, employee, data: Dict, year: int,
                      projected: bool = False) -> bytes:
    """Comprobante de retenciones (Formulario 107) anual de un empleado.

    Filas definidas en FORM107_ROWS (editable). `data` mapea cada clave a su valor
    anual. Si `projected` es True, los valores se proyectaron (mes × 12) por falta
    de roles cerrados y se marca como tal.
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)

    elements = _header(company, "COMPROBANTE DE RETENCIONES — FORMULARIO 107", str(year), styles)
    elements.append(Paragraph(
        f"<b>{employee.first_name} {employee.last_name}</b> &nbsp;·&nbsp; "
        f"Cédula {employee.cedula} &nbsp;·&nbsp; Ejercicio fiscal {year}", styles["Sub"]))
    if projected:
        elements.append(Paragraph(
            "<b>VALORES PROYECTADOS</b> (no hay roles cerrados del ejercicio; "
            "estimado como mes × 12).", styles["Sub"]))
    elements.append(Spacer(1, 5 * mm))

    table_data = [["Casillero", "Concepto", "Valor"]]
    for casillero, label, key in FORM107_ROWS:
        table_data.append([casillero or "", label, _money(data.get(key, 0))])

    table = Table(table_data, colWidths=[20 * mm, 110 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _MINT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, _LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FBF9")]),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        "Nota: los números de casillero no confirmados contra el instructivo oficial del SRI "
        "se dejan en blanco. Entrega al empleado hasta el 31 de enero del año siguiente.",
        styles["Sub"]))

    elements.append(Spacer(1, 14 * mm))
    sign = Table([["_______________________"], ["Agente de retención (empleador)"]],
                 colWidths=[90 * mm])
    sign.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                              ("FONTSIZE", (0, 0), (-1, -1), 8)]))
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
