import React, { useState, useEffect } from 'react';
import {
  Container, Typography, TextField, Button, Box, MenuItem, Autocomplete,
  Card, CardContent, Table, TableBody, TableCell, TableContainer, TableRow, Divider
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const money = (n: number) => `$${(n ?? 0).toFixed(2)}`;

const CAUSES = [
  'Despido Intempestivo',
  'Desahucio por el Empleador',
  'Desahucio por el Trabajador',
  'Renuncia Voluntaria',
];

const Settlement: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<any[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);
  const [form, setForm] = useState({
    termination_date: new Date().toISOString().split('T')[0],
    cause: 'Despido Intempestivo',
    remuneration: 0,
    pending_vacation_days: 0,
    pending_reserve_funds: 0,
    unpaid_amounts: 0,
  });
  const [result, setResult] = useState<any>(null);

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
        console.error('Failed to fetch employees', error);
      }
    };
    fetchEmployees();
  }, [getToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    try {
      const token = await getToken();
      // Omite `remuneration` si es 0 para que el backend use el sueldo del empleado.
      const { remuneration, ...rest } = form;
      const params: Record<string, unknown> = { ...rest };
      if (remuneration > 0) params.remuneration = remuneration;
      const res = await axios.get(`${API_URL}/payroll/settlement/${selectedEmployee.id}`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });
      setResult(res.data);
    } catch (error) {
      console.error('Failed to compute settlement', error);
    }
  };

  const rows: [string, number][] = result ? [
    ['Décimo Tercero proporcional', result.thirteenth_proportional],
    ['Décimo Cuarto proporcional', result.fourteenth_proportional],
    ['Vacaciones no gozadas', result.vacation_pending],
    ['Fondos de Reserva pendientes', result.reserve_funds_pending],
    ['Indemnización (Art. 188)', result.severance_indemnity],
    ['Bonificación por desahucio (Art. 185)', result.desahucio_bonus],
    ['Valores pendientes', result.unpaid_amounts],
  ] : [];

  return (
    <Container maxWidth="sm" sx={{ mt: 4, mb: 6 }}>
      <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
      <Typography variant="h5" gutterBottom>Liquidación de Haberes</Typography>

      <form onSubmit={handleSubmit}>
        <Autocomplete
          options={employees}
          getOptionLabel={(o) => `${o.first_name} ${o.last_name}`}
          onChange={(_, val) => setSelectedEmployee(val)}
          renderInput={(params) => <TextField {...params} label="Empleado" margin="normal" required />}
        />
        <TextField fullWidth label="Fecha de Salida" type="date" margin="normal"
          value={form.termination_date}
          onChange={(e) => setForm({ ...form, termination_date: e.target.value })} required />
        <TextField fullWidth select label="Causa de Salida" margin="normal"
          value={form.cause} onChange={(e) => setForm({ ...form, cause: e.target.value })}>
          {CAUSES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
        </TextField>
        <TextField fullWidth label="Remuneración mensual ($)" type="number" margin="normal"
          helperText="Sueldo + beneficios permanentes. Déjalo en 0 para usar el sueldo del empleado."
          value={form.remuneration}
          onChange={(e) => setForm({ ...form, remuneration: parseFloat(e.target.value) || 0 })} />
        <TextField fullWidth label="Días de vacaciones no gozadas (años previos)" type="number" margin="normal"
          value={form.pending_vacation_days}
          onChange={(e) => setForm({ ...form, pending_vacation_days: parseFloat(e.target.value) || 0 })} />
        <TextField fullWidth label="Fondos de reserva pendientes ($)" type="number" margin="normal"
          value={form.pending_reserve_funds}
          onChange={(e) => setForm({ ...form, pending_reserve_funds: parseFloat(e.target.value) || 0 })} />
        <TextField fullWidth label="Otros valores pendientes ($)" type="number" margin="normal"
          value={form.unpaid_amounts}
          onChange={(e) => setForm({ ...form, unpaid_amounts: parseFloat(e.target.value) || 0 })} />
        <Button type="submit" fullWidth variant="contained" sx={{ mt: 2 }}>Calcular Liquidación</Button>
      </form>

      {result && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              {result.cause} · {result.years_of_service} años de servicio
            </Typography>
            <Divider sx={{ my: 1.5 }} />
            <TableContainer>
              <Table size="small">
                <TableBody>
                  {rows.map(([label, val]) => (
                    <TableRow key={label}>
                      <TableCell>{label}</TableCell>
                      <TableCell align="right">{money(val)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Total a recibir</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>{money(result.total)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Container>
  );
};

export default Settlement;
