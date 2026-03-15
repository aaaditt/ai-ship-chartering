import { useEffect, useState } from 'react';
import { getRoutes, optimizeRoute } from '../services/api';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Navigation, Clock, DollarSign, AlertTriangle, Loader, Fuel, Ship } from 'lucide-react';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const portIcon = new L.DivIcon({
  className: '',
  html: `<div style="width:14px;height:14px;background:#06b6d4;border:2px solid #fff;border-radius:50%;box-shadow:0 0 8px rgba(6,182,212,0.6)"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const waypointIcon = new L.DivIcon({
  className: '',
  html: `<div style="width:8px;height:8px;background:#f59e0b;border:1.5px solid #fff;border-radius:50%;"></div>`,
  iconSize: [8, 8],
  iconAnchor: [4, 4],
});

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds?.length >= 2) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [bounds, map]);
  return null;
}

const ports = ['Jamnagar', 'Rotterdam', 'Ras Tanura', 'Fujairah', 'Singapore', 'Bonny Terminal', 'Houston', 'Mumbai', 'Piraeus', 'Qingdao', 'Durban', 'Mongstad', 'Ain Sukhna'];

export default function RouteMap() {
  const [routes, setRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [optimized, setOptimized] = useState(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ originPort: '', destinationPort: '', cargoVolume: '90000' });

  useEffect(() => {
    getRoutes().then(d => setRoutes(d.routes || [])).catch(console.error);
  }, []);

  const handleOptimize = async () => {
    if (!form.originPort || !form.destinationPort) return;
    setLoading(true);
    try {
      const data = await optimizeRoute(form);
      setOptimized(data);
      setSelectedRoute(null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRouteClick = (route) => {
    setSelectedRoute(route);
    setOptimized(null);
  };

  const activeWaypoints = optimized?.waypoints || selectedRoute?.waypoints || [];
  const routeLine = activeWaypoints.map(w => [w.lat, w.lon]);
  const bounds = routeLine.length >= 2 ? routeLine : [[20, 0], [50, 80]];
  const activeInfo = optimized || selectedRoute;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-120px)]">
      {/* Sidebar */}
      <div className="lg:col-span-1 space-y-4 overflow-y-auto pr-1">
        {/* Route finder */}
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Route Finder</h3>
          <div className="space-y-2">
            <select className="input-field" value={form.originPort}
              onChange={e => setForm({ ...form, originPort: e.target.value })}>
              <option value="">Origin port</option>
              {ports.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select className="input-field" value={form.destinationPort}
              onChange={e => setForm({ ...form, destinationPort: e.target.value })}>
              <option value="">Destination port</option>
              {ports.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <input type="number" className="input-field" placeholder="Cargo volume (MT)"
              value={form.cargoVolume} onChange={e => setForm({ ...form, cargoVolume: e.target.value })} />
            <button className="btn-primary w-full" onClick={handleOptimize} disabled={loading}>
              {loading ? <Loader size={15} className="animate-spin" /> : <Navigation size={15} />}
              {loading ? 'Optimizing...' : 'Optimize Route'}
            </button>
          </div>
        </div>

        {/* Route info panel */}
        {activeInfo && (
          <div className="glass-card p-4 animate-fade-in">
            <h3 className="text-sm font-semibold text-white mb-3">
              {activeInfo.routeName || activeInfo.name}
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center gap-2">
                <Navigation size={14} className="text-cyan-400" />
                <span className="text-[var(--navy-300)]">Distance:</span>
                <span className="text-white font-medium ml-auto">
                  {(activeInfo.routeDistanceNM || activeInfo.distanceNM)?.toLocaleString()} NM
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-cyan-400" />
                <span className="text-[var(--navy-300)]">Duration:</span>
                <span className="text-white font-medium ml-auto">
                  {activeInfo.typicalDurationDays} days
                </span>
              </div>
              {activeInfo.canalTransit && (
                <div className="flex items-center gap-2">
                  <Ship size={14} className="text-amber-400" />
                  <span className="text-[var(--navy-300)]">Canal:</span>
                  <span className="text-white font-medium ml-auto">{activeInfo.canalTransit}</span>
                </div>
              )}
              {activeInfo.recommendedVesselTypes?.length > 0 && (
                <div>
                  <p className="text-[var(--navy-400)] mb-1">Recommended Vessels:</p>
                  <div className="flex flex-wrap gap-1">
                    {activeInfo.recommendedVesselTypes.map(t => (
                      <span key={t} className="badge badge-blue">{t}</span>
                    ))}
                  </div>
                </div>
              )}
              {activeInfo.riskFactors?.length > 0 && (
                <div>
                  <p className="text-[var(--navy-400)] mb-1.5 flex items-center gap-1">
                    <AlertTriangle size={12} className="text-amber-400" /> Risk Factors:
                  </p>
                  {activeInfo.riskFactors.map((r, i) => (
                    <p key={i} className="text-amber-300/80 text-[11px] mb-1 pl-4">• {r}</p>
                  ))}
                </div>
              )}
              {optimized?.costEstimates?.length > 0 && (
                <div className="border-t border-[var(--glass-border)] pt-3 mt-2 space-y-2">
                  <p className="text-[var(--navy-400)] font-medium">Cost Estimates:</p>
                  {optimized.costEstimates.map((ce, i) => (
                    <div key={i} className="bg-[var(--navy-800)] rounded-lg p-2.5">
                      <div className="flex justify-between mb-1">
                        <span className="badge badge-blue">{ce.vesselType}</span>
                        <span className="text-white font-semibold">${ce.estimate.totalCost?.toLocaleString()}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1 text-[10px] text-[var(--navy-400)]">
                        <span>Charter: ${ce.estimate.charterCost?.toLocaleString()}</span>
                        <span>Fuel: ${ce.estimate.fuelCost?.toLocaleString()}</span>
                        <span>Duration: {ce.estimate.durationDays}d</span>
                        <span>Per MT: ${ce.estimate.costPerMT}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Predefined routes list */}
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Predefined Routes</h3>
          <div className="space-y-1.5 max-h-60 overflow-y-auto">
            {routes.map(r => (
              <button key={r.id} onClick={() => handleRouteClick(r)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                  selectedRoute?.id === r.id
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                    : 'text-[var(--navy-300)] hover:bg-[var(--navy-800)]'
                }`}>
                <p className="font-medium">{r.name}</p>
                <p className="text-[10px] text-[var(--navy-500)]">{r.distanceNM?.toLocaleString()} NM • {r.typicalDurationDays}d</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="lg:col-span-2 glass-card overflow-hidden" style={{ minHeight: 400 }}>
        <MapContainer center={[25, 55]} zoom={3} className="w-full h-full" style={{ minHeight: 400 }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          <FitBounds bounds={bounds} />
          {routeLine.length >= 2 && (
            <Polyline positions={routeLine} color="#06b6d4" weight={3} opacity={0.8} dashArray="8 4" />
          )}
          {activeWaypoints.map((w, i) => {
            const isEndpoint = i === 0 || i === activeWaypoints.length - 1;
            return (
              <Marker key={i} position={[w.lat, w.lon]} icon={isEndpoint ? portIcon : waypointIcon}>
                <Popup>{w.name}</Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
