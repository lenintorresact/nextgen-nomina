import React, { useCallback, useEffect, useState } from 'react';
import {
  Container, Typography, TextField, Button, Box, MenuItem, Autocomplete,
  Card, CardContent, Table, TableBody, TableCell, TableContainer, TableRow, Divider,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, CircularProgress,
  Snackbar, Alert,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import API_URL from '../api_config';

const money = (n: number) => `$${(n ?? 0).toFixed(2)}`;
const yearsLabel = (n: number) => `${n} ${n === 1 ? 'año' : 'años'} de servicio`;

const CAUSES = [
  'Despido Intempestivo',
  'Desahucio por el Empleador',
  'Desahucio por el Trabajador',
  'Renuncia Voluntaria',
];

const settlementRows = (r: any): [string, number][] => r ? [
  ['Décimo Tercero proporcional', r.thirteenth_proportional],
  ['Décimo Cuarto proporcional', r.fourteenth_proportional],
  ['Vacaciones no gozadas', r.vacation_pending],
  ['Fondos de Reserva pendientes', r.reserve_funds_pending],
  ['Indemnización (Art. 188)', r.severance_indemnity],
  ['Bonificación por desahucio (Art. 185)', r.desahucio_bonus],
  ['Valores pendientes', r.unpaid_amounts],
] : [];

const SettlementTable: React.FC<{ data: any }> = ({ data }) => (
  <Card sx={{ mt: 3 }}>
    <CardContent>
      <Typography color="textSecondary" gutterBottom>
        {data.cause} · {yearsLabel(data.years_of_service)}
      </Typography>
      <Divider sx={{ my: 1.5 }} />
      <TableContainer>
        <Table size="small">
          <TableBody>
            {settlementRows(data).map(([label, val]) => (
              <TableRow key={label}>
                <TableCell>{label}</TableCell>
                <TableCell align="right">{money(val)}</TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>Total a recibir</TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>{money(data.total)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </CardContent>
  </Card>
);

const Settlement: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const reviewEmployeeId: string | undefined = (location.state as any)?.reviewEmployeeId;

  // --- Modo revisión: finiquito ya registrado de un empleado dado de baja ---
  const [reviewName, setReviewName] = useState('');
  const [reviewData, setReviewData] = useState<any>(null);
  const [reviewLoading, setReviewLoading] = useState(!!reviewEmployeeId);
  const [reactivating, setReactivating] = useState(false);

  useEffect(() => {
    if (!reviewEmployeeId) return;
    (async () => {
      try {
        const token = await getToken();
        const headers = { Authorization: `Bearer ${token}` };
        const [emp, rec] = await Promise.all([
          axios.get(`${API_URL}/employees/${reviewEmployeeId}`, { headers }),
          axios.get(`${API_URL}/payroll/settlement-record/${reviewEmployeeId}`, { headers }),
        ]);
        setReviewName(`${emp.data.first_name} ${emp.data.last_name}`);
        setReviewData(rec.data);
      } catch (error) {
        console.error('Failed to load settlement record', error);
      } finally {
        setReviewLoading(false);
      }
    })();
  }, [reviewEmployeeId, getToken]);

  const reactivate = async () => {
    setReactivating(true);
    try {
      const token = await getToken();
      await axios.post(`${API_URL}/payroll/reactivate/${reviewEmployeeId}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to reactivate', error);
      setReactivating(false);
    }
  };

  // --- Modo calculadora ---
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
  const [confirmBaja, setConfirmBaja] = useState(false);
  const [terminating, setTerminating] = useState(false);
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (reviewEmployeeId) return;
    (async () => {
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
    })();
  }, [getToken, reviewEmployeeId]);

  // Cualquier cambio en los datos invalida el resultado ya calculado.
  const setField = (patch: Partial<typeof form>) => { setForm((p) => ({ ...p, ...patch })); setResult(null); };
  const pickEmployee = (val: any) => { setSelectedEmployee(val); setResult(null); };

  const params = useCallback(() => {
    const { remuneration, ...rest } = form;
    const p: Record<string, unknown> = { ...rest };
    if (remuneration > 0) p.remuneration = remuneration;
    return p;
  }, [form]);

  const handleCalc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployee) return;
    try {
      const token = await getToken();
      const res = await axios.get(`${API_URL}/payroll/settlement/${selectedEmployee.id}`, {
        headers: { Authorization: `Bearer ${token}` }, params: params(),
      });
      setResult(res.data);
    } catch (error) {
      console.error('Failed to compute settlement', error);
    }
  };

  const terminate = async () => {
    if (!selectedEmployee) return;
    setTerminating(true);
    try {
      const token = await getToken();
      await axios.post(`${API_URL}/payroll/terminate/${selectedEmployee.id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }, params: params(),
      });
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Failed to terminate', error);
      setToast(error?.response?.data?.detail ?? 'No se pudo registrar la baja.');
      setTerminating(false);
      setConfirmBaja(false);
    }
  };

  // ----- Render: modo revisión -----
  if (reviewEmployeeId) {
    if (reviewLoading) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
    }
    return (
      <Container maxWidth="sm" sx={{ mt: 4, mb: 6 }}>
        <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
        <Typography variant="h5" gutterBottom>Finiquito — {reviewName}</Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
          Empleado dado de baja en el período abierto. Puedes reactivarlo mientras no cierres el período.
        </Typography>
        {reviewData && <SettlementTable data={reviewData} />}
        <Box sx={{ position: 'relative', mt: 3 }}>
          <Button fullWidth variant="outlined" color="secondary" onClick={reactivate} disabled={reactivating}>
            Reactivar empleado
          </Button>
          {reactivating && <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', mt: '-12px', ml: '-12px' }} />}
        </Box>
      </Container>
    );
  }

  // ----- Render: modo calculadora -----
  return (
    <Container maxWidth="sm" sx={{ mt: 4, mb: 6 }}>
      <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
      <Typography variant="h4" gutterBottom>Liquidación de Haberes</Typography>

      <Card>
        <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Box component="form" onSubmit={handleCalc}>
            <Autocomplete
              options={employees}
              getOptionLabel={(o) => `${o.first_name} ${o.last_name}`}
              onChange={(_, val) => pickEmployee(val)}
              renderInput={(p) => <TextField {...p} label="Empleado" margin="normal" required />}
            />
            <TextField fullWidth label="Fecha de Salida" type="date" margin="normal"
              InputLabelProps={{ shrink: true }}
              value={form.termination_date}
              onChange={(e) => setField({ termination_date: e.target.value })} required />
            <TextField fullWidth select label="Causa de Salida" margin="normal"
              value={form.cause} onChange={(e) => setField({ cause: e.target.value })}>
              {CAUSES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
            </TextField>
            <TextField fullWidth label="Remuneración mensual ($)" type="number" margin="normal"
              helperText="Sueldo + beneficios permanentes. Déjalo en 0 para usar el sueldo del empleado."
              value={form.remuneration}
              onChange={(e) => setField({ remuneration: parseFloat(e.target.value) || 0 })} />
            <TextField fullWidth label="Días de vacaciones no gozadas (años previos)" type="number" margin="normal"
              value={form.pending_vacation_days}
              onChange={(e) => setField({ pending_vacation_days: parseFloat(e.target.value) || 0 })} />
            <TextField fullWidth label="Fondos de reserva pendientes ($)" type="number" margin="normal"
              value={form.pending_reserve_funds}
              onChange={(e) => setField({ pending_reserve_funds: parseFloat(e.target.value) || 0 })} />
            <TextField fullWidth label="Otros valores pendientes ($)" type="number" margin="normal"
              value={form.unpaid_amounts}
              onChange={(e) => setField({ unpaid_amounts: parseFloat(e.target.value) || 0 })} />
            <Button type="submit" fullWidth variant="contained" sx={{ mt: 2 }}>Calcular Liquidación</Button>
          </Box>
        </CardContent>
      </Card>

      {result && (
        <>
          <SettlementTable data={result} />
          <Button fullWidth variant="contained" color="secondary" sx={{ mt: 2 }}
            onClick={() => setConfirmBaja(true)}>
            Aceptar y dar de baja
          </Button>
        </>
      )}

      <Dialog open={confirmBaja} onClose={terminating ? undefined : () => setConfirmBaja(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>Dar de baja</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Vas a registrar el finiquito de <b>{selectedEmployee?.first_name} {selectedEmployee?.last_name}</b>{' '}
            (total {money(result?.total ?? 0)}) y darlo de baja. Quedará deshabilitado en el período
            abierto; podrás reactivarlo mientras no cierres el período.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirmBaja(false)} disabled={terminating} color="inherit">Cancelar</Button>
          <Box sx={{ position: 'relative' }}>
            <Button variant="contained" color="secondary" onClick={terminate} disabled={terminating}>
              Dar de baja
            </Button>
            {terminating && <CircularProgress size={22} sx={{ position: 'absolute', top: '50%', left: '50%', mt: '-11px', ml: '-11px' }} />}
          </Box>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={4000} onClose={() => setToast('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setToast('')} severity="error" variant="filled" sx={{ width: '100%' }}>{toast}</Alert>
      </Snackbar>
    </Container>
  );
};

export default Settlement;
