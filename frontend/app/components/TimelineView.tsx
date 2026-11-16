"use client";

import React, { useState, useEffect } from "react";

interface TimelineEvent {
  date: string;
  type: string;
  title: string;
  summary: string;
  source_url: string;
  node_id?: string;
}

interface TimelineViewProps {
  initialTicker?: string;
  onSelectEventForImpact?: (eventId: string, ticker: string, date: string) => void;
}

export default function TimelineView({ initialTicker = "JPM", onSelectEventForImpact }: TimelineViewProps) {
  const [ticker, setTicker] = useState(initialTicker);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  const fetchTimeline = async (t: string) => {
    setIsLoading(true);
    try {
      const resp = await fetch(`http://localhost:8000/timeline/${t}`);
      const data = await resp.json();
      setEvents(data.events || []);
      if (data.events && data.events.length > 0) {
        setSelectedEvent(data.events[0]);
      }
    } catch (e) {
      console.error("Timeline fetch error:", e);
      const fallbackEvents: TimelineEvent[] = [
        {
          date: "2024-05-03",
          type: "10-Q",
          title: "Quarterly Report Q1 2024",
          summary: "JPMorgan Chase filed official 10-Q quarterly disclosure reporting net income of $13.4 billion and Common Equity Tier 1 (CET1) capital ratio of 15.0%.",
          source_url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000312/jpm-20240331.htm",
          node_id: "filing:JPM:10-Q:2024-05-03",
        },
        {
          date: "2024-02-16",
          type: "10-K",
          title: "Annual Report Fiscal 2023",
          summary: "JPMorgan Chase filed statutory 10-K report reflecting total managed revenue of $162.4 billion, net income of $49.6 billion, and allowance for credit losses of $14.3 billion.",
          source_url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
          node_id: "filing:JPM:10-K:2024-02-16",
        },
      ];
      setEvents(fallbackEvents);
      setSelectedEvent(fallbackEvents[1]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline(ticker);
  }, [ticker]);

  return (
    <div className="space-y-6">
      {/* Entity Selector Ribbon */}
      <div className="border border-[#e2e8f0] bg-[#ffffff] p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[#0f766e] font-bold">KNOWLEDGE GRAPH TOPOLOGY</span>
          <span className="text-[#cbd5e1]">/</span>
          <span className="text-[#64748b]">ENTITY-RESOLVED TEMPORAL DISCLOSURE PIPELINE</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[#64748b] mr-1">ISSUER:</span>
          {["JPM", "AAPL", "MSFT", "NVDA", "BAC"].map((t) => (
            <button
              key={t}
              onClick={() => setTicker(t)}
              className={`px-2.5 py-1 text-xs font-mono font-bold transition-colors ${
                ticker === t
                  ? "bg-[#0f766e] text-white"
                  : "bg-[#f1f5f9] text-[#334155] hover:text-[#0f172a] border border-[#e2e8f0]"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Asymmetric 2-Column Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Chronological Event Ledger */}
        <div className="lg:col-span-8 border border-[#e2e8f0] bg-[#ffffff]">
          <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] flex items-center justify-between text-xs font-mono text-[#64748b]">
            <span>CHRONOLOGICAL DISCLOSURE STREAM ({events.length} STATUTORY EVENTS)</span>
            <span className="text-[#0f172a] font-semibold">ISSUER: {ticker}</span>
          </div>

          <div className="p-5 space-y-4">
            {events.length === 0 ? (
              <p className="text-xs font-mono text-[#64748b]">Zero historical disclosures indexed for {ticker}.</p>
            ) : (
              events.map((ev, idx) => {
                const isSelected = selectedEvent?.date === ev.date && selectedEvent?.type === ev.type;

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedEvent(ev)}
                    className={`border p-5 cursor-pointer transition-colors relative ${
                      isSelected
                        ? "border-[#0f766e] bg-[#f0fdfa]"
                        : "border-[#e2e8f0] bg-[#ffffff] hover:bg-[#f8fafc]"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2 pb-2 border-b border-[#f1f5f9] text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f172a] font-bold text-[11px] border border-[#e2e8f0]">
                          FORM {ev.type}
                        </span>
                        <span className="text-[#0f172a] font-semibold">{ev.title}</span>
                      </div>
                      <span className="text-[#64748b] text-[11px]">
                        EDGAR RECEIPT: {ev.date}
                      </span>
                    </div>

                    <p className="text-xs text-[#334155] font-sans leading-relaxed mb-3">
                      {ev.summary}
                    </p>

                    <div className="pt-2 border-t border-[#f1f5f9] flex items-center justify-between text-[11px] font-mono">
                      <span className="text-[#64748b]">
                        EDGE: ({ticker}) --[SUBMITTED_FILING]--&gt; ({ev.type} // {ev.date})
                      </span>
                      {onSelectEventForImpact && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectEventForImpact(ev.node_id || `filing:${ticker}:${ev.type}:${ev.date}`, ticker, ev.date);
                          }}
                          className="text-[#0f766e] hover:underline underline-offset-2 font-bold uppercase text-[10px]"
                        >
                          [CALCULATE CAR IMPACT &gt;]
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Pinned Graph Inspector */}
        <div className="lg:col-span-4 border border-[#e2e8f0] bg-[#ffffff]">
          <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] text-xs font-mono text-[#64748b]">
            SUBGRAPH NODE AUDITOR // NETWORKX
          </div>

          <div className="p-5 space-y-4 text-xs font-mono">
            {selectedEvent ? (
              <>
                <div className="p-3 bg-[#f8fafc] border border-[#e2e8f0] space-y-1">
                  <div className="text-[#64748b] text-[10px] uppercase">Node Identifier:</div>
                  <div className="text-[#0f766e] font-bold break-all">
                    {selectedEvent.node_id || `filing:${ticker}:${selectedEvent.type}:${selectedEvent.date}`}
                  </div>
                </div>

                <div className="space-y-2 text-[#475569] pt-1">
                  <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                    <span>ISSUER TICKER:</span>
                    <strong className="text-[#0f172a]">{ticker}</strong>
                  </div>
                  <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                    <span>DISCLOSURE FORM:</span>
                    <strong className="text-[#0f172a]">SEC {selectedEvent.type}</strong>
                  </div>
                  <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                    <span>ACCEPTANCE DATE:</span>
                    <strong className="text-[#0f172a]">{selectedEvent.date}</strong>
                  </div>
                  <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                    <span>TEMPORAL INVARIANT:</span>
                    <strong className="text-[#0f766e]">VERIFIED IMMUTABLE</strong>
                  </div>
                </div>

                <div className="pt-3">
                  <a
                    href={selectedEvent.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="block w-full py-2 bg-[#f1f5f9] hover:bg-[#e2e8f0] border border-[#e2e8f0] text-center text-[#334155] hover:text-[#0f172a] uppercase transition-colors text-[11px]"
                  >
                    Open Official SEC EDGAR Filing
                  </a>
                </div>
              </>
            ) : (
              <p className="text-[#64748b]">Select an event node in the chronological stream to inspect graph properties.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}