import axios from 'axios';
import API_URL from '../api_config';

// Contexto de la empresa + constantes legales del año, usados por los formularios
// de empleado (región por defecto, sueldo por defecto = SBU, y umbral para mostrar
// la sección de Impuesto a la Renta solo cuando el sueldo llega a ser gravable).
export interface OrgContext {
  companyId: string | null;
  companyRegion: string;
  sbu: number;
  irMinAnnual: number;
  iessRate: number;
}

export const fetchOrgContext = async (
  getToken: () => Promise<string | null>,
): Promise<OrgContext> => {
  const token = await getToken();
  const headers = { Authorization: `Bearer ${token}` };
  const [compRes, constRes] = await Promise.all([
    axios.get(`${API_URL}/companies/`, { headers }),
    axios.get(`${API_URL}/payroll/legal-constants`, { headers }),
  ]);
  const company = compRes.data[0];
  return {
    companyId: company?.id ?? null,
    companyRegion: company?.region ?? '',
    sbu: constRes.data.sbu ?? 0,
    irMinAnnual: constRes.data.ir_min_taxable_annual ?? Infinity,
    iessRate: constRes.data.iess_employee ?? 0.0945,
  };
};
