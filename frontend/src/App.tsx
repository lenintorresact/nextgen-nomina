import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from './context/AuthContext';
import TopBar from './components/TopBar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/Onboarding';
import AddEmployee from './pages/AddEmployee';
import LogEvent from './pages/LogEvent';
import EmployeeDashboard from './pages/EmployeeDashboard';
import ClosePeriod from './pages/ClosePeriod';
import EmployeeEdit from './pages/EmployeeEdit';
import PayslipView from './pages/PayslipView';
import Settlement from './pages/Settlement';
import './i18n';

// "Menta fresca" — warm, approachable SMB fintech: mint + cream, rounded Nunito,
// pill shapes, soft shadows.
const theme = createTheme({
  palette: {
    primary: { main: '#16B69E', dark: '#0E9A85', light: '#39D6BB', contrastText: '#ffffff' },
    secondary: { main: '#FF6B5E', contrastText: '#ffffff' },
    success: { main: '#16B69E' },
    warning: { main: '#F2A65A' },
    background: { default: '#F1F8F5', paper: '#FFFFFF' },
    text: { primary: '#1F2A2A', secondary: '#7B8A86' },
    divider: '#E7F0EC',
  },
  shape: { borderRadius: 18 },
  typography: {
    fontFamily: 'Nunito, system-ui, Avenir, Helvetica, Arial, sans-serif',
    h4: { fontWeight: 800, letterSpacing: 0.2 },
    h5: { fontWeight: 800 },
    h6: { fontWeight: 800 },
    button: { fontWeight: 800, textTransform: 'none' },
    overline: { fontWeight: 800, letterSpacing: 1 },
  },
  components: {
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: 24,
          boxShadow: '0 2px 6px rgba(22,182,158,.05), 0 14px 34px rgba(20,60,52,.07)',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 999, paddingTop: 10, paddingBottom: 10 },
        outlined: { borderColor: '#E7F0EC' },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 800, borderRadius: 999 },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { backgroundColor: '#FFFFFF', color: '#1F2A2A', boxShadow: 'none', borderBottom: '1px solid #E7F0EC' },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <TopBar />
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/add-employee" element={<AddEmployee />} />
            <Route path="/employee/:id" element={<EmployeeEdit />} />
            <Route path="/employee/:id/rol" element={<PayslipView />} />
            <Route path="/log-event" element={<LogEvent />} />
            <Route path="/close-period" element={<ClosePeriod />} />
            <Route path="/settlement" element={<Settlement />} />
            <Route path="/employee-dashboard" element={<EmployeeDashboard />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
