import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const AddEmployee: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState({
    cedula: '',
    first_name: '',
    last_name: '',
    email: '',
    salary: 460,
    start_date: new Date().toISOString().split('T')[0],
    contract_type: 'Indefinido',
    company_id: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const token = await getToken();

        // Fetch company_id first
        const compRes = await axios.get(`${API_URL}/companies/`, {
            headers: { Authorization: `Bearer ${token}` }
        });

        if (compRes.data.length > 0) {
            const company_id = compRes.data[0].id;
            await axios.post(`${API_URL}/employees/`, { ...employee, company_id }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            navigate('/dashboard');
        }
    } catch (error) {
        console.error("Failed to add employee", error);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>Nuevo Empleado</Typography>

        <form onSubmit={handleSubmit}>
          <TextField fullWidth label="Cédula" margin="normal" value={employee.cedula} onChange={e => setEmployee({...employee, cedula: e.target.value})} required />
          <TextField fullWidth label="Nombre" margin="normal" value={employee.first_name} onChange={e => setEmployee({...employee, first_name: e.target.value})} required />
          <TextField fullWidth label="Apellido" margin="normal" value={employee.last_name} onChange={e => setEmployee({...employee, last_name: e.target.value})} required />
          <TextField fullWidth label="Email" margin="normal" value={employee.email} onChange={e => setEmployee({...employee, email: e.target.value})} required />
          <TextField fullWidth label="Salario" margin="normal" type="number" value={employee.salary} onChange={e => setEmployee({...employee, salary: parseFloat(e.target.value)})} required />
          <TextField fullWidth label="Fecha de Inicio" margin="normal" type="date" value={employee.start_date} onChange={e => setEmployee({...employee, start_date: e.target.value})} required />

          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3 }}>
            Guardar Empleado
          </Button>
        </form>
      </Box>
    </Container>
  );
};

export default AddEmployee;
