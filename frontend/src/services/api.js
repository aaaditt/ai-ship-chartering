/**
 * API Service Layer
 * Handles all communication with the Flask backend
 *
 * In development: Vite proxy forwards /api → http://localhost:5000
 * In production:  VITE_API_URL points to the Render backend, e.g.
 *                 https://ai-ship-chartering-backend.onrender.com
 */
import axios from 'axios';

// Use the env variable when available (set in .env.production / Vercel env settings).
// Falls back to '/api' which is handled by the Vite proxy in local dev.
const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

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
