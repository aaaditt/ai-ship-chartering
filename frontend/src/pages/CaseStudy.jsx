import { useState, useEffect, useRef } from 'react';
import { matchVessels, optimizeRoute } from '../services/api';
import { Play, Pause, RotateCcw, CheckCircle, Clock, Ship, MapPin, ArrowRight, Loader, Zap, Award } from 'lucide-react';

const DEMO_STEPS = [
  { id: 1, label: 'Receiving Charter Request', desc: 'Cargo: 90,000 MT Gasoline — Jamnagar → Rotterdam', dur: 2000 },
  { id: 2, label: 'Running AI Vessel Matching', desc: 'Scoring 18 vessels across 5 parameters...', dur: 2500 },
  { id: 3, label: 'Selecting Optimal Vessel', desc: 'LR2 type recommended for clean product transport', dur: 2000 },
  { id: 4, label: 'Optimizing Route', desc: 'Jamnagar → Suez Canal → Rotterdam (6,200 NM, 18 days)', dur: 2000 },
  { id: 5, label: 'Generating Cost Estimate', desc: 'Total voyage cost calculated with fuel and charter rate', dur: 1500 },
  { id: 6, label: 'Fixture Complete', desc: 'Charter confirmed in under 30 minutes vs 4-6 hours traditional', dur: 1500 },
];

