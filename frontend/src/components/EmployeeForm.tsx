import React, { useState } from 'react';
import {
  TextField, Button, Box, MenuItem, FormControlLabel, Checkbox, Divider, Typography,
  CircularProgress,
} from '@mui/material';

export interface EmployeeFormValues {
  cedula: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  salary: number;
  start_date: string; // YYYY-MM-DD
  contract_type: string;
  region_override: string; // '' = hereda la región de la empresa
  accumulate_13th: boolean;
  accumulate_14th: boolean;
  accumulate_reserve_funds: boolean;
  projected_personal_expenses: number;
  family_burdens: number;
  catastrophic_illness_burden: boolean;
}

export const emptyEmployee = (): EmployeeFormValues => ({
  cedula: '', first_name: '', last_name: '', email: '', phone: '',
  salary: 482, start_date: new Date().toISOString().split('T')[0],
  contract_type: 'Indefinido', region_override: '',
  accumulate_13th: true, accumulate_14th: true, accumulate_reserve_funds: true,
  projected_personal_expenses: 0, family_burdens: 0, catastrophic_illness_burden: false,
});

const CONTRACT_TYPES = ['Indefinido', 'Plazo Fijo', 'Eventual'];
const REGIONS = ['Sierra', 'Amazonia', 'Costa', 'Insular'];

interface Props {
  initial: EmployeeFormValues;
  submitLabel: string;
  saving?: boolean;
  onSubmit: (values: EmployeeFormValues) => void;
}

const EmployeeForm: React.FC<Props> = ({ initial, submitLabel, saving, onSubmit }) => {
  const [v, setV] = useState<EmployeeFormValues>(initial);
  const set = (patch: Partial<EmployeeFormValues>) => setV((prev) => ({ ...prev, ...patch }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(v);
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextField fullWidth label="Cédula" margin="normal" value={v.cedula}
        onChange={(e) => set({ cedula: e.target.value })} required />
      <TextField fullWidth label="Nombre" margin="normal" value={v.first_name}
        onChange={(e) => set({ first_name: e.target.value })} required />
      <TextField fullWidth label="Apellido" margin="normal" value={v.last_name}
        onChange={(e) => set({ last_name: e.target.value })} required />
      <TextField fullWidth label="Email" margin="normal" value={v.email}
        onChange={(e) => set({ email: e.target.value })} required />
      <TextField fullWidth label="Teléfono" margin="normal" value={v.phone}
        onChange={(e) => set({ phone: e.target.value })} />
      <TextField fullWidth label="Salario" type="number" margin="normal" value={v.salary}
        onChange={(e) => set({ salary: parseFloat(e.target.value) || 0 })} required />
      <TextField fullWidth label="Fecha de Inicio" type="date" margin="normal" value={v.start_date}
        onChange={(e) => set({ start_date: e.target.value })} InputLabelProps={{ shrink: true }} required />
      <TextField fullWidth select label="Tipo de Contrato" margin="normal" value={v.contract_type}
        onChange={(e) => set({ contract_type: e.target.value })}>
        {CONTRACT_TYPES.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
      </TextField>
      <TextField fullWidth select label="Región (si difiere de la empresa)" margin="normal"
        value={v.region_override} onChange={(e) => set({ region_override: e.target.value })}>
        <MenuItem value=""><em>Hereda de la empresa</em></MenuItem>
        {REGIONS.map((r) => <MenuItem key={r} value={r}>{r}</MenuItem>)}
      </TextField>

      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" sx={{ mb: 1 }}>Provisiones acumuladas</Typography>
      <FormControlLabel
        control={<Checkbox checked={v.accumulate_13th} onChange={(e) => set({ accumulate_13th: e.target.checked })} />}
        label="Acumula Décimo Tercero (13º)" />
      <FormControlLabel
        control={<Checkbox checked={v.accumulate_14th} onChange={(e) => set({ accumulate_14th: e.target.checked })} />}
        label="Acumula Décimo Cuarto (14º)" />
      <FormControlLabel
        control={<Checkbox checked={v.accumulate_reserve_funds} onChange={(e) => set({ accumulate_reserve_funds: e.target.checked })} />}
        label="Acumula Fondos de Reserva" />

      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" sx={{ mb: 1 }}>Impuesto a la Renta</Typography>
      <TextField fullWidth label="Gastos Personales Proyectados (anual)" type="number" margin="normal"
        helperText="Para la rebaja del Impuesto a la Renta" value={v.projected_personal_expenses}
        onChange={(e) => set({ projected_personal_expenses: parseFloat(e.target.value) || 0 })} />
      <TextField fullWidth label="Cargas Familiares" type="number" margin="normal" value={v.family_burdens}
        onChange={(e) => set({ family_burdens: parseInt(e.target.value) || 0 })} />
      <FormControlLabel
        control={<Checkbox checked={v.catastrophic_illness_burden}
          onChange={(e) => set({ catastrophic_illness_burden: e.target.checked })} />}
        label="Carga con enfermedad catastrófica/rara/huérfana (tope 100 canastas)" />

      <Box sx={{ position: 'relative', mt: 3 }}>
        <Button type="submit" fullWidth variant="contained" disabled={saving}>
          {submitLabel}
        </Button>
        {saving && (
          <CircularProgress size={24} sx={{ position: 'absolute', top: '50%', left: '50%', mt: '-12px', ml: '-12px' }} />
        )}
      </Box>
    </Box>
  );
};

export default EmployeeForm;
