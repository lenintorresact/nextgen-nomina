import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Container, Typography, Card, CardContent, Box, Button, Divider,
  Table, TableBody, TableCell, TableContainer, TableRow
} from '@mui/material';

const money = (n: number) => `$${(n ?? 0).toFixed(2)}`;

const EmployeeDetail: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const employee = (location.state as any)?.employee;

  if (!employee) {
    return (
      <Container sx={{ mt: 4 }}>
        <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
        <Typography>Abre un empleado desde el tablero para ver su detalle.</Typography>
      </Container>
    );
  }

  const earnings = employee.earnings_breakdown || {};
  const deductions = employee.deductions_breakdown || {};

  return (
    <Container sx={{ mt: 4, mb: 6 }} maxWidth="sm">
      <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
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
                    <TableCell>{key}</TableCell>
                    <TableCell align="right">{money(val)}</TableCell>
                  </TableRow>
                ))}
                {Object.entries(deductions).map(([key, val]: any) => (
                  <TableRow key={key}>
                    <TableCell>{key}</TableCell>
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

export default EmployeeDetail;
