"use client";

import React, { useState } from "react";

interface SearchBarProps {
  onSearch: (params: { q: string; entity?: string; before?: string; strictPIT: boolean }) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState("What did JPMorgan report regarding allowance for credit losses in 2023?");
  const [entity, setEntity] = useState("JPM");
  const [beforeDate, setBeforeDate] = useState("2024-03-01");
  const [strictPIT, setStrictPIT] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch({
      q: query.trim(),
      entity: entity.trim() || undefined,
      before: beforeDate.trim() || undefined,
      strictPIT,
    });
  };

  return (
    <div className="border border-[#e2e8f0] bg-[#ffffff] mb-8">
      {/* Context Banner */}
      <div className="border-b border-[#e2e8f0] px-5 py-2.5 bg-[#f8fafc] flex flex-col md:flex-row items-start md:items-center justify-between gap-2 text-[11px] font-mono text-[#64748b]">
        <div className="flex items-center gap-2">
          <span className="text-[#0f766e] font-bold">QUERY ENGINE</span>
          <span className="text-[#cbd5e1]">/</span>
          <span>HYBRID BM25 + BAAI/BGE-BASE-EN-V1.5 (RRF K=60)</span>
          <span className="text-[#cbd5e1]">/</span>
          <span>CROSS-ENCODER MINI-LM RE-RANKING</span>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 cursor-pointer text-[#334155]">
            <input
              type="checkbox"
              checked={strictPIT}
              onChange={(e) => setStrictPIT(e.target.checked)}
              className="accent-[#0f766e] rounded-none border border-[#cbd5e1] bg-[#ffffff]"
            />
            <span className="font-medium">STRICT PIT PARTITION ACTIVE</span>
          </label>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        {/* Asymmetric Inputs Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
          {/* Query Field */}
          <div className="lg:col-span-7 flex flex-col justify-between">
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
              Natural Language Disclosure Query // Specific Accounting or Regulatory Focus
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Allowance for credit losses in commercial real estate portfolios..."
              className="w-full px-3.5 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-sans placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
            />
          </div>

          {/* Canonical Ticker Filter */}
          <div className="lg:col-span-2 flex flex-col justify-between">
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
              Entity Ticker / CIK
            </label>
            <input
              type="text"
              value={entity}
              onChange={(e) => setEntity(e.target.value.toUpperCase())}
              placeholder="JPM"
              className="w-full px-3 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-mono font-bold placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
            />
          </div>

          {/* Point-in-Time Temporal Cutoff */}
          <div className="lg:col-span-2 flex flex-col justify-between">
            <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
              Temporal Cutoff (t_as_of)
            </label>
            <input
              type="date"
              value={beforeDate}
              onChange={(e) => setBeforeDate(e.target.value)}
              className="w-full px-3 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-mono placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
            />
          </div>

          {/* Execution Button */}
          <div className="lg:col-span-1 flex flex-col justify-end">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-[#0f766e] text-white hover:bg-[#115e59] font-bold text-xs uppercase font-mono tracking-wider transition-colors disabled:opacity-50 flex items-center justify-center text-center"
            >
              {isLoading ? "Running..." : "Execute"}
            </button>
          </div>
        </div>

        {/* Real Curated Financial Scenarios */}
        <div className="pt-3 border-t border-[#f1f5f9] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#64748b] gap-2">
          <div className="flex items-center gap-2">
            <span className="text-[#94a3b8]">CURATED DESK SCENARIOS:</span>
            <button
              type="button"
              onClick={() => {
                setQuery("What did JPMorgan report regarding allowance for credit losses in 2023?");
                setEntity("JPM");
                setBeforeDate("2024-03-01");
              }}
              className="px-2 py-1 bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#e2e8f0] transition-colors"
            >
              JPM: Credit Loss Provisioning (Item 1A)
            </button>
            <button
              type="button"
              onClick={() => {
                setQuery("Apple supplier concentration and single-source dependency disclosures in Asia");
                setEntity("AAPL");
                setBeforeDate("2023-12-01");
              }}
              className="px-2 py-1 bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#e2e8f0] transition-colors"
            >
              AAPL: Supply Chain Concentration
            </button>
            <button
              type="button"
              onClick={() => {
                setQuery("NVIDIA revenue recognition and gross margin expansion from Data Center Hopper architecture");
                setEntity("NVDA");
                setBeforeDate("2024-03-01");
              }}
              className="px-2 py-1 bg-[#f1f5f9] hover:bg-[#e2e8f0] text-[#334155] border border-[#e2e8f0] transition-colors"
            >
              NVDA: Data Center Gross Margins
            </button>
          </div>

          <div className="text-[#94a3b8]">
            DISCLOSURES PUBLISHED STRICTLY AFTER {beforeDate || "CUTOFF"} ARE MASKED
          </div>
        </div>
      </form>
    </div>
  );
}