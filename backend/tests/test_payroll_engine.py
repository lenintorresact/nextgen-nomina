import pytest
from datetime import datetime
from app.models.schemas import (
    Employee, ContractType, Region, PayrollEvent, EventType, SettlementCause
)
from app.services.payroll_engine import PayrollEngine
from app.services import legal_constants


def _event(event_type, amount, description="x"):
    return PayrollEvent(
        employee_id="emp123", company_id="comp1", type=event_type,
        amount=amount, description=description, date=datetime(2026, 6, 1),
    )

C2026 = legal_constants.for_year(2026)


def _employee(**overrides):
    base = dict(
        id="emp123", company_id="comp1", cedula="1712345678",
        first_name="Juan", last_name="Perez", email="juan@example.com",
        salary=1000.0, start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE,
    )
    base.update(overrides)
    return Employee(**base)

def test_basic_payroll_calculation():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE,
        region_override=Region.SIERRA
    )

    events = []

    result = PayrollEngine.process_monthly_payroll(employee, events)

    assert result["taxable_earnings"] == 1000.0
    assert result["iess_employee"] == 94.5
    assert result["iess_employer"] == 121.5
    assert pytest.approx(result["thirteenth_salary"]) == 1000.0 / 12
    assert result["fourteenth_salary"] == 482.0 / 12  # SBU 2026
    assert result["reserve_funds"] == 83.3
    assert pytest.approx(result["vacation_provision"]) == 1000.0 / 24
    assert result["net_salary"] == 1000.0 - 94.5

def test_payroll_with_overtime():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime(2020, 1, 1),
        contract_type=ContractType.INDEFINITE
    )

    events = [
        PayrollEvent(
            employee_id="emp123",
            company_id="comp1",
            type=EventType.OVERTIME_50,
            amount=100.0,
            description="Extra hours",
            date=datetime.now()
        )
    ]

    result = PayrollEngine.process_monthly_payroll(employee, events)

    assert result["taxable_earnings"] == 1100.0
    assert result["iess_employee"] == 1100.0 * 0.0945
    assert result["net_salary"] == 1100.0 - (1100.0 * 0.0945)

def test_no_reserve_funds_for_new_employees():
    employee = Employee(
        id="emp123",
        company_id="comp1",
        cedula="1712345678",
        first_name="Juan",
        last_name="Perez",
        email="juan@example.com",
        salary=1000.0,
        start_date=datetime.now(), # Just started
        contract_type=ContractType.INDEFINITE
    )

    result = PayrollEngine.process_monthly_payroll(employee, [])
    assert result["reserve_funds"] == 0.0


# --- Constantes legales por año ------------------------------------------

def test_for_year_resolves_2026_sbu():
    assert legal_constants.for_year(2026).sbu == 482.0

def test_for_year_falls_back_to_latest_for_future_year():
    # Un año futuro sin tabla usa las constantes más recientes (2026).
    assert legal_constants.for_year(2030).sbu == 482.0

def test_for_year_historic():
    assert legal_constants.for_year(2024).sbu == 460.0


# --- Impuesto a la Renta: tabla -------------------------------------------

def test_ir_tax_below_exempt_fraction_is_zero():
    assert PayrollEngine.calculate_ir_tax(12000.0, C2026) == 0.0

def test_ir_tax_mid_bracket():
    # Base 20.000 → tramo (15.549–20.188): 167 + (20.000-15.549)*0.10
    expected = 167 + (20000.0 - 15549.0) * 0.10
    assert PayrollEngine.calculate_ir_tax(20000.0, C2026) == pytest.approx(expected)

def test_ir_tax_top_bracket():
    # Base 120.000 → último tramo: 24.572 + (120.000-109.956)*0.37
    expected = 24572 + (120000.0 - 109956.0) * 0.37
    assert PayrollEngine.calculate_ir_tax(120000.0, C2026) == pytest.approx(expected)


# --- Impuesto a la Renta: retención mensual -------------------------------

def test_ir_withholding_zero_near_sbu():
    # Un sueldo cercano al SBU proyecta una base bajo la fracción exenta → 0.
    assert PayrollEngine.calculate_ir_withholding(1000.0, C2026) == 0.0

