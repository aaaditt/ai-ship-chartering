import { useState } from 'react';
import { matchVessels } from '../services/api';
import {
  Ship, MapPin, Package, ArrowRight, Loader,
  Star, Navigation, Clock, DollarSign, CheckCircle, AlertTriangle
} from 'lucide-react';

const cargoTypes = ['Crude Oil', 'Gasoline', 'Diesel', 'Naphtha', 'Jet Fuel', 'Fuel Oil', 'Condensate', 'LPG', 'Petrochemicals', 'Clean Products'];
const ports = ['Jamnagar', 'Rotterdam', 'Ras Tanura', 'Fujairah', 'Singapore', 'Bonny Terminal', 'Houston', 'Mumbai', 'Piraeus', 'Qingdao', 'Durban', 'Mongstad', 'Ain Sukhna'];

function ScoreBar({ label, score, color }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-[var(--navy-400)]">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--navy-800)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" 
          style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="w-8 text-right text-[var(--navy-300)]">{score}</span>
    </div>
  );
}

export default function CharterRequest() {
  const [form, setForm] = useState({ cargoType: '', cargoVolume: '', originPort: '', destinationPort: '' });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!form.cargoType || !form.cargoVolume || !form.originPort || !form.destinationPort) {
      setError('All fields are required');
      return;
    }
    if (form.originPort === form.destinationPort) {
      setError('Origin and destination must be different');
      return;
    }
    setLoading(true);
    try {
      const data = await matchVessels({
        cargoType: form.cargoType,
        cargoVolume: parseFloat(form.cargoVolume),
        originPort: form.originPort,
        destinationPort: form.destinationPort,
        topN: 5
      });
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to match vessels. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Form */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-bold text-white mb-1">Charter Request</h2>
        <p className="text-xs text-[var(--navy-400)] mb-5">Enter cargo details to find the best vessel match</p>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-[var(--navy-400)] mb-1.5 font-medium">Cargo Type</label>
            <select className="input-field" value={form.cargoType}
              onChange={e => setForm({ ...form, cargoType: e.target.value })}>
              <option value="">Select cargo type</option>
              {cargoTypes.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-[var(--navy-400)] mb-1.5 font-medium">Volume (MT)</label>
            <input type="number" className="input-field" placeholder="e.g. 90000"
              value={form.cargoVolume} onChange={e => setForm({ ...form, cargoVolume: e.target.value })} />
          </div>
          <div>
            <label className="block text-xs text-[var(--navy-400)] mb-1.5 font-medium">Origin Port</label>
            <select className="input-field" value={form.originPort}
              onChange={e => setForm({ ...form, originPort: e.target.value })}>
              <option value="">Select origin</option>
              {ports.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-[var(--navy-400)] mb-1.5 font-medium">Destination Port</label>
            <select className="input-field" value={form.destinationPort}
              onChange={e => setForm({ ...form, destinationPort: e.target.value })}>
              <option value="">Select destination</option>
              {ports.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div className="md:col-span-2 flex items-center gap-3">
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? <Loader size={16} className="animate-spin" /> : <Ship size={16} />}
              {loading ? 'Matching...' : 'Find Vessels'}
            </button>
            {error && <p className="text-xs text-red-400 flex items-center gap-1"><AlertTriangle size={14} />{error}</p>}
          </div>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4 stagger-children">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">
              Top {results.matchCount} Vessel Recommendations
            </h2>
            <span className="badge badge-blue">
              {results.query.cargoType} • {Number(results.query.cargoVolume).toLocaleString()} MT
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-[var(--navy-400)]">
            <MapPin size={14} />
            {results.query.originPort} <ArrowRight size={12} /> {results.query.destinationPort}
          </div>

          {results.matches.map((match, index) => {
            const v = match.vessel;
            const s = match.scores;
            const scoreClass = match.totalScore >= 70 ? 'score-high' : match.totalScore >= 45 ? 'score-mid' : 'score-low';

            return (
              <div key={v.id} className="glass-card p-5">
                <div className="flex flex-col md:flex-row gap-4">
                  {/* Score ring */}
                  <div className="flex flex-col items-center gap-1">
                    <div className={`score-ring ${scoreClass}`} style={{ '--score': match.totalScore }}>
                      <span>{match.totalScore}</span>
                    </div>
                    <span className="text-[10px] text-[var(--navy-500)]">#{index + 1} Match</span>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-white font-semibold">{v.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="badge badge-blue">{v.type}</span>
                          <span className="text-xs text-[var(--navy-400)]">{v.dwt?.toLocaleString()} DWT</span>
                          <span className="text-xs text-[var(--navy-400)]">• Built {v.built}</span>
                          {v.vetted && <span className="badge badge-green"><CheckCircle size={10} /> Vetted</span>}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-bold">${v.dailyRate?.toLocaleString()}/day</p>
                        <span className={`badge ${v.status === 'Available' ? 'badge-green' : 'badge-amber'}`}>{v.status}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 text-xs">
                      <div className="flex items-center gap-1.5">
                        <MapPin size={13} className="text-[var(--navy-400)]" />
                        <div>
                          <p className="text-[var(--navy-500)]">Current Port</p>
                          <p className="text-white">{v.currentPort}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Navigation size={13} className="text-[var(--navy-400)]" />
                        <div>
                          <p className="text-[var(--navy-500)]">Dist to Origin</p>
                          <p className="text-white">{match.distanceToOrigin?.toLocaleString()} NM</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock size={13} className="text-[var(--navy-400)]" />
                        <div>
                          <p className="text-[var(--navy-500)]">ETA to Origin</p>
                          <p className="text-white">{match.etaDays} days</p>
                        </div>
                      </div>
                      {match.voyageEstimate && (
                        <div className="flex items-center gap-1.5">
                          <DollarSign size={13} className="text-[var(--navy-400)]" />
                          <div>
                            <p className="text-[var(--navy-500)]">Est. Total Cost</p>
                            <p className="text-white">${match.voyageEstimate.totalCost?.toLocaleString()}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Score breakdown */}
                    <div className="space-y-1.5">
                      <ScoreBar label="Distance" score={s.distance} color="#06b6d4" />
                      <ScoreBar label="Capacity" score={s.capacity} color="#10b981" />
                      <ScoreBar label="Age" score={s.age} color="#8b5cf6" />
                      <ScoreBar label="Vetting" score={s.vetting} color="#f59e0b" />
                      <ScoreBar label="Availability" score={s.availability} color="#f43f5e" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
