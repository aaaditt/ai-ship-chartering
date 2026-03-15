import { useState, useRef, useEffect } from 'react';
import { negotiate as negotiateAPI, getVessels } from '../services/api';
import {
  Send, Bot, User, Ship, Loader, RotateCcw, Zap,
  CheckCircle, XCircle, ArrowUpDown, Info
} from 'lucide-react';

const statusColors = {
  accepted: 'badge-green',
  counter: 'badge-amber',
  rejected: 'badge-red',
  negotiating: 'badge-blue',
  inquiring: 'badge-violet',
};

export default function Negotiation() {
  const [vessels, setVessels] = useState([]);
  const [selectedVessel, setSelectedVessel] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    getVessels({ status: 'Available' }).then(d => {
      const available = (d.vessels || []).filter(v => v.status === 'Available');
      setVessels(available);
      if (available.length > 0) setSelectedVessel(available[0]);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    const msg = input.trim();
    if (!msg || !selectedVessel || loading) return;

    const userMsg = { role: 'user', content: msg };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await negotiateAPI({
        message: msg,
        context: {
          vessel: selectedVessel,
          route: {
            origin: 'Jamnagar',
            destination: 'Rotterdam',
            distance: 6200,
            duration: 18,
          }
        },
        history: [...messages, userMsg],
      });

      if (data.success && data.response) {
        setMessages(prev => [...prev, data.response]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Connection error. Please ensure the backend is running and try again.',
        status: 'error'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const resetChat = () => {
    setMessages([]);
    setInput('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-120px)]">
      {/* Vessel selector */}
      <div className="lg:col-span-1 space-y-4 overflow-y-auto">
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Ship size={16} className="text-cyan-400" /> Select Vessel
          </h3>
          <div className="space-y-1.5 max-h-64 overflow-y-auto">
            {vessels.map(v => (
              <button key={v.id} onClick={() => { setSelectedVessel(v); resetChat(); }}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                  selectedVessel?.id === v.id
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                    : 'text-[var(--navy-300)] hover:bg-[var(--navy-800)]'
                }`}>
                <p className="font-medium">{v.name}</p>
                <p className="text-[10px] text-[var(--navy-500)]">{v.type} • ${v.dailyRate?.toLocaleString()}/day</p>
              </button>
            ))}
          </div>
        </div>

        {selectedVessel && (
          <div className="glass-card p-4 animate-fade-in">
            <h3 className="text-sm font-semibold text-white mb-3">Vessel Details</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">Type</span>
                <span className="badge badge-blue">{selectedVessel.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">DWT</span>
                <span className="text-white">{selectedVessel.dwt?.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">Market Rate</span>
                <span className="text-white font-semibold">${selectedVessel.dailyRate?.toLocaleString()}/day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">Location</span>
                <span className="text-white">{selectedVessel.currentPort}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">Built</span>
                <span className="text-white">{selectedVessel.built}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--navy-400)]">Vetted</span>
                <span>{selectedVessel.vetted ?
                  <span className="badge badge-green"><CheckCircle size={10} /> Yes</span> :
                  <span className="badge badge-red"><XCircle size={10} /> No</span>}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
            <Info size={14} /> Negotiation Tips
          </h3>
          <ul className="text-[11px] text-[var(--navy-400)] space-y-1.5 list-disc pl-3">
            <li>Start by proposing a daily charter rate</li>
            <li>The AI will accept, counter, or reject</li>
            <li>Try rates near market value for best results</li>
            <li>Discuss laytime, demurrage, and payment terms</li>
          </ul>
        </div>
      </div>

      {/* Chat area */}
      <div className="lg:col-span-3 glass-card flex flex-col overflow-hidden">
        {/* Chat header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--glass-border)]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">AI Shipowner Broker</h3>
              <p className="text-[10px] text-emerald-400">Online • Powered by Gemini</p>
            </div>
          </div>
          <button onClick={resetChat} className="btn-secondary text-xs py-1.5 px-3">
            <RotateCcw size={13} /> Reset
          </button>
        </div>

        {/* Messages */}
        <div ref={chatRef} className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 opacity-60">
              <Zap size={40} className="text-cyan-400/50 mb-3" />
              <p className="text-[var(--navy-300)] text-sm">Start negotiating!</p>
              <p className="text-xs text-[var(--navy-500)] mt-1 max-w-xs">
                Select a vessel and propose a daily charter rate to begin.
                Try: "I'd like to offer $28,000/day for this vessel"
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
              <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>
                <div className="flex items-center gap-2 mb-1">
                  {msg.role === 'user' ?
                    <User size={13} className="text-cyan-300" /> :
                    <Bot size={13} className="text-emerald-400" />
                  }
                  <span className="text-[10px] text-[var(--navy-400)]">
                    {msg.role === 'user' ? 'You (Charterer)' : 'Shipowner Broker'}
                  </span>
                  {msg.status && msg.status !== 'error' && (
                    <span className={`badge ${statusColors[msg.status] || 'badge-blue'} text-[10px]`}>
                      {msg.status}
                    </span>
                  )}
                </div>
                <p className="text-sm text-[var(--navy-100)] whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>
                {msg.agreedRate && (
                  <div className="mt-2 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2 text-xs text-emerald-300">
                    <CheckCircle size={13} className="inline mr-1" />
                    Agreed Rate: ${msg.agreedRate?.toLocaleString()}/day
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start animate-fade-in">
              <div className="chat-bubble-ai flex items-center gap-2">
                <Loader size={14} className="animate-spin text-cyan-400" />
                <span className="text-sm text-[var(--navy-400)]">Analyzing your offer...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-5 py-3 border-t border-[var(--glass-border)]">
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2">
            <input
              className="input-field flex-1"
              placeholder={selectedVessel ? `Negotiate for ${selectedVessel.name}...` : 'Select a vessel first'}
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={!selectedVessel || loading}
            />
            <button type="submit" className="btn-primary" disabled={!selectedVessel || loading || !input.trim()}>
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