export default function CaseStudy() {
  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(0);
  const [vessels, setVessels] = useState(null);
  const [route, setRoute] = useState(null);
  const [done, setDone] = useState(false);
  const timers = useRef([]);

  const runDemo = async () => {
    setRunning(true); setStep(1); setDone(false); setVessels(null); setRoute(null);

    // Step 1-2: Match vessels
    timers.current.push(setTimeout(() => setStep(2), 2000));
    try {
      const vData = await matchVessels({ cargoType: 'Gasoline', cargoVolume: 90000, originPort: 'Jamnagar', destinationPort: 'Rotterdam', topN: 5 });
      setVessels(vData);
    } catch(e) { console.error(e); }

    timers.current.push(setTimeout(() => setStep(3), 4500));

    // Step 4: Route
    timers.current.push(setTimeout(async () => {
      setStep(4);
      try {
        const rData = await optimizeRoute({ originPort: 'Jamnagar', destinationPort: 'Rotterdam', cargoVolume: 90000 });
        setRoute(rData);
      } catch(e) { console.error(e); }
    }, 6500));

    timers.current.push(setTimeout(() => setStep(5), 8500));
    timers.current.push(setTimeout(() => { setStep(6); setDone(true); setRunning(false); }, 10000));
  };

  const reset = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setRunning(false); setStep(0); setDone(false); setVessels(null); setRoute(null);
  };

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const topVessel = vessels?.matches?.[0];

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="glass-card p-6 bg-gradient-to-r from-amber-500/10 to-cyan-500/5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Award size={20} className="text-amber-400" />
              <span className="badge badge-amber">Reliance Industries Case Study</span>
            </div>
            <h1 className="text-xl font-bold text-white mb-1">Jamnagar → Rotterdam Demo</h1>
            <p className="text-xs text-[var(--navy-400)] max-w-lg">
              Live demonstration of AI-powered chartering for 90,000 MT Gasoline shipment
              from Reliance Jamnagar Refinery to Rotterdam, Netherlands.
            </p>
          </div>
          <div className="flex gap-2">
            {!running && !done && (
              <button onClick={runDemo} className="btn-accent"><Play size={16} /> Run Demo</button>
            )}
            {(running || done) && (
              <button onClick={reset} className="btn-secondary"><RotateCcw size={16} /> Reset</button>
            )}
          </div>
        </div>
      </div>

      {/* Scenario Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Cargo', val: '90,000 MT Gasoline', icon: Ship },
          { label: 'Origin', val: 'Jamnagar, India', icon: MapPin },
          { label: 'Destination', val: 'Rotterdam, NL', icon: MapPin },
          { label: 'AI Target Time', val: '< 30 minutes', icon: Clock },
        ].map((s, i) => (
          <div key={i} className="glass-card p-4">
            <s.icon size={16} className="text-cyan-400 mb-2" />
            <p className="text-xs text-[var(--navy-500)]">{s.label}</p>
            <p className="text-sm font-semibold text-white">{s.val}</p>
          </div>
        ))}
      </div>

      {/* Progress Steps */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Demo Progress</h3>
        <div className="space-y-3">
          {DEMO_STEPS.map(s => {
            const isDone = step > s.id;
            const isCurrent = step === s.id;
            return (
              <div key={s.id} className={`flex items-center gap-3 p-3 rounded-lg transition-all ${
                isCurrent ? 'bg-cyan-500/10 border border-cyan-500/20' :
                isDone ? 'bg-emerald-500/5' : 'opacity-40'
              }`}>
                <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0" style={{
                  background: isDone ? '#10b981' : isCurrent ? '#06b6d4' : 'var(--navy-700)'
                }}>
                  {isDone ? <CheckCircle size={14} className="text-white" /> :
                   isCurrent ? <Loader size={14} className="text-white animate-spin" /> :
                   <span className="text-xs text-[var(--navy-400)]">{s.id}</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">{s.label}</p>
                  <p className="text-xs text-[var(--navy-400)]">{s.desc}</p>
                </div>
                {isCurrent && <span className="badge badge-blue text-[10px]">In Progress</span>}
                {isDone && <span className="badge badge-green text-[10px]">Complete</span>}
              </div>
            );
          })}
        </div>
      </div>

      {/* Results */}
      {topVessel && step >= 3 && (
        <div className="glass-card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Zap size={16} className="text-cyan-400" /> Selected Vessel
          </h3>
          <div className="flex flex-wrap gap-4">
            <div>
              <p className="text-lg font-bold text-white">{topVessel.vessel.name}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="badge badge-blue">{topVessel.vessel.type}</span>
                <span className="text-xs text-[var(--navy-400)]">{topVessel.vessel.dwt?.toLocaleString()} DWT</span>
              </div>
            </div>
            <div className="flex gap-6 text-xs">
              <div><p className="text-[var(--navy-500)]">Score</p><p className="text-xl font-bold text-cyan-400">{topVessel.totalScore}</p></div>
              <div><p className="text-[var(--navy-500)]">Rate</p><p className="text-white font-semibold">${topVessel.vessel.dailyRate?.toLocaleString()}/day</p></div>
              <div><p className="text-[var(--navy-500)]">ETA</p><p className="text-white font-semibold">{topVessel.etaDays} days</p></div>
              {topVessel.voyageEstimate && (
                <div><p className="text-[var(--navy-500)]">Total Cost</p><p className="text-white font-semibold">${topVessel.voyageEstimate.totalCost?.toLocaleString()}</p></div>
              )}
            </div>
          </div>
        </div>
      )}

      {route && step >= 4 && (
        <div className="glass-card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold text-white mb-3">Route Details</h3>
          <div className="flex flex-wrap gap-6 text-xs">
            <div><p className="text-[var(--navy-500)]">Route</p><p className="text-white font-semibold">{route.routeName}</p></div>
            <div><p className="text-[var(--navy-500)]">Distance</p><p className="text-white font-semibold">{route.routeDistanceNM?.toLocaleString()} NM</p></div>
            <div><p className="text-[var(--navy-500)]">Duration</p><p className="text-white font-semibold">{route.typicalDurationDays} days</p></div>
            {route.canalTransit && <div><p className="text-[var(--navy-500)]">Canal</p><p className="text-amber-300 font-semibold">{route.canalTransit}</p></div>}
          </div>
          {route.riskFactors?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {route.riskFactors.map((r,i) => <span key={i} className="badge badge-amber text-[10px]">⚠ {r}</span>)}
            </div>
          )}
        </div>
      )}

      {done && (
        <div className="glass-card p-6 bg-gradient-to-r from-emerald-500/10 to-transparent animate-fade-in text-center">
          <CheckCircle size={40} className="text-emerald-400 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-white mb-1">Fixture Complete!</h2>
          <p className="text-sm text-[var(--navy-300)]">
            Full chartering process completed in <span className="text-emerald-400 font-bold">~30 seconds</span> (simulated).
          </p>
          <p className="text-xs text-[var(--navy-500)] mt-2">Traditional process would take 4-6 hours with 25-30 staff members.</p>
        </div>
      )}
    </div>
  );
}
