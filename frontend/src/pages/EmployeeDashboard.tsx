import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableRow, Divider, Box, CircularProgress,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';
import { money, labelForKey } from '../lib/payrollLabels';

const EmployeeDashboard: React.FC = () => {
  const { getToken, user } = useAuth();
  const [slips, setSlips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSlips = async () => {
      if (!user) { setLoading(false); return; }
      try {
        const token = await getToken();
        const headers = { Authorization: `Bearer ${token}` };
        const response = await axios.get(`${API_URL}/employee-portal/my-slips`, { headers });
        setSlips(response.data);
      } catch (error) {
        console.error('Failed to fetch slips', error);
      } finally {
        setLoading(false);
      }
    };
    fetchSlips();
  }, [getToken, user]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Container sx={{ mt: 4, mb: 6 }} maxWidth="sm">
      <Typography variant="h4" gutterBottom>Mis Roles de Pago</Typography>

      {slips.length === 0 ? (
        <Typography color="textSecondary">
          {user?.email
            ? `No tienes roles de pago generados aún para ${user.email}.`
            : 'No tienes roles de pago generados aún.'}
        </Typography>
      ) : (
        slips.map((slip) => (
          <Card key={slip.id} sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <Typography variant="h6">Rol de Pago · {slip.period}</Typography>
                <Typography variant="h6" color="primary">{money(slip.net_salary)}</Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    {Object.entries(slip.earnings || {}).map(([key, val]: any) => (
                      <TableRow key={`e-${key}`}>
                        <TableCell>{labelForKey(key)}</TableCell>
                        <TableCell align="right">{money(val)}</TableCell>
                      </TableRow>
                    ))}
                    {Object.entries(slip.deductions || {}).map(([key, val]: any) => (
                      <TableRow key={`d-${key}`}>
                        <TableCell>{labelForKey(key)}</TableCell>
                        <TableCell align="right" sx={{ color: 'error.main' }}>-{money(val)}</TableCell>
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Líquido a Recibir</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 'bold' }}>{money(slip.net_salary)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        ))
      )}
    </Container>
  );
};

export default EmployeeDashboard;
