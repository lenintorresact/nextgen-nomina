import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, MenuItem, Autocomplete } from '@mui/material';
import axios from 'axios';

const LogEvent: React.FC = () => {
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [event, setEvent] = useState({
    type: 'Overtime 50%',
    amount: 0,
    description: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    // Fetch employees for the dropdown
    // (In a real app, you'd get the company ID from context/state)
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Implementation for posting event to /payroll/events
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
            renderInput={(params) => <TextField {...params} label="Empleado" margin="normal" />}
          />

          <TextField
            fullWidth
            select
            label="Tipo de Novedad"
            margin="normal"
            value={event.type}
            onChange={(e) => setEvent({ ...event, type: e.target.value })}
          >
            <MenuItem value="Overtime 50%">Horas Extras 50%</MenuItem>
            <MenuItem value="Overtime 100%">Horas Extras 100%</MenuItem>
            <MenuItem value="Commission">Comisión</MenuItem>
            <MenuItem value="Bonus">Bono</MenuItem>
            <MenuItem value="Deduction">Descuento</MenuItem>
          </TextField>

          <TextField
            fullWidth
            label="Monto ($)"
            type="number"
            margin="normal"
            value={event.amount}
            onChange={(e) => setEvent({ ...event, amount: parseFloat(e.target.value) })}
          />

          <TextField
            fullWidth
            label="Descripción"
            margin="normal"
            value={event.description}
            onChange={(e) => setEvent({ ...event, description: e.target.value })}
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
