import React, { useEffect, useState } from 'react';
import { Container, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableRow, Divider, Box, CircularProgress } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';

const EmployeeDashboard: React.FC = () => {
  const { getToken, user } = useAuth();
  const [slips, setSlips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlips = async () => {
        if (!user) {
            setLoading(false);
            return;
        }
        try {
            const token = await getToken();
            const headers = { Authorization: `Bearer ${token}` };
            const response = await axios.get(`${API_URL}/employee-portal/my-slips`, { headers });
            setSlips(response.data);
        } catch (error) {
            console.error("Failed to fetch slips", error);
        } finally {
            setLoading(false);
        }
    };
    fetchSlips();
  }, [getToken, user]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Mis Roles de Pago</Typography>

      {slips.length === 0 ? (
        <Typography color="textSecondary">No tienes roles de pago generados aún para tu correo: {user?.email}</Typography>
      ) : (
        slips.map((slip) => (
          <Paper key={slip.id} elevation={2} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6">Rol de Pago - {slip.period}</Typography>
                <Typography variant="h6" color="primary">${slip.net_salary.toFixed(2)}</Typography>
            </Box>
            <Divider sx={{ my: 2 }} />
            <TableContainer>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Sueldo Base</TableCell>
                    <TableCell align="right">${slip.base_salary.toFixed(2)}</TableCell>
                  </TableRow>
                  {Object.entries(slip.earnings).map(([key, val]: any) => (
                    <TableRow key={key}>
                      <TableCell>{key}</TableCell>
                      <TableCell align="right">${val.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>IESS Personal (9.45%)</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>-${slip.iess_employee.toFixed(2)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Líquido a Recibir</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>${slip.net_salary.toFixed(2)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        ))
      )}
    </Container>
  );
};

export default EmployeeDashboard;
