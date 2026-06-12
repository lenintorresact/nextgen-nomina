import { EVENT_TYPES } from './payrollEvents';

// Formato de moneda local (es-EC): $1.234,56.
export const money = (n: number) =>
  `$${(n ?? 0).toLocaleString('es-EC', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

// Etiqueta en español para las claves crudas del desglose (earnings/deductions).
// El backend usa claves como "base_salary" o el string del tipo de novedad.
const STATIC_LABELS: Record<string, string> = { base_salary: 'Sueldo base' };
export const labelForKey = (key: string): string =>
  STATIC_LABELS[key] ?? EVENT_TYPES.find((t) => t.value === key)?.label ?? key;
