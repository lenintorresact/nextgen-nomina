import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Card, CardContent, CircularProgress } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';
import EmployeeForm, { emptyEmployee, type EmployeeFormValues } from '../components/EmployeeForm';
import { fetchOrgContext, type OrgContext } from '../lib/orgContext';

// Convierte los valores del formulario al payload que espera el backend
// (region_override vacío -> null, ya que el backend valida un enum Region).
export const toEmployeePayload = (v: EmployeeFormValues) => ({
  ...v,
  region_override: v.region_override || null,
});

const AddEmployee: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [ctx, setCtx] = useState<OrgContext | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchOrgContext(getToken).then(setCtx).catch((e) => {
      console.error('Failed to load org context', e);
      setCtx({ companyId: null, companyRegion: '', sbu: 0, irMinAnnual: Infinity, iessRate: 0.0945 });
    });
  }, [getToken]);

  const handleSubmit = async (values: EmployeeFormValues) => {
    setSaving(true);
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const company_id = ctx?.companyId
        ?? (await axios.get(`${API_URL}/companies/`, { headers })).data[0]?.id;
      if (company_id) {
        await axios.post(`${API_URL}/employees/`, { ...toEmployeePayload(values), company_id }, { headers });
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Failed to add employee', error);
      setSaving(false);
    }
  };

  if (!ctx) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  const initial = { ...emptyEmployee(), salary: ctx.sbu || 0, region_override: ctx.companyRegion };

  return (
    <Container maxWidth="sm" sx={{ mt: 4, mb: 6 }}>
      <Typography variant="h4" gutterBottom>Nuevo Empleado</Typography>
      <Card>
        <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <EmployeeForm
            initial={initial}
            submitLabel="Guardar Empleado"
            saving={saving}
            companyRegion={ctx.companyRegion}
            irMinAnnual={ctx.irMinAnnual}
            iessRate={ctx.iessRate}
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>
    </Container>
  );
};

export default AddEmployee;
