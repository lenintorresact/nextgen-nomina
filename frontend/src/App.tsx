import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Onboarding from './pages/Onboarding';
import AddEmployee from './pages/AddEmployee';
import LogEvent from './pages/LogEvent';
import EmployeeDashboard from './pages/EmployeeDashboard';
import ClosePeriod from './pages/ClosePeriod';
import EmployeeDetail from './pages/EmployeeDetail';
import './i18n';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/add-employee" element={<AddEmployee />} />
            <Route path="/employee/:id" element={<EmployeeDetail />} />
            <Route path="/log-event" element={<LogEvent />} />
            <Route path="/close-period" element={<ClosePeriod />} />
            <Route path="/employee-dashboard" element={<EmployeeDashboard />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
