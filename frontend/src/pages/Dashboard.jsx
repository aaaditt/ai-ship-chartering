import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAnalytics, getVessels } from '../services/api';
import {
  Ship, Clock, Users, TrendingUp, ArrowRight,
  Anchor, DollarSign, CheckCircle, Zap
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center`}
          style={{ background: `${color}20` }}>
          <Icon size={20} style={{ color }} />
        </div>
        <Zap size={14} className="text-[var(--navy-500)]" />
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-[var(--navy-400)] mt-1">{label}</p>
      {sub && <p className="text-[11px] text-emerald-400 mt-1">{sub}</p>}
    </div>
  );
}

function QuickAction({ to, icon: Icon, title, desc }) {
  return (
    <Link to={to} className="glass-card p-5 group cursor-pointer block">
      <div className="flex items-center justify-between mb-3">
        <Icon size={20} className="text-cyan-400" />
        <ArrowRight size={16} className="text-[var(--navy-500)] group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
      </div>
      <h3 className="text-white font-semibold text-sm mb-1">{title}</h3>
      <p className="text-xs text-[var(--navy-400)]">{desc}</p>
    </Link>
  );
}

export default function Dashboard() {
  const [kpis, setKpis] = useState(null);
  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getAnalytics('kpis'),
      getVessels()
    ]).then(([analytics, vesselData]) => {
      setKpis(analytics.kpis);
      setVessels(vesselData.vessels || []);
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const available = vessels.filter(v => v.status === 'Available').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="glass-card p-6 md:p-8 bg-gradient-to-r from-cyan-500/10 to-violet-500/5">
        <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
          AI Ship Chartering Platform
        </h1>
        <p className="text-[var(--navy-300)] text-sm max-w-xl">
          Intelligent vessel matching, route optimization, and AI-powered negotiation.
          Reducing chartering time from <span className="text-cyan-400 font-semibold">4-6 hours to 30 minutes</span>.
        </p>
        <div className="flex gap-3 mt-5">
          <Link to="/charter" className="btn-primary">
            <Ship size={16} /> New Charter Request
          </Link>
          <Link to="/case-study" className="btn-secondary">
            Run Demo
          </Link>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
        <StatCard icon={Ship} label="Active Vessels" value={available}
          sub={`${vessels.length} total fleet`} color="#06b6d4" />
        <StatCard icon={Clock} label="Avg Fixture Time" value={`${kpis?.avgTimeToFixture || 28}m`}
          sub="90% faster" color="#10b981" />
        <StatCard icon={CheckCircle} label="Success Rate" value={`${kpis?.onTimeDelivery || 96.5}%`}
          sub="+14% improvement" color="#8b5cf6" />
        <StatCard icon={DollarSign} label="Revenue YTD" value={`$${((kpis?.revenueYTD || 0) / 1e6).toFixed(1)}M`}
          sub="Fleet utilization" color="#f59e0b" />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 stagger-children">
          <QuickAction to="/charter" icon={Anchor} title="Charter Request"
            desc="Match cargo to optimal vessels with AI scoring" />
          <QuickAction to="/negotiate" icon={Ship} title="AI Negotiation"
            desc="Negotiate charter rates with AI-powered broker" />
          <QuickAction to="/analytics" icon={TrendingUp} title="Analytics"
            desc="Compare Traditional vs AI-powered performance" />
        </div>
      </div>

      {/* Fleet Overview Table */}
      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--glass-border)]">
          <h2 className="text-sm font-semibold text-white">Fleet Overview</h2>
          <span className="text-xs text-[var(--navy-400)]">{vessels.length} vessels</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[var(--navy-400)] text-xs border-b border-[var(--glass-border)]">
                <th className="text-left px-5 py-3 font-medium">Vessel</th>
                <th className="text-left px-5 py-3 font-medium">Type</th>
                <th className="text-left px-5 py-3 font-medium">DWT</th>
                <th className="text-left px-5 py-3 font-medium">Location</th>
                <th className="text-left px-5 py-3 font-medium">Status</th>
                <th className="text-right px-5 py-3 font-medium">Rate/Day</th>
              </tr>
            </thead>
            <tbody>
              {vessels.slice(0, 8).map(v => (
                <tr key={v.id} className="border-b border-[var(--glass-border)] hover:bg-[var(--navy-800)]/50 transition-colors">
                  <td className="px-5 py-3 font-medium text-white">{v.name}</td>
                  <td className="px-5 py-3">
                    <span className="badge badge-blue">{v.type}</span>
                  </td>
                  <td className="px-5 py-3 text-[var(--navy-300)]">{v.dwt?.toLocaleString()}</td>
                  <td className="px-5 py-3 text-[var(--navy-300)]">{v.currentPort}</td>
                  <td className="px-5 py-3">
                    <span className={`badge ${
                      v.status === 'Available' ? 'badge-green' :
                      v.status === 'On Voyage' ? 'badge-amber' : 'badge-red'
                    }`}>{v.status}</span>
                  </td>
                  <td className="px-5 py-3 text-right text-white font-medium">
                    ${v.dailyRate?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
