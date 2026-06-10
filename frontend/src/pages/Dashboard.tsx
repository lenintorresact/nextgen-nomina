import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Card, CardContent, Button, List, ListItem, ListItemText,
  Divider, Box, Stack, ListItemButton, Chip, CircularProgress
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import BoltIcon from '@mui/icons-material/Bolt';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import API_URL from '../api_config';

const money = (n: number) => `$${(n ?? 0).toFixed(2)}`;

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
        if (compRes.data.length === 0) {
          navigate('/onboarding');
          return;
        }
        const comp = compRes.data[0];
        setCompany(comp);

        const prevRes = await axios.get(`${API_URL}/payroll/preview/${comp.id}`, { headers });
        setPreview(prevRes.data);
      } catch (error) {
        console.error("Dashboard data load failed", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [getToken, navigate]);

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>;
  }

  const totals = preview?.totals;
  const provisions = totals
    ? totals.thirteenth_salary + totals.fourteenth_salary + totals.reserve_funds + totals.vacation_provision
    : 0;

  return (
    <Container sx={{ mt: 4, mb: 6 }}>
      <Typography variant="h4" gutterBottom>
        {company ? company.name : 'Mi Empresa'}
      </Typography>

      {/* Tarjeta de cálculo en vivo: el corazón de la demo */}
      <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
            <BoltIcon fontSize="small" />
            <Typography variant="overline">Nómina calculada en vivo · {preview?.period}</Typography>
          </Stack>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3} sx={{ mt: 1 }}>
            <Box>
              <Typography variant="h4">{money(totals?.net_salary ?? 0)}</Typography>
              <Typography variant="body2">Líquido a pagar</Typography>
            </Box>
            <Box>
              <Typography variant="h5">{money(totals?.iess_employer ?? 0)}</Typography>
              <Typography variant="body2">Aporte patronal IESS</Typography>
            </Box>
            <Box>
              <Typography variant="h5">{money(provisions)}</Typography>
              <Typography variant="body2">Provisiones (13º, 14º, fondos, vac.)</Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="flex-start">
        <Card sx={{ flex: 2, width: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Empleados ({preview?.employee_count ?? 0})</Typography>
              <Button startIcon={<AddIcon />} variant="outlined" onClick={() => navigate('/add-employee')}>
                Añadir
              </Button>
            </Box>
            <List>
              {preview?.employees.map((emp) => (
                <React.Fragment key={emp.employee_id}>
                  <ListItem
                    disablePadding
                    secondaryAction={
                      <Chip label={money(emp.net_salary)} color="primary" variant="outlined" />
                    }
                  >
                    <ListItemButton
                      onClick={() => navigate(`/employee/${emp.employee_id}`, { state: { employee: emp, company } })}
                    >
                      <ListItemText
                        primary={`${emp.first_name} ${emp.last_name}`}
                        secondary={`Sueldo base: ${money(emp.base_salary)}`}
                      />
                    </ListItemButton>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, width: '100%' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Acciones</Typography>
            <Button fullWidth variant="contained" sx={{ mt: 1 }} onClick={() => navigate('/log-event')}>
              Registrar Novedad
            </Button>
            <Button fullWidth variant="outlined" color="warning" sx={{ mt: 2 }} onClick={() => navigate('/close-period')}>
              Cerrar Mes
            </Button>
            <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 2 }}>
              Registra una novedad y vuelve aquí: el total se recalcula al instante, sin cerrar el mes.
            </Typography>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default Dashboard;
