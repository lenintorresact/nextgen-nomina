import React, { useEffect, useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem,
  Button, Box, Alert, CircularProgress,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import API_URL from '../api_config';
import { typesForBucket, isHourBased, type EventBucket } from '../lib/payrollEvents';

interface QuickEmployee {
  employee_id: string;
  first_name: string;
  last_name: string;
}

interface Props {
  open: boolean;
  bucket: EventBucket;
  employee: QuickEmployee | null;
  companyId: string;
  onClose: () => void;
  onSaved: () => void;
}

const todayISO = () => new Date().toISOString().split('T')[0];

const QuickEventDialog: React.FC<Props> = ({ open, bucket, employee, companyId, onClose, onSaved }) => {
  const { getToken } = useAuth();
  const options = typesForBucket(bucket);
  const [type, setType] = useState(options[0]?.value ?? '');
  const [amount, setAmount] = useState<number>(0);
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(todayISO());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reinicia el formulario cada vez que se abre o cambia el bucket (ingreso/descuento).
  useEffect(() => {
    if (open) {
      setType(typesForBucket(bucket)[0]?.value ?? '');
      setAmount(0);
      setDescription('');
      setDate(todayISO());
      setError(null);
    }
  }, [open, bucket]);

  const accent = bucket === 'ingreso' ? 'primary' : 'secondary';
  const title = employee ? `${bucket === 'ingreso' ? 'Ingreso' : 'Descuento'} — ${employee.first_name} ${employee.last_name}` : '';
  const hours = isHourBased(type);
  const canSave = !!employee && amount > 0 && description.trim().length > 0 && !saving;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSave || !employee) return;
    setSaving(true);
    setError(null);
    try {
      const token = await getToken();
      await axios.post(
        `${API_URL}/payroll/events`,
        { type, amount, description, date, employee_id: employee.employee_id, company_id: companyId },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      onSaved();
      onClose();
    } catch (err) {
      console.error('Failed to log event', err);
      setError('No se pudo registrar la novedad. Inténtalo de nuevo.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={saving ? undefined : onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ color: `${accent}.dark`, fontWeight: 800 }}>{title}</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            fullWidth select label="Tipo de Novedad" margin="normal"
            value={type} onChange={(e) => setType(e.target.value)}
          >
            {options.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
            ))}
          </TextField>
          <TextField
            fullWidth type="number" margin="normal" required
            label={hours ? 'Nº de Horas' : 'Monto ($)'}
            value={amount}
            onChange={(e) => setAmount(parseFloat(e.target.value))}
          />
          <TextField
            fullWidth label="Descripción" margin="normal" required
            value={description} onChange={(e) => setDescription(e.target.value)}
          />
          <TextField
            fullWidth type="date" label="Fecha" margin="normal"
            value={date} onChange={(e) => setDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={onClose} disabled={saving} color="inherit">Cancelar</Button>
          <Box sx={{ position: 'relative' }}>
            <Button type="submit" variant="contained" color={accent} disabled={!canSave}>
              Guardar
            </Button>
            {saving && (
              <CircularProgress size={22} sx={{ position: 'absolute', top: '50%', left: '50%', mt: '-11px', ml: '-11px' }} />
            )}
          </Box>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default QuickEventDialog;
