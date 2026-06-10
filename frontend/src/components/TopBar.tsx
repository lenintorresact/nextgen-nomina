import React from 'react';
import { AppBar, Toolbar, Box, Typography, Avatar, Button } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { logout } from '../firebase';

const LogoMark: React.FC = () => (
  <Box
    sx={{
      width: 36, height: 36, borderRadius: '50%',
      background: 'linear-gradient(135deg, #16B69E, #39D6BB)',
      display: 'grid', placeItems: 'center', color: '#fff', fontWeight: 800, fontSize: 18,
    }}
  >
    N
  </Box>
);

const TopBar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  // No chrome on the login screen — let it feel like a landing page.
  if (location.pathname === '/') return null;

  const isAnon = user?.isAnonymous;

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <AppBar position="sticky">
      <Toolbar sx={{ gap: 1.5 }}>
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1.5, cursor: 'pointer' }}
          onClick={() => navigate('/dashboard')}
        >
          <LogoMark />
          <Typography variant="h6" sx={{ fontSize: 18 }}>Nómina&nbsp;Ecuador</Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {isAnon && (
          <Typography variant="caption" sx={{ color: 'text.secondary', display: { xs: 'none', sm: 'block' } }}>
            Modo demo
          </Typography>
        )}
        <Button size="small" color="inherit" onClick={handleLogout} sx={{ color: 'text.secondary' }}>
          Salir
        </Button>
        <Avatar sx={{ width: 32, height: 32, bgcolor: '#DFF4EF', color: '#0E9A85', fontWeight: 800, fontSize: 13 }}>
          {(user?.email?.[0] ?? 'D').toUpperCase()}
        </Avatar>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;
