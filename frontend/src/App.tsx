import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, ShieldAlert, Cpu } from 'lucide-react';
import './index.css';

const API_BASE = 'http://127.0.0.1:8000/api';

function App() {
  const [kpis, setKpis] = useState({
    session_pnl: 0,
    total_trades: 0,
    active_markets: 0,
    avg_edge_pct: 0,
    ai_inference_count: 0
  });
  
  const [trades, setTrades] = useState([]);
  const [pnlData, setPnlData] = useState([]);
  const [health, setHealth] = useState({ status: 'offline' });

  const fetchData = async () => {
    try {
      const hd = await fetch(`${API_BASE}/health`).then(r => r.json());
      setHealth(hd);

      const [kRes, tRes, pRes] = await Promise.all([
        fetch(`${API_BASE}/kpis`).then(r => r.json()),
        fetch(`${API_BASE}/trades?limit=50`).then(r => r.json()),
        fetch(`${API_BASE}/pnl`).then(r => r.json())
      ]);

      setKpis(kRes);
      setTrades(tRes.trades);
      setPnlData(pRes);
    } catch (err) {
      console.error("API error", err);
    }
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 3000);
    return () => clearInterval(iv);
  }, []);

  const formatMoney = (val: number) => {
    if (val === undefined || val === null) return "$0.00";
    const sign = val >= 0 ? '+' : '-';
    return `${sign}$${Math.abs(val).toFixed(2)}`;
  };

  const renderBadge = (decision: string) => {
    if (!decision) return null;
    if (decision.includes('TRADE')) return <span className="badge badge-trade">{decision}</span>;
    return <span className="badge badge-skip">{decision}</span>;
  };

  return (
    <>
      <header className="header">
        <div className="logo-section">
          <div className={`logo-dot ${health.status === 'ok' ? 'active' : ''}`}></div>
          <h1 className="mono">BEXAI <span style={{color: 'var(--text-muted)'}}>|</span> KALSHI</h1>
        </div>
        <div style={{display: 'flex', gap: '20px', alignItems: 'center'}}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={14} /> LIVE MONITORING
          </div>
          <div className="badge" style={{background: 'rgba(255, 217, 59, 0.1)', color: 'var(--accent-yellow)', border: '1px solid rgba(255, 217, 59, 0.3)'}}>
             LOCAL DEV
          </div>
        </div>
      </header>

      <main className="dashboard-grid">
        <div className="kpi-row">
          <div className="glass-card kpi-card">
            <span className="kpi-label">Session PNL</span>
            <span className={`kpi-value ${kpis.session_pnl >= 0 ? 'text-green' : 'text-red'}`}>
              {formatMoney(kpis.session_pnl)}
            </span>
          </div>
          <div className="glass-card kpi-card">
            <span className="kpi-label">Active Markets</span>
            <span className="kpi-value">{kpis.active_markets}</span>
          </div>
          <div className="glass-card kpi-card">
            <span className="kpi-label">Total Trades</span>
            <span className="kpi-value">{kpis.total_trades}</span>
          </div>
          <div className="glass-card kpi-card">
            <span className="kpi-label">AI Inferences</span>
            <span className="kpi-value text-blue">{kpis.ai_inference_count}</span>
          </div>
          <div className="glass-card kpi-card">
            <span className="kpi-label">Avg Edge</span>
            <span className="kpi-value text-yellow">{kpis.avg_edge_pct.toFixed(2)}%</span>
          </div>
        </div>

        <div className="main-column">
          <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '20px', letterSpacing: '1px'}}>Cumulative P&L</h2>
            <div style={{ flex: 1, minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pnlData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis 
                    dataKey="timestamp" 
                    hide 
                  />
                  <YAxis 
                    stroke="var(--text-muted)" 
                    tickFormatter={(val) => `$${val}`}
                    domain={['auto', 'auto']}
                    width={60}
                    fontSize={12}
                  />
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-card-hover)', border: '1px solid var(--border-subtle)', borderRadius: '8px' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                    formatter={(val: number) => [`$${val.toFixed(2)}`, 'PNL']}
                    labelFormatter={() => ''}
                  />
                  <Line 
                    type="stepAfter" 
                    dataKey="pnl" 
                    stroke="var(--accent-green)" 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 6, fill: 'var(--accent-green)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card">
            <h2 style={{fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '20px', letterSpacing: '1px'}}>Recent Trade Stream</h2>
            <div className="trades-table-container">
              <table className="trades-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Market</th>
                    <th>Decision</th>
                    <th>Prob</th>
                    <th>Edge</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{textAlign: 'center', color: 'var(--text-muted)'}}>Waiting for trade data...</td>
                    </tr>
                  )}
                  {trades.map((t: any, i: number) => {
                    const di = t.debate_inference || {};
                    const date = new Date(t.timestamp * 1000);
                    return (
                      <tr key={i}>
                        <td className="mono" style={{color: 'var(--text-muted)'}}>{date.toLocaleTimeString()}</td>
                        <td style={{maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
                          {t.market}
                        </td>
                        <td>{renderBadge(di.decision)}</td>
                        <td className="mono">{(di.llm_prob * 100).toFixed(1)}%</td>
                        <td className="mono" style={{color: di.edge > 0 ? 'var(--accent-green)' : 'var(--text-primary)'}}>
                          {di.edge ? `+${(di.edge * 100).toFixed(1)}%` : '-'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="side-column">
          <div className="glass-card" style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
             <h2 style={{fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '8px'}}>
               <Cpu size={16} /> TimesFM 2.5
             </h2>
             {trades.length > 0 && trades[0].debate_inference?.timesfm_forecast ? (
               <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                 <div style={{fontSize: '24px', fontWeight: 'bold'}} className={trades[0].debate_inference.timesfm_forecast.direction === 'UP' ? 'text-green' : trades[0].debate_inference.timesfm_forecast.direction === 'DOWN' ? 'text-red' : 'text-secondary'}>
                   {trades[0].debate_inference.timesfm_forecast.direction}
                 </div>
                 <div style={{fontSize: '14px', color: 'var(--text-secondary)'}}>
                   {trades[0].debate_inference.timesfm_forecast.summary}
                 </div>
               </div>
             ) : (
               <div style={{color: 'var(--text-muted)', fontSize: '13px'}}>No TimesFM forecast for recent market.</div>
             )}
          </div>
          
          <div className="glass-card" style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
             <h2 style={{fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '8px'}}>
               <ShieldAlert size={16} /> Latest Debate
             </h2>
             {trades.length > 0 && trades[0].debate_inference ? (
               <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                 <div style={{background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px'}}>
                    <div style={{fontSize: '11px', color: 'var(--accent-green)', textTransform: 'uppercase', marginBottom: '4px'}}>Bull Case</div>
                    <div style={{fontSize: '13px', color: 'var(--text-secondary)'}}>{trades[0].debate_inference.bull_arg}</div>
                 </div>
                 <div style={{background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px'}}>
                    <div style={{fontSize: '11px', color: 'var(--accent-red)', textTransform: 'uppercase', marginBottom: '4px'}}>Bear Case</div>
                    <div style={{fontSize: '13px', color: 'var(--text-secondary)'}}>{trades[0].debate_inference.bear_arg}</div>
                 </div>
               </div>
             ) : (
               <div style={{color: 'var(--text-muted)', fontSize: '13px'}}>No debate inference available.</div>
             )}
          </div>
        </div>
      </main>
    </>
  );
}

export default App;
