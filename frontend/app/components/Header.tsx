"use client";

import React from "react";

interface HeaderProps {
  entityCount?: number;
  lastIngest?: string;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Header({
  entityCount = 50,
  lastIngest = "2026-11-16 19:00 UTC",
  activeTab,
  setActiveTab,
}: HeaderProps) {
  const tabs = [
    { id: "search", num: "01", label: "Hybrid Search", desc: "Dual BM25 + Dense RRF" },
    { id: "qa", num: "02", label: "Grounded QA", desc: "Attributed SEC Inference" },
    { id: "timeline", num: "03", label: "Temporal Graph", desc: "Chronological Disclosures" },
    { id: "impact", num: "04", label: "Market Impact", desc: "Econometric OLS CAR" },
    { id: "benchmarks", num: "05", label: "Audit Ledger", desc: "Ablation & Leakage Suite" },
  ];

  return (
    <header className="border-b border-[#e2e8f0] bg-[#ffffff] text-[#0f172a] sticky top-0 z-40">
      {/* Top Utility and Classification Bar */}
      <div className="border-b border-[#f1f5f9] px-6 py-2 bg-[#f8fafc] flex flex-col md:flex-row items-start md:items-center justify-between gap-2 text-[11px] font-mono uppercase tracking-wider text-[#64748b]">
        <div className="flex items-center gap-3">
          <span className="text-[#0f766e] font-semibold">TERMINAL ACCESS</span>
          <span className="text-[#cbd5e1]">/</span>
          <span>INSTITUTIONAL WORKSPACE SPECIFICATION</span>
          <span className="text-[#cbd5e1]">/</span>
          <span>SEC FAIR-ACCESS COMPLIANT (8 REQ/S)</span>
        </div>
        <div className="flex items-center gap-4 text-[#475569]">
          <span>INDEXED: <strong className="text-[#0f172a] font-mono">{entityCount} EQUITIES</strong></span>
          <span className="text-[#cbd5e1]">|</span>
          <span>HARDWARE: <strong className="text-[#0f172a] font-mono">RTX 4060 CUDA FP16</strong></span>
          <span className="text-[#cbd5e1]">|</span>
          <span>PIT LEAKAGE: <strong className="text-[#0f766e] font-mono">0.00% (20/20)</strong></span>
          <span className="text-[#cbd5e1]">|</span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="text-[#64748b] hover:text-[#0f172a] underline decoration-[#cbd5e1] underline-offset-2"
          >
            OPENAPI SPEC
          </a>
        </div>
      </div>

      {/* Main Masthead Banner */}
      <div className="px-6 py-4 flex flex-col lg:flex-row lg:items-end justify-between gap-4 bg-[#ffffff]">
        <div>
          <div className="flex items-baseline gap-3">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-[#0f172a] font-sans uppercase">
              Financial Knowledge Graph & Temporal Retrieval
            </h1>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 bg-[#f1f5f9] text-[#475569] border border-[#e2e8f0]">
              v1.0 Production
            </span>
          </div>
          <p className="text-xs text-[#64748b] font-mono mt-1 max-w-2xl leading-normal">
            Entity-resolved disclosure indexing over SEC EDGAR 10-K/Q, Yahoo Finance OHLCV, and FRED macro time-series.
            Candidate-level point-in-time filtering strictly enforced.
          </p>
        </div>

        {/* Temporal Calibration Note */}
        <div className="hidden xl:block text-right text-[11px] font-mono text-[#64748b]">
          <div>ACCEPTANCE STAMP KEYED TO SEC EDGAR RECEIPT</div>
          <div className="text-[#0f172a]">LAST INGEST CADENCE: {lastIngest}</div>
        </div>
      </div>

      {/* Navigation Tab Bar */}
      <div className="px-6 flex items-stretch overflow-x-auto border-t border-[#e2e8f0] bg-[#f8fafc]">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-3 text-left border-r border-[#e2e8f0] transition-colors relative flex flex-col justify-center min-w-[170px] ${
                isActive
                  ? "bg-[#ffffff] text-[#0f172a]"
                  : "bg-transparent text-[#64748b] hover:text-[#0f172a] hover:bg-[#f1f5f9]"
              }`}
            >
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#0f766e]" />
              )}
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-[#94a3b8]">
                <span>{tab.num}</span>
                <span>//</span>
                <span className={isActive ? "text-[#0f766e] font-semibold" : ""}>{tab.label}</span>
              </div>
              <div className="text-xs font-semibold tracking-tight mt-0.5">
                {tab.desc}
              </div>
            </button>
          );
        })}
      </div>
    </header>
  );
}