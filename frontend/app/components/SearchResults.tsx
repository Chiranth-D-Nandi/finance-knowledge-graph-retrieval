"use client";

import React, { useState } from "react";

interface ChunkResult {
  rank: number;
  chunk_id: string;
  ticker: string;
  form: string;
  filing_date: string;
  section: string;
  text: string;
  source_url: string;
  rerank_score: number;
  rrf_score: number;
  sentiment?: {
    label: string;
    positive: number;
    negative: number;
    neutral: number;
  };
}

interface SearchResultsProps {
  results: ChunkResult[];
  query: string;
  entityLinked?: any;
  latencyMs?: number;
}

export default function SearchResults({ results, query, entityLinked, latencyMs }: SearchResultsProps) {
  const [selectedChunk, setSelectedChunk] = useState<ChunkResult | null>(null);

  if (!results || results.length === 0) {
    return (
      <div className="border border-[#e2e8f0] bg-[#ffffff] p-10 text-center">
        <div className="text-xs font-mono uppercase tracking-widest text-[#64748b] mb-1">
          RETRIEVAL PARTITION EMPTY
        </div>
        <p className="text-sm font-sans text-[#0f172a]">
          Zero disclosure segments satisfy the joint BM25 + dense vector threshold under the configured point-in-time boundary.
        </p>
        <p className="text-xs font-mono text-[#64748b] mt-2">
          Adjust temporal cutoff t_as_of or relax entity symbology constraint.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Ledger Status Bar */}
      <div className="border border-[#e2e8f0] bg-[#f8fafc] px-4 py-2.5 flex flex-wrap items-center justify-between text-[11px] font-mono text-[#64748b]">
        <div className="flex items-center gap-3">
          <span>
            RETRIEVED: <strong className="text-[#0f172a]">{results.length} EVIDENCE CHUNKS</strong>
          </span>
          <span className="text-[#cbd5e1]">/</span>
          {entityLinked && (
            <span>
              RESOLVED ISSUER: <strong className="text-[#0f766e]">{entityLinked.ticker}</strong> ({entityLinked.name || "Canonical SEC CIK"})
            </span>
          )}
        </div>
        {latencyMs !== undefined && (
          <div className="text-[#64748b]">
            END-TO-END RETRIEVAL LATENCY: <strong className="text-[#0f172a]">{latencyMs} MS</strong>
          </div>
        )}
      </div>

      {/* Asymmetric Results Stream */}
      <div className="space-y-3">
        {results.map((chunk) => {
          const sent = chunk.sentiment;
          const isNeg = sent?.label === "negative";
          const isPos = sent?.label === "positive";

          return (
            <div
              key={chunk.chunk_id}
              onClick={() => setSelectedChunk(chunk)}
              className="border border-[#e2e8f0] bg-[#ffffff] hover:bg-[#f8fafc] p-5 cursor-pointer transition-colors relative"
            >
              {/* Top Meta Strip */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-[#f1f5f9] text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f172a] font-bold text-[11px] border border-[#e2e8f0]">
                    RANK #{chunk.rank}
                  </span>
                  <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f766e] font-bold text-[11px] border border-[#e2e8f0]">
                    {chunk.ticker}
                  </span>
                  <span className="px-2 py-0.5 bg-[#f8fafc] text-[#334155] text-[11px] border border-[#e2e8f0]">
                    FORM {chunk.form}
                  </span>
                  <span className="text-[#64748b] text-[11px]">
                    DISCLOSED: {chunk.filing_date}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[11px]">
                  {sent && (
                    <span className="font-mono text-[10px] uppercase text-[#64748b]">
                      POLARITY: <strong className={isNeg ? "text-[#b91c1c]" : isPos ? "text-[#15803d]" : "text-[#334155]"}>
                        {sent.label} ({Math.round(Math.max(sent.positive, sent.negative, sent.neutral) * 100)}%)
                      </strong>
                    </span>
                  )}
                  <span className="text-[#cbd5e1]">|</span>
                  <span className="font-mono text-[#0f766e] font-bold">
                    CROSS-ENCODER: {chunk.rerank_score.toFixed(4)}
                  </span>
                </div>
              </div>

              {/* SEC Section Taxonomy */}
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#64748b] mb-2">
                SECTION TAXONOMY: <span className="text-[#0f172a] font-semibold">{chunk.section}</span>
              </div>

              {/* Disclosed Text Body */}
              <p className="text-sm text-[#334155] font-sans leading-relaxed line-clamp-3 mb-4">
                {chunk.text}
              </p>

              {/* Audit Ledger Line */}
              <div className="pt-2 border-t border-[#f1f5f9] flex flex-col sm:flex-row sm:items-center justify-between text-[10px] font-mono text-[#64748b] gap-1">
                <span className="truncate max-w-lg text-[#94a3b8]">
                  CHUNK HASH: {chunk.chunk_id}
                </span>
                <span className="text-[#0f766e] underline decoration-[#cbd5e1] underline-offset-4 font-semibold uppercase">
                  View Full Audit Excerpt // SEC EDGAR Source
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal for Full Chunk Audit */}
      {selectedChunk && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4">
          <div className="bg-[#ffffff] border border-[#cbd5e1] max-w-3xl w-full max-h-[85vh] flex flex-col">
            {/* Modal Masthead */}
            <div className="px-6 py-3.5 border-b border-[#e2e8f0] bg-[#f8fafc] flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f172a] font-bold border border-[#e2e8f0]">
                  {selectedChunk.ticker}
                </span>
                <span className="text-[#0f172a] font-semibold">
                  FORM {selectedChunk.form} // {selectedChunk.section}
                </span>
                <span className="text-[#64748b]">
                  ({selectedChunk.filing_date})
                </span>
              </div>
              <button
                onClick={() => setSelectedChunk(null)}
                className="text-xs font-mono text-[#64748b] hover:text-[#0f172a] px-2 py-1 border border-[#cbd5e1] bg-[#ffffff]"
              >
                [CLOSE ESC]
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-sm">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-[#64748b] mb-1.5">
                  Verbatim Regulatory Text (Trafilatura Ingestion)
                </div>
                <div className="p-4 bg-[#f8fafc] border border-[#e2e8f0] text-[#0f172a] text-sm leading-relaxed font-serif">
                  {selectedChunk.text}
                </div>
              </div>

              <div>
                <div className="text-[10px] font-mono uppercase tracking-widest text-[#64748b] mb-1.5">
                  Cryptographic Provenance & Scoring Record
                </div>
                <pre className="p-4 bg-[#f8fafc] border border-[#e2e8f0] text-xs font-mono text-[#0f766e] overflow-x-auto">
                  {JSON.stringify(
                    {
                      chunk_id: selectedChunk.chunk_id,
                      ticker: selectedChunk.ticker,
                      form: selectedChunk.form,
                      filing_date: selectedChunk.filing_date,
                      section: selectedChunk.section,
                      cross_encoder_score: selectedChunk.rerank_score,
                      rrf_score: selectedChunk.rrf_score,
                      source_url: selectedChunk.source_url,
                      sentiment_distribution: selectedChunk.sentiment,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            </div>

            {/* Modal Action Bar */}
            <div className="px-6 py-3 border-t border-[#e2e8f0] bg-[#f8fafc] flex items-center justify-between text-xs font-mono">
              <span className="text-[#64748b]">POINT-IN-TIME GUARANTEE: COMPLIANT</span>
              <a
                href={selectedChunk.source_url}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-[#0f766e] hover:bg-[#115e59] text-white font-bold uppercase transition-colors"
              >
                View Official SEC Filing
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}