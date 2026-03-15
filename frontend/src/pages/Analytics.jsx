import { useEffect, useState } from 'react';
import { getAnalytics } from '../services/api';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';
import { Clock, Users, TrendingUp, DollarSign, ArrowDown, Calculator } from 'lucide-react';

const COLORS = ['#06b6d4', '#10b981', '#f59e0b', '#8b5cf6', '#f43f5e'];

function MetricCard({ icon: Icon, label, trad, ai, improvement }) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className="text-cyan-400" />
        <span className="text-xs font-semibold text-white">{label}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-[var(--navy-800)] rounded-lg p-2.5 text-center">
          <p className="text-[10px] text-[var(--navy-500)] mb-1">Traditional</p>
          <p className="text-sm font-bold text-[var(--navy-300)]">{trad}</p>
        </div>
        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-2.5 text-center">
          <p className="text-[10px] text-cyan-400 mb-1">AI-Powered</p>
          <p className="text-sm font-bold text-cyan-300">{ai}</p>
        </div>
      </div>
      <div className="flex items-center justify-center gap-1 mt-2">
        <ArrowDown size={12} className="text-emerald-400" />
        <span className="text-[11px] text-emerald-400 font-semibold">{improvement}</span>
      </div>
    </div>
  );
}

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fixtures, setFixtures] = useState(250);

  useEffect(() => {
    getAnalytics('all').then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="spinner" /></div>;

  const comp = data?.comparison;
  const savings = data?.annualSavings;
  const rates = data?.freightRates;

  const bars = [
    { name: 'Time (min)', Traditional: comp?.traditional?.timePerFixture?.minutes, AI: comp?.aiPowered?.timePerFixture?.minutes },
    { name: 'Staff', Traditional: comp?.traditional?.staffRequired?.avg, AI: comp?.aiPowered?.staffRequired?.avg },
    { name: 'Cost ($K)', Traditional: (comp?.traditional?.costPerFixture?.avg||0)/1000, AI: (comp?.aiPowered?.costPerFixture?.avg||0)/1000 },
    { name: 'Rounds', Traditional: comp?.traditional?.negotiationCycles?.avg, AI: comp?.aiPowered?.negotiationCycles?.avg },
  ];

  const rateHist = rates?.vesselTypes?.VLCC?.history?.map(h => ({
    month: h.month.split('-')[1],
    VLCC: h.rate/1000,
    Suezmax: rates.vesselTypes.Suezmax.history.find(s=>s.month===h.month)?.rate/1000,
    Aframax: rates.vesselTypes.Aframax.history.find(s=>s.month===h.month)?.rate/1000,
  })) || [];

  const calcSaved = fixtures * ((comp?.traditional?.costPerFixture?.avg||20000) - (comp?.aiPowered?.costPerFixture?.avg||4000));
  const calcHrs = fixtures * ((comp?.traditional?.timePerFixture?.minutes||300)-(comp?.aiPowered?.timePerFixture?.minutes||30))/60;

  const ttip = { background:'#162a46', border:'1px solid rgba(90,143,194,0.2)', borderRadius:10, fontSize:12 };

  return (
    <div className="space-y-6">
      <div className="glass-card p-6 bg-gradient-to-r from-violet-500/10 to-cyan-500/5">
        <h1 className="text-xl font-bold text-white mb-1">Performance Analytics</h1>
        <p className="text-xs text-[var(--navy-400)]">Traditional vs AI-Powered Chartering — Reliance Industries case study</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
        <MetricCard icon={Clock} label="Time per Fixture" trad="4-6 hours" ai="30 minutes" improvement="90% reduction" />
        <MetricCard icon={Users} label="Staff Required" trad="25-30" ai="8-10" improvement="70% reduction" />
        <MetricCard icon={TrendingUp} label="Success Rate" trad="85%" ai="97%" improvement="+14% improvement" />
        <MetricCard icon={DollarSign} label="Cost per Fixture" trad="$15-25K" ai="$3-5K" improvement="80% reduction" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Process Comparison</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={bars}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(90,143,194,0.1)" />
              <XAxis dataKey="name" tick={{fontSize:11,fill:'#82b1db'}} />
              <YAxis tick={{fontSize:11,fill:'#82b1db'}} />
              <Tooltip contentStyle={ttip} labelStyle={{color:'#dce9f5'}} />
              <Bar dataKey="Traditional" fill="#5a8fc2" radius={[4,4,0,0]} />
              <Bar dataKey="AI" fill="#06b6d4" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Success Rate</h3>
          <div className="grid grid-cols-2 gap-4">
            {[{label:'Traditional',val:85,color:'#5a8fc2'},{label:'AI-Powered',val:97,color:'#06b6d4'}].map(s=>(
              <div key={s.label} className="text-center">
                <p className="text-xs text-[var(--navy-400)] mb-2">{s.label}</p>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart><Pie data={[{v:s.val},{v:100-s.val}]} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="v" startAngle={90} endAngle={-270}>
                    <Cell fill={s.color} /><Cell fill="#1e3a5f" />
                  </Pie></PieChart>
                </ResponsiveContainer>
                <p className="text-2xl font-bold -mt-2" style={{color:s.color}}>{s.val}%</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Freight Rate Trends ($/K per day)</h3>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={rateHist}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(90,143,194,0.1)" />
            <XAxis dataKey="month" tick={{fontSize:11,fill:'#82b1db'}} />
            <YAxis tick={{fontSize:11,fill:'#82b1db'}} />
            <Tooltip contentStyle={ttip} labelStyle={{color:'#dce9f5'}} />
            <Legend wrapperStyle={{fontSize:11}} />
            <Line type="monotone" dataKey="VLCC" stroke="#06b6d4" strokeWidth={2} dot={{r:3}} />
            <Line type="monotone" dataKey="Suezmax" stroke="#8b5cf6" strokeWidth={2} dot={{r:3}} />
            <Line type="monotone" dataKey="Aframax" stroke="#f59e0b" strokeWidth={2} dot={{r:3}} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-card p-5 bg-gradient-to-r from-emerald-500/5 to-transparent">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Calculator size={16} className="text-emerald-400" /> Annual Savings Calculator
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="text-xs text-[var(--navy-400)] block mb-2">Fixtures/Year</label>
            <input type="range" min="50" max="500" value={fixtures} onChange={e=>setFixtures(+e.target.value)} className="w-full accent-cyan-500" />
            <p className="text-lg font-bold text-white mt-1">{fixtures}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-[var(--navy-400)] mb-1">Annual Savings</p>
            <p className="text-3xl font-bold text-emerald-400">${(calcSaved/1e6).toFixed(1)}M</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-[var(--navy-400)] mb-1">Hours Saved</p>
            <p className="text-3xl font-bold text-cyan-400">{calcHrs.toLocaleString()}</p>
            <p className="text-xs text-[var(--navy-500)]">{(calcHrs/8).toFixed(0)} working days</p>
          </div>
        </div>
      </div>

      {savings && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Annual Financial Impact</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[var(--navy-800)] rounded-xl p-4 text-center">
              <p className="text-xs text-[var(--navy-400)] mb-2">Traditional Cost</p>
              <p className="text-2xl font-bold text-[var(--navy-300)]">${(savings.traditional.totalAnnualCost/1e6).toFixed(1)}M</p>
            </div>
            <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 text-center">
              <p className="text-xs text-cyan-400 mb-2">AI-Powered Cost</p>
              <p className="text-2xl font-bold text-cyan-300">${(savings.aiPowered.totalAnnualCost/1e6).toFixed(1)}M</p>
            </div>
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
              <p className="text-xs text-emerald-400 mb-2">Net Savings</p>
              <p className="text-3xl font-bold text-emerald-300">${(savings.netSavings/1e6).toFixed(1)}M</p>
              <p className="text-xs text-emerald-400/70 mt-1">ROI: {savings.roi} • Payback: {savings.paybackMonths}mo</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
