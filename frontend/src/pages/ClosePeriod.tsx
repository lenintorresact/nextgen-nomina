import React, { useCallback, useEffect, useState } from 'react';
import {
  Container, Typography, Card, CardContent, Button, Box, Stack, Chip, Divider,
  CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, Snackbar, Alert,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';
import { downloadPdf } from '../lib/pdf';

const money = (n: number) =>
  `$${(n ?? 0).toLocaleString('es-EC', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const calendarMonth = () => new Date().toISOString().slice(0, 7);
const nextPeriod = (p: string) => {
  const [y, m] = p.split('-').map(Number);
  return m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, '0')}`;
};
const formatPeriod = (p: string) => {
  const [y, m] = p.split('-').map(Number);
  const s = new Date(y, m - 1, 1).toLocaleDateString('es-EC', { month: 'long', year: 'numeric' });
  return s.charAt(0).toUpperCase() + s.slice(1);
};

type Confirm = { action: 'close' | 'reopen'; period: string } | null;

const ClosePeriod: React.FC = () => {
  const { getToken } = useAuth();
  const [company, setCompany] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<Confirm>(null);
  const [toast, setToast] = useState('');

  const load = useCallback(async () => {
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const compRes = await axios.get(`${API_URL}/companies/`, { headers });
      if (compRes.data.length === 0) return;
      const comp = compRes.data[0];
      setCompany(comp);
      const prevRes = await axios.get(`${API_URL}/payroll/preview/${comp.id}`, { headers });
      setPreview(prevRes.data);
    } catch (error) {
      console.error('Failed to load close-period data', error);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => { load(); }, [load]);

  const runConfirm = async () => {
    if (!confirm || !company) return;
    setBusy(true);
    try {
      const token = await getToken();
      const headers = { Authorization: `Bearer ${token}` };
      const path = confirm.action === 'close' ? 'close-period' : 'reopen-period';
      await axios.post(`${API_URL}/payroll/${path}/${company.id}/${confirm.period}`, {}, { headers });
      setToast(confirm.action === 'close' ? 'Período cerrado' : 'Período reabierto');
      setConfirm(null);
      await load();
    } catch (error: any) {
      console.error('close/reopen failed', error);
      setToast(error?.response?.data?.detail ?? 'No se pudo completar la acción.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  const currentPeriod = company?.current_period || calendarMonth();
  const closedPeriods: string[] = [...(company?.closed_periods ?? [])].sort().reverse();
  const latestClosed = closedPeriods[0];
  const count = preview?.employee_count ?? 0;
  const netTotal = preview?.totals?.net_salary ?? 0;

  const reportBtn = (period: string, label: string, urlPath: string, fileBase: string) => (
    <Button size="small" variant="outlined" color="inherit" sx={{ color: 'text.primary' }}
      onClick={() => company && downloadPdf(
        getToken,
        `${API_URL}/payroll/${urlPath}/${company.id}/pdf?period=${period}`,
        `${fileBase}_${period}.pdf`,
      )}>
      {label}
    </Button>
  );

  return (
    <Container sx={{ mt: 4, mb: 6 }} maxWidth="sm">
      <Typography variant="h4" gutterBottom>Cierre de Nómina</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
            Cierra el mes para dejar la nómina en firme y poder generar los documentos
            oficiales (planilla IESS, Ministerio de Trabajo). Los empleados reciben su rol
            automáticamente. Tras el cierre, las nuevas novedades pasan al período siguiente;
            si algo faltó, puedes reabrirlo.
          </Typography>

          <Typography variant="overline" sx={{ color: 'primary.dark' }}>Período abierto</Typography>
          <Typography variant="h5" sx={{ mb: 1.5 }}>{formatPeriod(currentPeriod)}</Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 3 }} flexWrap="wrap" useFlexGap>
            <Chip label={`${count} ${count === 1 ? 'empleado' : 'empleados'}`} variant="outlined" />
            <Chip label={`Líquido total ${money(netTotal)}`} color="primary" variant="outlined" sx={{ borderWidth: 2 }} />
          </Stack>

          <Button fullWidth variant="contained"
            onClick={() => setConfirm({ action: 'close', period: currentPeriod })}>
            Cerrar {formatPeriod(currentPeriod)}
          </Button>
        </CardContent>
      </Card>

      {closedPeriods.length > 0 && (
        <Card>
          <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
            <Typography variant="h6" gutterBottom>Períodos cerrados</Typography>
            {closedPeriods.map((p, i) => (
              <Box key={p}>
                {i > 0 && <Divider sx={{ my: 2 }} />}
                <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" useFlexGap spacing={1}>
                  <Typography sx={{ fontWeight: 700 }}>{formatPeriod(p)}</Typography>
                  {p === latestClosed && (
                    <Button size="small" color="secondary"
                      onClick={() => setConfirm({ action: 'reopen', period: p })}>
                      Reabrir
                    </Button>
                  )}
                </Stack>
                <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap" useFlexGap>
                  {reportBtn(p, 'Rol Consolidado (PDF)', 'payroll-report', 'rol_consolidado')}
                  {reportBtn(p, 'Planilla IESS (PDF)', 'planilla-iess', 'planilla_iess')}
                </Stack>
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      <Dialog open={!!confirm} onClose={busy ? undefined : () => setConfirm(null)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>
          {confirm?.action === 'close' ? `Cerrar ${confirm ? formatPeriod(confirm.period) : ''}` : `Reabrir ${confirm ? formatPeriod(confirm.period) : ''}`}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirm?.action === 'close' ? (
              <>
                Vas a cerrar <b>{confirm ? formatPeriod(confirm.period) : ''}</b> para {count}{' '}
                {count === 1 ? 'empleado' : 'empleados'} (líquido total {money(netTotal)}). Las nuevas
                novedades pasarán a <b>{confirm ? formatPeriod(nextPeriod(confirm.period)) : ''}</b>.
                Podrás reabrir el período si necesitas corregir algo.
              </>
            ) : (
              <>
                Vas a reabrir <b>{confirm ? formatPeriod(confirm.period) : ''}</b>. Se eliminarán los
                roles generados de ese período y volverás a poder registrar novedades en él.
              </>
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setConfirm(null)} disabled={busy} color="inherit">Cancelar</Button>
          <Box sx={{ position: 'relative' }}>
            <Button variant="contained" color={confirm?.action === 'close' ? 'primary' : 'secondary'}
              onClick={runConfirm} disabled={busy}>
              {confirm?.action === 'close' ? 'Cerrar período' : 'Reabrir'}
            </Button>
            {busy && <CircularProgress size={22} sx={{ position: 'absolute', top: '50%', left: '50%', mt: '-11px', ml: '-11px' }} />}
          </Box>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!toast} autoHideDuration={3000} onClose={() => setToast('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setToast('')} severity="success" variant="filled" sx={{ width: '100%' }}>
          {toast}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ClosePeriod;
