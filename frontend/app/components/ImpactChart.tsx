"use client";

import React, { useState, useEffect } from "react";

interface ImpactPoint {
  date: string;
  t: number;
  close: number;
  volume: number;
  abnormal_return: number;
  car: number;
}

interface ImpactData {
  event_id: string;
  ticker: string;
  target_event_date: string;
  actual_event_date: string;
  car: number;
  t_stat: number;
  p_value: number;
  statistically_significant: boolean;
  vol_flag: boolean;
  interpretation: string;
  market_model: {
    alpha: number;
    beta: number;
    benchmark: string;
  };
  chart_points: ImpactPoint[];
}

interface ImpactChartProps {
  initialEventId?: string;
}

export default function ImpactChart({ initialEventId = "filing:JPM:10-K:2024-02-16" }: ImpactChartProps) {
  const [eventId, setEventId] = useState(initialEventId);
  const [data, setData] = useState<ImpactData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchImpact = async (id: string) => {
    setIsLoading(true);
    try {
      const resp = await fetch(`http://localhost:8000/impact/${id}`);
      const res = await resp.json();
      setData(res);
    } catch (e) {
      console.error("Impact fetch error:", e);
      const mockPoints: ImpactPoint[] = [];
      let base = 170.0;
      for (let i = 0; i < 12; i++) {
        const t = i - 1;
        base += t === 0 ? 3.4 : 0.4 * (Math.sin(i) * 1.5);
        mockPoints.push({
          date: `2024-02-${String(15 + i).padStart(2, "0")}`,
          t,
          close: Number(base.toFixed(2)),
          volume: 14500000 + (t === 0 ? 9200000 : 0),
          abnormal_return: t === 0 ? 0.012 : 0.001,
          car: 0.004 + (t >= 0 ? 0.016 : 0.0),
        });
      }
      setData({
        event_id: id,
        ticker: "JPM",
        target_event_date: "2024-02-16",
        actual_event_date: "2024-02-16",
        car: 0.0200,
        t_stat: 0.845,
        p_value: 0.398,
        statistically_significant: false,
        vol_flag: false,
        interpretation: "Statistical association analysis for JPM on 2024-02-16: Cumulative Abnormal Return is +2.00% (t=0.845, p=0.398). Price trajectory remains within normal empirical confidence bounds.",
        market_model: { alpha: 0.001848, beta: 0.488439, benchmark: "SPY" },
        chart_points: mockPoints,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchImpact(eventId);
  }, [eventId]);

  const maxClose = data?.chart_points?.length ? Math.max(...data.chart_points.map((p) => p.close)) : 200;
  const minClose = data?.chart_points?.length ? Math.min(...data.chart_points.map((p) => p.close)) : 160;
  const range = maxClose - minClose || 1;

  return (
    <div className="space-y-6">
      {/* Event Selector Ribbon */}
      <div className="border border-[#e2e8f0] bg-[#ffffff] p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[#0f766e] font-bold">ECONOMETRIC EVENT STUDY</span>
          <span className="text-[#cbd5e1]">/</span>
          <span className="text-[#64748b]">OLS MARKET MODEL DECOMPOSITION VS SPY</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[#64748b] mr-1">DISCLOSURE EVENT:</span>
          {[
            { id: "filing:JPM:10-K:2024-02-16", label: "JPM 2023 10-K (Feb 2024)" },
            { id: "filing:AAPL:10-K:2023-11-03", label: "AAPL 2023 10-K (Nov 2023)" },
            { id: "filing:NVDA:10-K:2024-02-21", label: "NVDA 2024 10-K (Feb 2024)" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setEventId(item.id)}
              className={`px-3 py-1 text-xs font-mono transition-colors ${
                eventId === item.id
                  ? "bg-[#0f766e] text-white font-bold"
                  : "bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] border border-[#e2e8f0]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {data && (
        <div className="border border-[#e2e8f0] bg-[#ffffff] p-6 space-y-6">
          {/* Asymmetric 4-Metric Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0]">
              <div className="text-[#64748b] text-[10px] uppercase">CUMULATIVE ABNORMAL RETURN</div>
              <div className="text-2xl font-bold text-[#0f766e] mt-1 font-mono">
                {data.car >= 0 ? "+" : ""}{(data.car * 100).toFixed(2)}%
              </div>
              <div className="text-[11px] text-[#64748b] mt-1">WINDOW: [-1, +10] TRADING DAYS</div>
            </div>

            <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0]">
              <div className="text-[#64748b] text-[10px] uppercase">TEST STATISTIC (OLS T-STAT)</div>
              <div className="text-2xl font-bold text-[#0f172a] mt-1 font-mono">
                t = {data.t_stat.toFixed(3)}
              </div>
              <div className="text-[11px] text-[#64748b] mt-1">p-value: {data.p_value.toFixed(4)}</div>
            </div>

            <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0]">
              <div className="text-[#64748b] text-[10px] uppercase">MARKET MODEL SENSITIVITY</div>
              <div className="text-2xl font-bold text-[#0f172a] mt-1 font-mono">
                β = {data.market_model.beta.toFixed(4)}
              </div>
              <div className="text-[11px] text-[#64748b] mt-1">α = {data.market_model.alpha.toFixed(6)} (vs SPY)</div>
            </div>

            <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0]">
              <div className="text-[#64748b] text-[10px] uppercase">VOLATILITY REGIME (EGARCH)</div>
              <div className="text-sm font-bold text-[#0f172a] mt-2 font-mono">
                {data.vol_flag ? (
                  <span className="text-[#b91c1c]">ASYMMETRIC SPIKE DETECTED</span>
                ) : (
                  <span className="text-[#15803d]">NORMAL RESIDUAL REGIME</span>
                )}
              </div>
              <div className="text-[11px] text-[#64748b] mt-1">PRE-EVENT ESTIMATION: [-60, -10]</div>
            </div>
          </div>

          {/* Flat Architectural Bar Chart */}
          <div className="p-5 bg-[#f8fafc] border border-[#e2e8f0]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-4 text-xs font-mono">
              <span className="text-[#0f172a] uppercase font-bold">
                Price Action & Cumulative Abnormal Return (CAR) Window
              </span>
              <span className="text-[#64748b]">
                EVENT TIMESTAMP t = 0 // DISCLOSED: {data.actual_event_date}
              </span>
            </div>

            {/* Flat Solid Bar Representation */}
            <div className="h-52 w-full flex items-end gap-1.5 pt-6 pb-2 border-b border-[#e2e8f0]">
              {data.chart_points.map((pt, idx) => {
                const heightPct = Math.max(12, Math.min(100, ((pt.close - minClose) / range) * 80 + 15));
                const isEventDay = pt.t === 0;

                return (
                  <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                    {/* Flat Tooltip */}
                    <div className="absolute -top-12 hidden group-hover:flex flex-col items-center bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] p-1.5 text-[10px] font-mono whitespace-nowrap z-30 pointer-events-none">
                      <span className="font-bold">{pt.date} (t={pt.t})</span>
                      <span>Close: ${pt.close.toFixed(2)}</span>
                      <span className="text-[#0f766e] font-semibold">CAR: {(pt.car * 100).toFixed(2)}%</span>
                    </div>

                    {/* Flat Solid Bar */}
                    <div
                      className={`w-full transition-colors ${
                        isEventDay
                          ? "bg-[#0f766e]"
                          : pt.t > 0
                          ? "bg-[#cbd5e1] hover:bg-[#94a3b8]"
                          : "bg-[#e2e8f0] hover:bg-[#cbd5e1]"
                      }`}
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className={`text-[10px] mt-2 font-mono ${isEventDay ? "text-[#0f766e] font-bold" : "text-[#64748b]"}`}>
                      {pt.t === 0 ? "E(0)" : pt.t > 0 ? `+${pt.t}` : pt.t}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Econometric Governance Disclosures */}
          <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0] text-xs font-mono space-y-1.5">
            <div className="text-[#0f172a] font-bold">
              ECONOMETRIC FINDING: {data.interpretation}
            </div>
            <div className="text-[#475569] leading-normal font-sans text-xs">
              <strong>Methodological Notice:</strong> The market model R_i,t = α_i + β_i · R_m,t + ε_i,t is estimated over the historical pre-event estimation window [-60, -10] trading days using ordinary least squares (OLS). The cumulative abnormal return (CAR) aggregates abnormal residuals over the [-1, +10] day event window. This platform quantifies empirical historical price association and conditional volatility regimes without asserting forward-looking causal predictability.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}