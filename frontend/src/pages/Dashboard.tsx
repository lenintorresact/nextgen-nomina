import React, { useEffect, useState } from 'react';
import { Container, Typography, Grid, Card, CardContent, Button, List, ListItem, ListItemText, Divider, Box, ListItemButton } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const [employees, setEmployees] = useState<any[]>([]);
  const [company, setCompany] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = await (window as any).firebaseUser?.getIdToken();
        const headers = { Authorization: `Bearer ${token}` };

        const compRes = await axios.get('http://localhost:8000/companies/', { headers });
        if (compRes.data.length > 0) {
          setCompany(compRes.data[0]);
          const empRes = await axios.get(`http://localhost:8000/employees/company/${compRes.data[0].id}`, { headers });
          setEmployees(empRes.data);
        }
      } catch (error) {
        console.error("Dashboard data load failed", error);
      }
    };
    fetchData();
  }, []);

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        {company ? company.name : 'Mi Empresa'}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Empleados</Typography>
                <Button startIcon={<AddIcon />} variant="outlined" href="/add-employee">
                  Añadir
                </Button>
              </Box>
              <List>
                {employees.map((emp) => (
                  <React.Fragment key={emp.id}>
                    <ListItem disablePadding>
                      <ListItemButton onClick={() => window.location.href = `/employee/${emp.id}`}>
                        <ListItemText
                          primary={`${emp.first_name} ${emp.last_name}`}
                          secondary={`Sueldo: $${emp.salary}`}
                        />
                      </ListItemButton>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'primary.light', color: 'white' }}>
            <CardContent>
              <Typography variant="h6">Acciones Rápidas</Typography>
              <Button fullWidth variant="contained" color="secondary" sx={{ mt: 2 }} href="/log-event">
                Registrar Novedad
              </Button>
              <Button fullWidth variant="contained" color="warning" sx={{ mt: 2 }} href="/close-period">
                Cerrar Mes
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
