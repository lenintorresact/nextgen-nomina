import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Card, CardContent, Box, Button, Divider, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';

const EmployeeDetail: React.FC = () => {
  const { id } = useParams();
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<any>(null);

  useEffect(() => {
    // Fetch employee details and their history
  }, [id, getToken]);

  if (!employee) return <Typography>Cargando...</Typography>;

  return (
    <Container sx={{ mt: 4 }}>
      <Button onClick={() => navigate('/dashboard')}>Volver</Button>
      <Typography variant="h4">{employee.first_name} {employee.last_name}</Typography>
      {/* Detail UI */}
    </Container>
  );
};

export default EmployeeDetail;
