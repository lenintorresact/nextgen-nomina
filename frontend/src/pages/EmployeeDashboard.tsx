import React, { useEffect, useState } from 'react';
import { Container, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableRow, Divider, Box } from '@mui/material';
import axios from 'axios';

const EmployeeDashboard: React.FC = () => {
  const [slips, setSlips] = useState<any[]>([]);

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Mis Roles de Pago</Typography>

      {slips.length === 0 ? (
        <Typography color="textSecondary">No tienes roles de pago generados aún.</Typography>
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
