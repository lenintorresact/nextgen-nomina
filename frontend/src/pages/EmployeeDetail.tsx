import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Card, CardContent, Box, Button, Divider, List, ListItem, ListItemText, CircularProgress } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';

const EmployeeDetail: React.FC = () => {
  const { id } = useParams();
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmployee = async () => {
        try {
            const token = await getToken();
            const headers = { Authorization: `Bearer ${token}` };
            // Fetch based on the ID. For now we use the general list to find it or a detail endpoint
            const res = await axios.get(`${API_URL}/employees/company/${employee?.company_id}`, { headers });
            // In a real app, use GET /employees/{id}
            setLoading(false);
        } catch (error) {
            console.error("Failed to fetch employee", error);
            setLoading(false);
        }
    };
    fetchEmployee();
  }, [id, getToken]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (!employee) return <Container sx={{ mt: 4 }}><Button onClick={() => navigate('/dashboard')}>Volver</Button><Typography>Empleado no encontrado.</Typography></Container>;

  return (
    <Container sx={{ mt: 4 }}>
      <Button onClick={() => navigate('/dashboard')} sx={{ mb: 2 }}>Volver</Button>
      <Card>
        <CardContent>
            <Typography variant="h4" gutterBottom>{employee.first_name} {employee.last_name}</Typography>
            <Typography color="textSecondary">Cédula: {employee.cedula}</Typography>
            <Typography color="textSecondary">Email: {employee.email}</Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6">Información Laboral</Typography>
            <List>
                <ListItem>
                    <ListItemText primary="Sueldo Base" secondary={`$${employee.salary}`} />
                </ListItem>
                <ListItem>
                    <ListItemText primary="Tipo de Contrato" secondary={employee.contract_type} />
                </ListItem>
                <ListItem>
                    <ListItemText primary="Fecha de Ingreso" secondary={new Date(employee.start_date).toLocaleDateString()} />
                </ListItem>
            </List>
        </CardContent>
      </Card>
    </Container>
  );
};

export default EmployeeDetail;
