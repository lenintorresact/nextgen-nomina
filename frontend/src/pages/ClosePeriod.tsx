import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, CircularProgress } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const ClosePeriod: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [loading, setLoading] = useState(false);

  const handleClose = async () => {
    setLoading(true);
    try {
        const token = await getToken();
        const headers = { Authorization: `Bearer ${token}` };
        const compRes = await axios.get(`${API_URL}/companies/`, { headers });
        if (compRes.data.length > 0) {
            await axios.post(`${API_URL}/payroll/close-period/${compRes.data[0].id}/${period}`, {}, { headers });
            navigate('/dashboard');
        }
    } catch (error) {
        console.error("Failed to close period", error);
    } finally {
        setLoading(false);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>Cerrar Período de Nómina</Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Al cerrar el período, se generarán los roles de pago para todos los empleados activos.
        </Typography>

        <TextField
          fullWidth
          label="Período (YYYY-MM)"
          type="month"
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          sx={{ mb: 3 }}
        />

        <Button
            fullWidth
            variant="contained"
            color="warning"
            onClick={handleClose}
            disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Generar Roles de Pago'}
        </Button>
      </Box>
    </Container>
  );
};

export default ClosePeriod;
