import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, MenuItem, Autocomplete } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const LogEvent: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [event, setEvent] = useState({
    type: 'Overtime 50%',
    amount: 0,
    description: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    const fetchEmployees = async () => {
        try {
            const token = await getToken();
            const headers = { Authorization: `Bearer ${token}` };
            const compRes = await axios.get(`${API_URL}/companies/`, { headers });
            if (compRes.data.length > 0) {
                const empRes = await axios.get(`${API_URL}/employees/company/${compRes.data[0].id}`, { headers });
                setEmployees(empRes.data);
            }
        } catch (error) {
            console.error("Failed to fetch employees", error);
        }
    };
    fetchEmployees();
  }, [getToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;

    try {
        const token = await getToken();
        await axios.post(`${API_URL}/payroll/events`, {
            ...event,
            employee_id: selectedEmployee.id,
            company_id: selectedEmployee.company_id
        }, {
            headers: { Authorization: `Bearer ${token}` }
        });
        navigate('/dashboard');
    } catch (error) {
        console.error("Failed to log event", error);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>Registrar Novedad</Typography>
        <form onSubmit={handleSubmit}>
          <Autocomplete
            options={employees}
            getOptionLabel={(option) => `${option.first_name} ${option.last_name}`}
            onChange={(_, val) => setSelectedEmployee(val)}
            renderInput={(params) => <TextField {...params} label="Empleado" margin="normal" required />}
          />

          <TextField
            fullWidth
            select
            label="Tipo de Novedad"
            margin="normal"
            value={event.type}
            onChange={(e) => setEvent({ ...event, type: e.target.value })}
          >
            <MenuItem value="Horas Suplementarias (50%)">Horas Suplementarias (50%)</MenuItem>
            <MenuItem value="Horas Extraordinarias (100%)">Horas Extraordinarias (100%)</MenuItem>
            <MenuItem value="Overtime 50%">Horas Extras 50% (monto)</MenuItem>
            <MenuItem value="Overtime 100%">Horas Extras 100% (monto)</MenuItem>
            <MenuItem value="Commission">Comisión</MenuItem>
            <MenuItem value="Bonus">Bono</MenuItem>
            <MenuItem value="Préstamo Quirografario IESS">Préstamo Quirografario IESS</MenuItem>
            <MenuItem value="Préstamo Hipotecario (Biess)">Préstamo Hipotecario (Biess)</MenuItem>
            <MenuItem value="Anticipo de Sueldo">Anticipo de Sueldo</MenuItem>
            <MenuItem value="Multa">Multa (tope 10%)</MenuItem>
            <MenuItem value="Falta / Atraso">Falta / Atraso</MenuItem>
            <MenuItem value="Deduction">Otro Descuento</MenuItem>
          </TextField>

          {(() => {
            const hourBased = ['Horas Suplementarias (50%)', 'Horas Extraordinarias (100%)', 'Falta / Atraso'];
            const isHours = hourBased.includes(event.type);
            return (
              <TextField
                fullWidth
                label={isHours ? 'Nº de Horas' : 'Monto ($)'}
                type="number"
                margin="normal"
                value={event.amount}
                onChange={(e) => setEvent({ ...event, amount: parseFloat(e.target.value) })}
                required
              />
            );
          })()}

          <TextField
            fullWidth
            label="Descripción"
            margin="normal"
            value={event.description}
            onChange={(e) => setEvent({ ...event, description: e.target.value })}
            required
          />

          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3 }}>
            Guardar Novedad
          </Button>
        </form>
      </Box>
    </Container>
  );
};

export default LogEvent;
