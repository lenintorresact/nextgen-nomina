import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, IconButton } from '@mui/material';
import PhotoCamera from '@mui/icons-material/PhotoCamera';
import axios from 'axios';

const AddEmployee: React.FC = () => {
  const [employee, setEmployee] = useState({
    cedula: '',
    first_name: '',
    last_name: '',
    email: '',
    salary: 460,
    start_date: new Date().toISOString().split('T')[0]
  });

  const handleScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const formData = new FormData();
      formData.append('file', e.target.files[0]);

      try {
        const token = await (window as any).firebaseUser?.getIdToken();
        const response = await axios.post('http://localhost:8000/ai/extract-employee', formData, {
            headers: { Authorization: `Bearer ${token}` }
        });

        const extracted = JSON.parse(response.data.extracted_data);
        setEmployee(prev => ({ ...prev, ...extracted }));
      } catch (error) {
        console.error("AI Scan failed", error);
      }
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>Nuevo Empleado</Typography>

        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography>Escanear desde Cédula/PDF:</Typography>
            <IconButton color="primary" component="label">
                <input hidden accept="image/*,application/pdf" type="file" onChange={handleScan} />
                <PhotoCamera />
            </IconButton>
        </Box>

        <form>
          <TextField fullWidth label="Cédula" margin="normal" value={employee.cedula} required />
          <TextField fullWidth label="Nombre" margin="normal" value={employee.first_name} required />
          <TextField fullWidth label="Apellido" margin="normal" value={employee.last_name} required />
          <TextField fullWidth label="Email" margin="normal" value={employee.email} required />
          <TextField fullWidth label="Salario" margin="normal" type="number" value={employee.salary} required />
          <TextField fullWidth label="Fecha de Inicio" margin="normal" type="date" value={employee.start_date} required />

          <Button fullWidth variant="contained" sx={{ mt: 3 }}>
            Guardar Empleado
          </Button>
        </form>
      </Box>
    </Container>
  );
};

export default AddEmployee;
