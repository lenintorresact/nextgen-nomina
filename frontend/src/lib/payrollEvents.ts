// Fuente única de los tipos de novedad de nómina.
// Los `value` deben coincidir EXACTAMENTE con el enum EventType del backend
// (backend/app/models/schemas.py y backend/app/services/payroll_engine.py).
// Lo consumen LogEvent.tsx (pantalla completa) y QuickEventDialog.tsx (alta rápida).

export type EventBucket = 'ingreso' | 'descuento';

export interface EventTypeDef {
  value: string; // string exacto del enum del backend (sensible a mayúsculas)
  label: string; // etiqueta en español para la UI
  bucket: EventBucket;
  hourBased?: boolean; // el monto se ingresa como Nº de horas, no en $
}

export const EVENT_TYPES: EventTypeDef[] = [
  // Ingresos
  { value: 'Horas Suplementarias (50%)', label: 'Horas Suplementarias (50%)', bucket: 'ingreso', hourBased: true },
  { value: 'Horas Extraordinarias (100%)', label: 'Horas Extraordinarias (100%)', bucket: 'ingreso', hourBased: true },
  { value: 'Overtime 50%', label: 'Horas Extras 50% (monto)', bucket: 'ingreso' },
  { value: 'Overtime 100%', label: 'Horas Extras 100% (monto)', bucket: 'ingreso' },
  { value: 'Commission', label: 'Comisión', bucket: 'ingreso' },
  { value: 'Bonus', label: 'Bono', bucket: 'ingreso' },
  // Descuentos
  { value: 'Préstamo Quirografario IESS', label: 'Préstamo Quirografario IESS', bucket: 'descuento' },
  { value: 'Préstamo Hipotecario (Biess)', label: 'Préstamo Hipotecario (Biess)', bucket: 'descuento' },
  { value: 'Anticipo de Sueldo', label: 'Anticipo de Sueldo', bucket: 'descuento' },
  { value: 'Multa', label: 'Multa (tope 10%)', bucket: 'descuento' },
  { value: 'Falta / Atraso', label: 'Falta / Atraso', bucket: 'descuento', hourBased: true },
  { value: 'Deduction', label: 'Otro Descuento', bucket: 'descuento' },
];

export const typesForBucket = (b: EventBucket): EventTypeDef[] =>
  EVENT_TYPES.filter((t) => t.bucket === b);

export const isHourBased = (value: string): boolean =>
  EVENT_TYPES.find((t) => t.value === value)?.hourBased ?? false;
