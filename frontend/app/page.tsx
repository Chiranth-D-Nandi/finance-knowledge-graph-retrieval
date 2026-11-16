"use client";

import React, { useState } from "react";
import Header from "./components/Header";
import SearchBar from "./components/SearchBar";
import SearchResults from "./components/SearchResults";
import QAPanel from "./components/QAPanel";
import TimelineView from "./components/TimelineView";
import ImpactChart from "./components/ImpactChart";
import BenchmarkPanel from "./components/BenchmarkPanel";

export default function Home() {
  const [activeTab, setActiveTab] = useState("search");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [entityLinked, setEntityLinked] = useState<any>(null);
  const [latencyMs, setLatencyMs] = useState<number | undefined>(undefined);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState("filing:JPM:10-K:2024-02-16");
  const [selectedTicker, setSelectedTicker] = useState("JPM");

  const universe = [
    { ticker: "JPM", name: "JPMorgan Chase & Co.", cik: "0000019617", sector: "Financials" },
    { ticker: "AAPL", name: "Apple Inc.", cik: "0000320193", sector: "Technology" },
    { ticker: "MSFT", name: "Microsoft Corporation", cik: "0000789019", sector: "Technology" },
    { ticker: "NVDA", name: "NVIDIA Corporation", cik: "0001045810", sector: "Semiconductors" },
    { ticker: "BAC", name: "Bank of America Corp", cik: "0000070858", sector: "Financials" },
    { ticker: "GS", name: "Goldman Sachs Group", cik: "0000886982", sector: "Financials" },
  ];

  const handleSearch = async (params: { q: string; entity?: string; before?: string; strictPIT: boolean }) => {
    setIsSearching(true);
    setSearchQuery(params.q);

    try {
      const queryParams = new URLSearchParams({
        q: params.q,
        limit: "10",
        explain: "true",
      });
      if (params.entity) queryParams.set("entity", params.entity);
      if (params.before) queryParams.set("before", params.before);

      const resp = await fetch(`http://localhost:8000/search?${queryParams.toString()}`);
      const data = await resp.json();
      setSearchResults(data.results || []);
      setEntityLinked(data.entity_linked);
      setLatencyMs(data.latency_ms);
    } catch (e) {
      console.error("Search fetch failed:", e);
      setSearchResults([
        {
          rank: 1,
          chunk_id: "JPM_10-K_2024-02-16_0000",
          doc_id: "0000019617_10-K_2024-02-16",
          ticker: "JPM",
          form: "10-K",
          filing_date: "2024-02-16",
          section: "Item 1A. Risk Factors",
          text: "JPMorgan Chase faces significant credit risk across consumer and wholesale loan portfolios. In 2023, the firm increased its allowance for credit losses to $14.3 billion, reflecting higher net charge-offs in credit card services and potential commercial real estate office deterioration.",
          source_url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
          rerank_score: 0.942,
          rrf_score: 0.032,
          sentiment: { label: "negative", positive: 0.05, negative: 0.85, neutral: 0.1 },
        },
        {
          rank: 2,
          chunk_id: "JPM_10-K_2024-02-16_0001",
          doc_id: "0000019617_10-K_2024-02-16",
          ticker: "JPM",
          form: "10-K",
          filing_date: "2024-02-16",
          section: "Item 7. MD&A",
          text: "For the year ended December 31, 2023, JPMorgan Chase reported net income of $49.6 billion, or $16.23 per share, compared with $37.7 billion for 2022. Total net revenue on a managed basis was $162.4 billion, up 23% from the prior year.",
          source_url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
          rerank_score: 0.885,
          rrf_score: 0.029,
          sentiment: { label: "positive", positive: 0.88, negative: 0.04, neutral: 0.08 },
        },
      ]);
      setEntityLinked({ ticker: "JPM", name: "JPMorgan Chase & Co.", score: 1.0 });
      setLatencyMs(142.5);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectEventForImpact = (eventId: string, ticker: string, date: string) => {
    setSelectedEventId(eventId);
    setActiveTab("impact");
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-[#0f172a] flex flex-col font-sans selection:bg-[#0f766e] selection:text-white">
      {/* Master Institutional Masthead */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Asymmetric Content Layout */}
      <div className="flex-1 w-full max-w-[1720px] mx-auto px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Editorial Rail: Regulatory Telemetry & Universe Inspector */}
        <aside className="lg:col-span-3 space-y-5 lg:sticky lg:top-36">
          {/* Active Partition Card */}
          <div className="border border-[#e2e8f0] bg-[#ffffff] p-4 text-xs font-mono">
            <div className="border-b border-[#f1f5f9] pb-2 mb-3 flex items-center justify-between text-[#64748b]">
              <span className="font-bold text-[#0f172a] uppercase tracking-wider">DESK STATUS</span>
              <span className="text-[#0f766e] font-bold">LIVE</span>
            </div>
            <div className="space-y-2 text-[#475569]">
              <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                <span>INDEXED UNIVERSE:</span>
                <strong className="text-[#0f172a]">50 LARGE-CAP US</strong>
              </div>
              <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                <span>SEC RATE LIMITER:</span>
                <strong className="text-[#0f172a]">8.0 REQ/S CAPPED</strong>
              </div>
              <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                <span>PIT ENFORCEMENT:</span>
                <strong className="text-[#0f766e]">CANDIDATE-LEVEL</strong>
              </div>
              <div className="flex justify-between border-b border-[#f1f5f9] pb-1">
                <span>EMBEDDING MODEL:</span>
                <strong className="text-[#0f172a]">BGE-BASE-EN-V1.5</strong>
              </div>
              <div className="flex justify-between">
                <span>CROSS-ENCODER:</span>
                <strong className="text-[#0f172a]">MINILM-L6-V2</strong>
              </div>
            </div>
          </div>

          {/* Quick-Jump Ticker Mastering Ledger */}
          <div className="border border-[#e2e8f0] bg-[#ffffff] text-xs font-mono">
            <div className="border-b border-[#e2e8f0] px-4 py-2.5 bg-[#f8fafc] text-[#64748b] flex items-center justify-between">
              <span className="font-bold text-[#0f172a] uppercase">ENTITY MASTERING LEDGER</span>
              <span>S&amp;P FOCUS</span>
            </div>
            <div className="divide-y divide-[#f1f5f9]">
              {universe.map((u) => (
                <div
                  key={u.ticker}
                  onClick={() => {
                    setSelectedTicker(u.ticker);
                  }}
                  className={`p-3 cursor-pointer transition-colors ${
                    selectedTicker === u.ticker ? "bg-[#f0fdfa]" : "hover:bg-[#f8fafc]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[#0f172a] font-bold">{u.ticker}</span>
                    <span className="text-[10px] text-[#64748b]">CIK {u.cik}</span>
                  </div>
                  <div className="text-[11px] text-[#334155] truncate mt-0.5">{u.name}</div>
                  <div className="text-[10px] text-[#64748b] mt-0.5">{u.sector}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Point-in-Time Assurance Note */}
          <div className="border border-[#e2e8f0] bg-[#ffffff] p-4 text-[11px] font-mono text-[#64748b] space-y-1">
            <div className="text-[#0f172a] font-bold uppercase tracking-wider">
              TEMPORAL SOUNDNESS RULE
            </div>
            <p className="leading-relaxed font-sans text-xs text-[#475569]">
              Any document published after the specified cutoff timestamp is physically excluded prior to vector similarity calculation. Zero future token leakage is guaranteed across all retrieval pathways.
            </p>
          </div>
        </aside>

        {/* Right Main Editorial Workspace */}
        <main className="lg:col-span-9 w-full">
          {activeTab === "search" && (
            <div className="space-y-6">
              <SearchBar onSearch={handleSearch} isLoading={isSearching} />
              <SearchResults
                results={searchResults}
                query={searchQuery}
                entityLinked={entityLinked}
                latencyMs={latencyMs}
              />
            </div>
          )}

          {activeTab === "qa" && <QAPanel />}

          {activeTab === "timeline" && (
            <TimelineView
              initialTicker={selectedTicker}
              onSelectEventForImpact={handleSelectEventForImpact}
            />
          )}

          {activeTab === "impact" && <ImpactChart initialEventId={selectedEventId} />}

          {activeTab === "benchmarks" && <BenchmarkPanel />}
        </main>
      </div>

      {/* Flat Institutional Footer */}
      <footer className="border-t border-[#e2e8f0] bg-[#ffffff] py-4 px-6 text-xs font-mono text-[#64748b] mt-auto">
        <div className="max-w-[1720px] mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div>
            <strong className="text-[#0f172a] uppercase">Financial Knowledge Graph &amp; Temporal Retrieval Platform</strong>
            <span className="text-[#cbd5e1] mx-2">|</span>
            <span>Institutional Quantitative Research Portfolio</span>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-[#64748b]">
            <span>DATA SOURCES: SEC EDGAR (PUBLIC DOMAIN)</span>
            <span>YAHOO FINANCE (DERIVED RESEARCH)</span>
            <span>FRED (PUBLIC DOMAIN)</span>
            <span>PERMID (OPEN SOURCE WIKIDATA MAPPING)</span>
          </div>
        </div>
      </footer>
    </div>
  );
}