import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, MenuItem } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const Onboarding: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [company, setCompany] = useState({
    ruc: '',
    name: '',
    region: 'Sierra'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = await getToken();
      await axios.post(`${API_URL}/companies/`, company, {
        headers: { Authorization: `Bearer ${token}` }
      });
      navigate('/dashboard');
    } catch (error) {
      console.error("Failed to create company", error);
    }
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>Registra tu Empresa</Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="RUC"
            margin="normal"
            value={company.ruc}
            onChange={(e) => setCompany({ ...company, ruc: e.target.value })}
            required
          />
          <TextField
            fullWidth
            label="Nombre de la Empresa"
            margin="normal"
            value={company.name}
            onChange={(e) => setCompany({ ...company, name: e.target.value })}
            required
          />
          <TextField
            fullWidth
            select
            label="Región"
            margin="normal"
            value={company.region}
            onChange={(e) => setCompany({ ...company, region: e.target.value })}
          >
            <MenuItem value="Sierra">Sierra</MenuItem>
            <MenuItem value="Costa">Costa</MenuItem>
            <MenuItem value="Amazonia">Amazonía</MenuItem>
            <MenuItem value="Insular">Galápagos</MenuItem>
          </TextField>
          <Button type="submit" fullWidth variant="contained" sx={{ mt: 3 }}>
            Continuar
          </Button>
        </form>
      </Box>
    </Container>
  );
};

export default Onboarding;
