import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Card, CardContent, Button, List, ListItem, ListItemButton,
  ListItemText, ListItemAvatar, Avatar, Divider, Box, Stack, Chip, CircularProgress
} from '@mui/material';
import { keyframes } from '@mui/system';
import AddIcon from '@mui/icons-material/Add';
import BoltIcon from '@mui/icons-material/Bolt';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';
import { downloadPdf } from './EmployeeDetail';

const money = (n: number) =>
  `$${(n ?? 0).toLocaleString('es-EC', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const initials = (a: string, b: string) => `${a?.[0] ?? ''}${b?.[0] ?? ''}`.toUpperCase();

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(255,107,94,.5); }
  70% { box-shadow: 0 0 0 9px rgba(255,107,94,0); }
  100% { box-shadow: 0 0 0 0 rgba(255,107,94,0); }
`;

interface EmployeePreview {
  employee_id: string;
  first_name: string;
  last_name: string;
  base_salary: number;
  net_salary: number;
  iess_employee: number;
  iess_employer: number;
  thirteenth_salary: number;
  fourteenth_salary: number;
  reserve_funds: number;
  vacation_provision: number;
  earnings_breakdown: Record<string, number>;
  deductions_breakdown: Record<string, number>;
}

interface Preview {
  period: string;
  employee_count: number;
  employees: EmployeePreview[];
  totals: {
    net_salary: number;
    iess_employer: number;
    thirteenth_salary: number;
    fourteenth_salary: number;
    reserve_funds: number;
    vacation_provision: number;
  };
}

const Stat: React.FC<{ value: string; caption: string; primary?: boolean }> = ({ value, caption, primary }) => (
  <Box>
    <Typography sx={{ fontWeight: 800, fontSize: { xs: 28, sm: 34 }, lineHeight: 1.05, color: primary ? 'primary.dark' : 'text.primary' }}>
      {value}
    </Typography>
    <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 600, mt: 0.5 }}>{caption}</Typography>
  </Box>
);

const Dashboard: React.FC = () => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [company, setCompany] = useState<any>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = await getToken();
        const headers = { Authorization: `Bearer ${token}` };
        const compRes = await axios.get(`${API_URL}/companies/`, { headers });
        if (compRes.data.length === 0) { navigate('/onboarding'); return; }
        const comp = compRes.data[0];
        setCompany(comp);
        const prevRes = await axios.get(`${API_URL}/payroll/preview/${comp.id}`, { headers });
        setPreview(prevRes.data);
      } catch (error) {
        console.error('Dashboard data load failed', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [getToken, navigate]);

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>;
  }

  const totals = preview?.totals;
  const provisions = totals
    ? totals.thirteenth_salary + totals.fourteenth_salary + totals.reserve_funds + totals.vacation_provision
    : 0;

  return (
    <Container sx={{ mt: 4, mb: 6 }}>
      <Typography variant="h4" gutterBottom>{company ? company.name : 'Mi Empresa'}</Typography>

      {/* Hero: cálculo en vivo */}
      <Card sx={{ mb: 3, borderLeft: '7px solid', borderColor: 'primary.main', overflow: 'hidden' }}>
        <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Stack direction="row" alignItems="center" spacing={1.2} sx={{ mb: 2 }}>
            <Box sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: 'secondary.main', animation: `${pulse} 1.6s infinite` }} />
            <Typography variant="overline" sx={{ color: 'primary.dark' }}>
              Nómina calculada en vivo · {preview?.period}
            </Typography>
            <BoltIcon sx={{ fontSize: 16, color: 'primary.main' }} />
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={{ xs: 2, sm: 5 }}>
            <Stat primary value={money(totals?.net_salary ?? 0)} caption="Líquido a pagar" />
            <Stat value={money(totals?.iess_employer ?? 0)} caption="Aporte patronal IESS" />
            <Stat value={money(provisions)} caption="Provisiones (13º, 14º, fondos, vac.)" />
          </Stack>
        </CardContent>
      </Card>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="flex-start">
        <Card sx={{ flex: 2, width: '100%' }}>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2.5, pb: 1.5 }}>
              <Typography variant="h6">Empleados ({preview?.employee_count ?? 0})</Typography>
              <Button startIcon={<AddIcon />} onClick={() => navigate('/add-employee')}
                sx={{ bgcolor: '#DFF4EF', color: 'primary.dark', '&:hover': { bgcolor: '#CFEEE7' } }}>
                Añadir
              </Button>
            </Box>
            <List disablePadding>
              {preview?.employees.map((emp, i) => (
                <React.Fragment key={emp.employee_id}>
                  {i > 0 && <Divider component="li" />}
                  <ListItem
                    disablePadding
                    secondaryAction={
                      <Chip label={money(emp.net_salary)} variant="outlined" color="primary"
                        sx={{ borderWidth: 2, bgcolor: '#fff' }} />
                    }
                  >
                    <ListItemButton sx={{ py: 1.5, px: 2.5 }}
                      onClick={() => navigate(`/employee/${emp.employee_id}`, { state: { employee: emp, company } })}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: '#DFF4EF', color: 'primary.dark', fontWeight: 800 }}>
                          {initials(emp.first_name, emp.last_name)}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={<Typography sx={{ fontWeight: 700 }}>{emp.first_name} {emp.last_name}</Typography>}
                        secondary={`Sueldo base ${money(emp.base_salary)}`}
                      />
                    </ListItemButton>
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, width: '100%' }}>
          <CardContent sx={{ p: 2.5 }}>
            <Typography variant="h6" gutterBottom>Acciones</Typography>
            <Button fullWidth variant="contained" sx={{ mt: 1 }} onClick={() => navigate('/log-event')}>
              Registrar Novedad
            </Button>
            <Button fullWidth variant="outlined" color="inherit" sx={{ mt: 1.5, color: 'text.primary' }}
              onClick={() => navigate('/close-period')}>
              Cerrar Mes
            </Button>
            <Button fullWidth variant="outlined" color="inherit" sx={{ mt: 1.5, color: 'text.primary' }}
              onClick={() => navigate('/settlement')}>
              Liquidación de Haberes
            </Button>
            <Button fullWidth variant="outlined" color="inherit" sx={{ mt: 1.5, color: 'text.primary' }}
              disabled={!company}
              onClick={() => company && downloadPdf(
                getToken,
                `${API_URL}/payroll/payroll-report/${company.id}/pdf${preview?.period ? `?period=${preview.period}` : ''}`,
                `rol_consolidado_${preview?.period ?? ''}.pdf`,
              )}>
              Rol Consolidado (PDF)
            </Button>
            <Button fullWidth variant="outlined" color="inherit" sx={{ mt: 1.5, color: 'text.primary' }}
              disabled={!company}
              onClick={() => company && downloadPdf(
                getToken,
                `${API_URL}/payroll/planilla-iess/${company.id}/pdf${preview?.period ? `?period=${preview.period}` : ''}`,
                `planilla_iess_${preview?.period ?? ''}.pdf`,
              )}>
              Planilla IESS (PDF)
            </Button>
            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 2, fontWeight: 600 }}>
              Registra una novedad y el total se recalcula al instante, sin cerrar el mes.
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default Dashboard;
