/**
 * API Service Layer
 * Handles all communication with the Flask backend
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Vessels ───
export const getVessels = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.type) params.append('type', filters.type);
  if (filters.status) params.append('status', filters.status);
  if (filters.vetted !== undefined) params.append('vetted', filters.vetted);
  return api.get(`/vessels?${params}`).then(r => r.data);
};

export const matchVessels = (data) =>
  api.post('/vessels/match', data).then(r => r.data);

// ─── Routes ───
export const getRoutes = () =>
  api.get('/routes').then(r => r.data);

export const optimizeRoute = (data) =>
  api.post('/routes/optimize', data).then(r => r.data);

// ─── Negotiation ───
export const negotiate = (data) =>
  api.post('/negotiate', data).then(r => r.data);

// ─── Analytics ───
export const getAnalytics = (section = 'all') =>
  api.get(`/analytics?section=${section}`).then(r => r.data);

export default api;