def test_ir_withholding_positive_for_high_earner():
    # Sueldo 3.000: base = 36.000 - IESS personal; cae en tramo 15% → retención > 0.
    monthly = PayrollEngine.calculate_ir_withholding(3000.0, C2026)
    assert monthly > 0
    annual_base = 36000.0 - 36000.0 * C2026.iess_employee
    expected = PayrollEngine.calculate_ir_tax(annual_base, C2026) / 12
    assert monthly == pytest.approx(expected)

def test_personal_expenses_rebate_reduces_withholding():
    without = PayrollEngine.calculate_ir_withholding(3000.0, C2026, gastos=0.0, cargas=0)
    with_rebate = PayrollEngine.calculate_ir_withholding(3000.0, C2026, gastos=5000.0, cargas=0)
    assert with_rebate < without

def test_personal_expenses_rebate_scale_by_cargas():
    # Tope confirmado (LRTI): 0→7, 1→9, 2→11, 3→14, 4→17, 5+→20 canastas; tasa 18%.
    canasta = C2026.canasta_basica
    for cargas, n in [(0, 7), (1, 9), (2, 11), (3, 14), (4, 17), (5, 20), (8, 20)]:
        # Gastos enormes para que el tope (N canastas) sea el límite.
        rebate = PayrollEngine.calculate_personal_expenses_rebate(1_000_000.0, cargas, C2026)
        assert rebate == pytest.approx(0.18 * n * canasta)

def test_personal_expenses_rebate_catastrophic_uses_100_canastas():
    rebate = PayrollEngine.calculate_personal_expenses_rebate(
        1_000_000.0, 0, C2026, catastrophic=True)
    assert rebate == pytest.approx(0.18 * 100 * C2026.canasta_basica)

def test_ir_withholding_applied_in_monthly_payroll():
    employee = _employee(salary=3000.0)
    result = PayrollEngine.process_monthly_payroll(employee, [], period="2026-06")
    assert result["income_tax"] > 0
    assert "Impuesto a la Renta" in result["deductions_breakdown"]
    # El líquido descuenta IESS personal + IR.
    expected_net = 3000.0 - result["iess_employee"] - result["income_tax"]
    assert result["net_salary"] == pytest.approx(expected_net)


# --- Décimo cuarto regional + mensualización ------------------------------

def test_fourteenth_payout_month_by_region():
    assert PayrollEngine.fourteenth_payout_month(Region.COSTA) == 3
    assert PayrollEngine.fourteenth_payout_month(Region.INSULAR) == 3
    assert PayrollEngine.fourteenth_payout_month(Region.SIERRA) == 8
    assert PayrollEngine.fourteenth_payout_month(Region.AMAZONIA) == 8

def test_mensualizado_thirteenth_adds_to_net():
    accrued = _employee(salary=1000.0, accumulate_13th=True)
    monthly = _employee(salary=1000.0, accumulate_13th=False)
    r_accrued = PayrollEngine.process_monthly_payroll(accrued, [], period="2026-06")
    r_monthly = PayrollEngine.process_monthly_payroll(monthly, [], period="2026-06")
    assert r_monthly["net_salary"] == pytest.approx(r_accrued["net_salary"] + 1000.0 / 12)


# --- Horas extras calculadas desde horas ----------------------------------

def test_horas_suplementarias_from_hours():
    # Sueldo 1200 → valor hora 5; 10 horas suplementarias x 1.5 = 75.
    employee = _employee(salary=1200.0)
    events = [_event(EventType.HORAS_SUPLEMENTARIAS, 10.0)]
    result = PayrollEngine.process_monthly_payroll(employee, events, period="2026-06")
    assert result["earnings_breakdown"]["Horas Suplementarias (50%)"] == pytest.approx(75.0)
    assert result["taxable_earnings"] == pytest.approx(1275.0)

def test_horas_extraordinarias_from_hours():
    # 10 horas extraordinarias x valor hora 5 x 2.0 = 100.
    employee = _employee(salary=1200.0)
    events = [_event(EventType.HORAS_EXTRAORDINARIAS, 10.0)]
    result = PayrollEngine.process_monthly_payroll(employee, events, period="2026-06")
    assert result["earnings_breakdown"]["Horas Extraordinarias (100%)"] == pytest.approx(100.0)
    assert result["taxable_earnings"] == pytest.approx(1300.0)


