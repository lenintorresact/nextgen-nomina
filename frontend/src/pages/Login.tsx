import React, { useState } from 'react';
import { Container, Box, Typography, Button, Paper, Divider, CircularProgress, Alert } from '@mui/material';
import GoogleIcon from '@mui/icons-material/Google';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { signInWithGoogle, signInAsDemo, auth } from '../firebase';
import API_URL from '../api_config';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    try {
      await signInWithGoogle();
      navigate('/dashboard');
    } catch (error) {
      console.error("Login failed", error);
      setError('No se pudo iniciar sesión con Google.');
    }
  };

  const handleDemo = async () => {
    setError(null);
    setLoadingDemo(true);
    try {
      // 1) Sesión anónima (sin registro). 2) Sembrar datos de ejemplo y esperar
      // a que terminen ANTES de navegar, para que el Dashboard no rebote a
      // /onboarding al no encontrar empresa todavía.
      await signInAsDemo();
      const token = await auth.currentUser?.getIdToken();
      await axios.post(`${API_URL}/demo/seed`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      navigate('/dashboard');
    } catch (error) {
      console.error("Demo init failed", error);
      setError('No se pudo iniciar la demo. Inténtalo de nuevo.');
      setLoadingDemo(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={0} sx={{ p: 4, width: '100%', textAlign: 'center', boxShadow: '0 14px 34px rgba(20,60,52,.10)' }}>
          <Box
            sx={{
              width: 56, height: 56, borderRadius: '50%', mx: 'auto', mb: 2,
              background: 'linear-gradient(135deg, #16B69E, #39D6BB)',
              display: 'grid', placeItems: 'center', color: '#fff', fontWeight: 800, fontSize: 26,
            }}
          >
            N
          </Box>
          <Typography variant="h4" gutterBottom>
            Nómina Ecuador
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Registra novedades y mira cómo la nómina se calcula sola, en tiempo real.
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={loadingDemo ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
            onClick={handleDemo}
            disabled={loadingDemo}
          >
            {loadingDemo ? 'Preparando demo…' : 'Entrar a la demo'}
          </Button>
          <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
            Sin registro. Se crea una empresa de ejemplo para que pruebes el concepto.
          </Typography>

          <Divider sx={{ my: 3 }}>o</Divider>

          <Button
            variant="outlined"
            fullWidth
            startIcon={<GoogleIcon />}
            onClick={handleLogin}
            disabled={loadingDemo}
          >
            Iniciar sesión con Google
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
