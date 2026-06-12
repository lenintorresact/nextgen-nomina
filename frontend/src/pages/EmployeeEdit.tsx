import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Container, Typography, Box, Button, Card, CardContent, CircularProgress,
  Snackbar, Alert,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';
import EmployeeForm, { emptyEmployee, type EmployeeFormValues } from '../components/EmployeeForm';
import { toEmployeePayload } from './AddEmployee';

// El backend devuelve start_date como ISO datetime; el input date necesita YYYY-MM-DD.
const toFormValues = (data: any): EmployeeFormValues => ({
  ...emptyEmployee(),
  cedula: data.cedula ?? '',
  first_name: data.first_name ?? '',
  last_name: data.last_name ?? '',
  email: data.email ?? '',
  phone: data.phone ?? '',
  salary: data.salary ?? 0,
  start_date: (data.start_date ?? '').split('T')[0] || new Date().toISOString().split('T')[0],
  contract_type: data.contract_type ?? 'Indefinido',
  region_override: data.region_override ?? '',
  accumulate_13th: data.accumulate_13th ?? true,
  accumulate_14th: data.accumulate_14th ?? true,
  accumulate_reserve_funds: data.accumulate_reserve_funds ?? true,
  projected_personal_expenses: data.projected_personal_expenses ?? 0,
  family_burdens: data.family_burdens ?? 0,
  catastrophic_illness_burden: data.catastrophic_illness_burden ?? false,
});

const EmployeeEdit: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [initial, setInitial] = useState<EmployeeFormValues | null>(null);
  const [companyId, setCompanyId] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(false);

  const load = useCallback(async () => {
    try {
      const token = await getToken();
      const res = await axios.get(`${API_URL}/employees/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setInitial(toFormValues(res.data));
      setCompanyId(res.data.company_id);
      setName(`${res.data.first_name} ${res.data.last_name}`);
    } catch (error) {
      console.error('Failed to load employee', error);
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [getToken, id]);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async (values: EmployeeFormValues) => {
    setSaving(true);
    try {
      const token = await getToken();
      await axios.put(`${API_URL}/employees/${id}`, { ...toEmployeePayload(values), company_id: companyId }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setName(`${values.first_name} ${values.last_name}`);
      setToast(true);
    } catch (error) {
      console.error('Failed to update employee', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  if (notFound || !initial) {
    return (
      <Container sx={{ mt: 4 }}>
        <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
        <Typography>No se encontró el empleado.</Typography>
      </Container>
    );
  }

  return (
    <Container sx={{ mt: 4, mb: 6 }} maxWidth="sm">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Button onClick={() => navigate('/dashboard')}>Volver</Button>
        <Button variant="outlined" color="inherit" sx={{ color: 'text.primary' }}
          onClick={() => navigate(`/employee/${id}/rol`)}>
          Ver rol del mes
        </Button>
      </Box>
      <Card>
        <CardContent>
          <Typography variant="h4" gutterBottom>{name}</Typography>
          <Typography color="textSecondary" gutterBottom>Datos del empleado</Typography>
          <EmployeeForm initial={initial} submitLabel="Guardar cambios" saving={saving} onSubmit={handleSubmit} />
        </CardContent>
      </Card>

      <Snackbar open={toast} autoHideDuration={3000} onClose={() => setToast(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setToast(false)} severity="success" variant="filled" sx={{ width: '100%' }}>
          Cambios guardados
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default EmployeeEdit;