# --- Descuentos estructurados ---------------------------------------------

def test_multa_capped_at_ten_percent():
    # Multa de 200 sobre sueldo 1000 → tope 10% = 100.
    employee = _employee(salary=1000.0)
    result = PayrollEngine.process_monthly_payroll(
        employee, [_event(EventType.MULTA, 200.0)], period="2026-06")
    assert result["deductions_breakdown"]["Multa"] == pytest.approx(100.0)

def test_falta_deducts_hours():
    # 8 horas de falta sobre sueldo 1200 (valor hora 5) → 40.
    employee = _employee(salary=1200.0)
    result = PayrollEngine.process_monthly_payroll(
        employee, [_event(EventType.FALTA, 8.0)], period="2026-06")
    assert result["deductions_breakdown"]["Falta / Atraso"] == pytest.approx(40.0)

def test_prestamo_categorized_deduction():
    employee = _employee(salary=1000.0)
    result = PayrollEngine.process_monthly_payroll(
        employee, [_event(EventType.PRESTAMO_QUIROGRAFARIO, 120.0)], period="2026-06")
    assert result["deductions_breakdown"]["Préstamo Quirografario IESS"] == pytest.approx(120.0)


# --- Liquidación de haberes -----------------------------------------------

def test_settlement_year_counting_calendar():
    # 4 años, 9 meses, 3 días → completos 4; con fracción (Art. 188) 5.
    employee = _employee(start_date=datetime(2020, 1, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 10, 4), SettlementCause.RENUNCIA)
    assert result["full_years"] == 4
    assert result["years_with_fraction"] == 5

def test_settlement_despido_includes_indemnity_and_bonus():
    # Reproduce el ejemplo de referencia: remuneración 482, 4a 9m 3d.
    # Art. 188 = 482 × 5 (con fracción) = 2410; Art. 185 = 482 × 25% × 4 (completos) = 482.
    employee = _employee(start_date=datetime(2020, 1, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 10, 4), SettlementCause.DESPIDO_INTEMPESTIVO,
        remuneration=482.0)
    assert result["severance_indemnity"] == pytest.approx(2410.0)
    assert result["desahucio_bonus"] == pytest.approx(482.0)

def test_settlement_despido_scale_under_3_years():
    # ~2.5 años → con fracción 3 → 3 meses de remuneración.
    employee = _employee(salary=1000.0, start_date=datetime(2022, 1, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 7, 1), SettlementCause.DESPIDO_INTEMPESTIVO)
    assert result["severance_indemnity"] == pytest.approx(3000.0)
    # Despido también paga bonificación 25% por años completos (2).
    assert result["desahucio_bonus"] == pytest.approx(0.25 * 1000.0 * 2)

def test_settlement_desahucio_uses_full_years_only():
    # 4a 9m → bonificación 25% SOLO por años completos (4); fracción no cuenta.
    employee = _employee(salary=1000.0, start_date=datetime(2020, 1, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 10, 4), SettlementCause.DESAHUCIO_TRABAJADOR)
    assert result["desahucio_bonus"] == pytest.approx(0.25 * 1000.0 * 4)
    assert result["severance_indemnity"] == 0.0

def test_settlement_vacation_uses_remuneration_over_30():
    # Vacaciones (Art. 78): (remuneración / 30) × días. 15 días pendientes a 482 = 241.
    employee = _employee(start_date=datetime(2020, 7, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 7, 1), SettlementCause.RENUNCIA,
        remuneration=482.0, pending_vacation_days=15.0)
    assert result["vacation_pending"] == pytest.approx(241.0)

def test_settlement_renuncia_has_no_indemnity():
    employee = _employee(salary=1000.0, start_date=datetime(2020, 1, 1))
    result = PayrollEngine.calculate_settlement(
        employee, datetime(2024, 7, 1), SettlementCause.RENUNCIA)
    assert result["severance_indemnity"] == 0.0
    assert result["desahucio_bonus"] == 0.0
    # Pero sí incluye proporcionales (13º, 14º, vacaciones).
    assert result["total"] > 0
