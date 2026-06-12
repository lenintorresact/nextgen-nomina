import React, { useState } from 'react';
import { Container, Typography, Box } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';
import EmployeeForm, { emptyEmployee, type EmployeeFormValues } from '../components/EmployeeForm';

// Convierte los valores del formulario al payload que espera el backend
// (region_override vacío -> null, ya que el backend valida un enum Region).
export const toEmployeePayload = (v: EmployeeFormValues) => ({
  ...v,
  region_override: v.region_override || null,
});

const AddEmployee: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (values: EmployeeFormValues) => {
    setSaving(true);
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const compRes = await axios.get(`${API_URL}/companies/`, { headers });
      if (compRes.data.length > 0) {
        const company_id = compRes.data[0].id;
        await axios.post(`${API_URL}/employees/`, { ...toEmployeePayload(values), company_id }, { headers });
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Failed to add employee', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4, mb: 6 }}>
        <Typography variant="h5" gutterBottom>Nuevo Empleado</Typography>
        <EmployeeForm initial={emptyEmployee()} submitLabel="Guardar Empleado" saving={saving} onSubmit={handleSubmit} />
      </Box>
    </Container>
  );
};

export default AddEmployee;
