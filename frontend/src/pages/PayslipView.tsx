import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import {
  Container, Typography, Card, CardContent, Box, Button, Divider,
  Table, TableBody, TableCell, TableContainer, TableRow, CircularProgress,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';
import { downloadPdf } from '../lib/pdf';
import { money, labelForKey } from '../lib/payrollLabels';

const PayslipView: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { getToken } = useAuth();

  const stateEmployee = (location.state as any)?.employee;
  const stateCompany = (location.state as any)?.company;
  const [employee, setEmployee] = useState<any>(stateEmployee ?? null);
  const [company, setCompany] = useState<any>(stateCompany ?? null);
  const [loading, setLoading] = useState(!stateEmployee);

  // Si llegamos por recarga / enlace directo (sin state), recuperamos empresa
  // y preview, y ubicamos al empleado por id.
  const load = useCallback(async () => {
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const compRes = await axios.get(`${API_URL}/companies/`, { headers });
      if (compRes.data.length === 0) return;
      const comp = compRes.data[0];
      setCompany(comp);
      const prevRes = await axios.get(`${API_URL}/payroll/preview/${comp.id}`, { headers });
      const emp = prevRes.data.employees?.find((e: any) => e.employee_id === id);
      setEmployee(emp ?? null);
    } catch (error) {
      console.error('Failed to load payslip', error);
    } finally {
      setLoading(false);
    }
  }, [getToken, id]);

  useEffect(() => { if (!stateEmployee) load(); }, [stateEmployee, load]);

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  if (!employee) {
    return (
      <Container sx={{ mt: 4 }}>
        <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
        <Typography>No se encontró el rol de este empleado.</Typography>
      </Container>
    );
  }

  const earnings = employee.earnings_breakdown || {};
  const deductions = employee.deductions_breakdown || {};

  return (
    <Container sx={{ mt: 4, mb: 6 }} maxWidth="sm">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Button onClick={() => navigate(`/employee/${id}`)}>Volver</Button>
        {company && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" color="inherit" sx={{ color: 'text.primary' }}
              onClick={() => downloadPdf(
                getToken,
                `${API_URL}/payroll/payslip/${company.id}/${employee.employee_id}/pdf`,
                `rol_${employee.last_name}_${employee.first_name}.pdf`,
              )}>
              Rol (PDF)
            </Button>
            <Button variant="outlined" color="inherit" sx={{ color: 'text.primary' }}
              onClick={() => downloadPdf(
                getToken,
                `${API_URL}/payroll/form107/${company.id}/${employee.employee_id}/pdf`,
                `form107_${employee.last_name}_${employee.first_name}.pdf`,
              )}>
              Form. 107 (PDF)
            </Button>
          </Box>
        )}
      </Box>
      <Card>
        <CardContent>
          <Typography variant="h4" gutterBottom>{employee.first_name} {employee.last_name}</Typography>
          <Typography color="textSecondary" gutterBottom>Cálculo del mes en curso (en vivo)</Typography>
          <Divider sx={{ my: 2 }} />

          <TableContainer>
            <Table size="small">
              <TableBody>
                {Object.entries(earnings).map(([key, val]: any) => (
                  <TableRow key={key}>
                    <TableCell>{labelForKey(key)}</TableCell>
                    <TableCell align="right">{money(val)}</TableCell>
                  </TableRow>
                ))}
                {Object.entries(deductions).map(([key, val]: any) => (
                  <TableRow key={key}>
                    <TableCell>{labelForKey(key)}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }}>-{money(val)}</TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Líquido a recibir</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>{money(employee.net_salary)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>Provisiones (costo del empleador)</Typography>
          <TableContainer>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Décimo Tercero (13º)</TableCell>
                  <TableCell align="right">{money(employee.thirteenth_salary)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Décimo Cuarto (14º)</TableCell>
                  <TableCell align="right">{money(employee.fourteenth_salary)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Fondos de Reserva</TableCell>
                  <TableCell align="right">{money(employee.reserve_funds)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Provisión de Vacaciones</TableCell>
                  <TableCell align="right">{money(employee.vacation_provision)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Aporte Patronal IESS (12.15%)</TableCell>
                  <TableCell align="right">{money(employee.iess_employer)}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Container>
  );
};

export default PayslipView;
