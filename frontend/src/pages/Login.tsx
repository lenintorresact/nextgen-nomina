import React from 'react';
import { Container, Box, Typography, Button, Paper } from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import { signInWithGoogle } from '../firebase';

const Login: React.FC = () => {
  const handleLogin = async () => {
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error("Login failed", error);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%', textAlign: 'center' }}>
          <Typography variant="h4" gutterBottom>
            Payroll Ecuador
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Sistema de nómina para micro y pequeñas empresas.
          </Typography>
          <Button
            variant="contained"
            fullWidth
            startIcon={<GoogleIcon />}
            onClick={handleLogin}
            sx={{ mt: 2 }}
          >
            Iniciar sesión con Google
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
