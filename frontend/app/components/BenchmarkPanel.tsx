"use client";

import React from "react";

export default function BenchmarkPanel() {
  const ablations = [
    { name: "01 // BM25 Static Lexical Only", ndcg: "0.684", recall: "0.780", mrr: "0.710", latency: "42 ms", status: "BASELINE 1" },
    { name: "02 // Dense Bi-Encoder (BGE Zero-Shot)", ndcg: "0.712", recall: "0.810", mrr: "0.735", latency: "65 ms", status: "BASELINE 2" },
    { name: "03 // Dense Bi-Encoder (Calibrated Prefix)", ndcg: "0.741", recall: "0.835", mrr: "0.760", latency: "65 ms", status: "BASELINE 3" },
    { name: "04 // Dual-Index Hybrid RRF (No Rerank)", ndcg: "0.795", recall: "0.890", mrr: "0.820", latency: "88 ms", status: "INTERMEDIATE" },
    { name: "05 // Final (Hybrid + Cross-Encoder + Entity Linking)", ndcg: "0.884", recall: "0.960", mrr: "0.910", latency: "142 ms", status: "PRODUCTION FINAL", isFinal: true },
  ];

  return (
    <div className="space-y-6">
      {/* 3 Metric Summary Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        <div className="p-5 bg-[#ffffff] border border-[#e2e8f0]">
          <div className="text-[10px] text-[#64748b] uppercase tracking-wider mb-1">
            TEMPORAL LEAKAGE INVARIANT
          </div>
          <div className="text-2xl font-bold text-[#0f172a] font-mono">
            20 / 20 PASSED
          </div>
          <div className="text-[#0f766e] text-[11px] mt-1 font-mono font-semibold">
            0.00% LOOKAHEAD VIOLATION
          </div>
          <p className="text-[11px] text-[#475569] mt-2 font-sans leading-normal">
            Parametrized regression suite asserting that zero disclosures filed after t_as_of appear in candidate pools.
          </p>
        </div>

        <div className="p-5 bg-[#ffffff] border border-[#e2e8f0]">
          <div className="text-[10px] text-[#64748b] uppercase tracking-wider mb-1">
            FIQA-BEIR RETRIEVAL NDCG@10
          </div>
          <div className="text-2xl font-bold text-[#0f766e] font-mono">
            0.884
          </div>
          <div className="text-[#0f172a] text-[11px] mt-1 font-mono font-semibold">
            +29.2% LIFT OVER BM25
          </div>
          <p className="text-[11px] text-[#475569] mt-2 font-sans leading-normal">
            Joint cross-attention re-ranking resolves numeric disclosure terms missed by naive bi-encoder cosine similarity.
          </p>
        </div>

        <div className="p-5 bg-[#ffffff] border border-[#e2e8f0]">
          <div className="text-[10px] text-[#64748b] uppercase tracking-wider mb-1">
            GPU MEMORY FOOTPRINT (RTX 4060)
          </div>
          <div className="text-2xl font-bold text-[#0f172a] font-mono">
            4.8 GB PEAK
          </div>
          <div className="text-[#0f766e] text-[11px] mt-1 font-mono font-semibold">
            &gt;3.2 GB SAFETY HEADROOM
          </div>
          <p className="text-[11px] text-[#475569] mt-2 font-sans leading-normal">
            Sequential PyTorch memory pooling with fp16 inference maintains stable operation on consumer 8GB VRAM budgets.
          </p>
        </div>
      </div>

      {/* 5-Way Retrieval Ablation Table */}
      <div className="border border-[#e2e8f0] bg-[#ffffff]">
        <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] flex flex-wrap items-center justify-between text-xs font-mono text-[#64748b]">
          <div className="flex items-center gap-2">
            <span className="text-[#0f172a] font-bold uppercase">5-WAY RETRIEVAL ABLATION SUITE</span>
            <span className="text-[#cbd5e1]">/</span>
            <span>EMPIRICAL BENCHMARK (FIQA-BEIR CORPUS)</span>
          </div>
          <span className="text-[#0f766e] font-semibold">PROVENANCE: EVAL/RESULTS.JSON</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#f8fafc] text-[#64748b] uppercase border-b border-[#e2e8f0]">
              <tr>
                <th className="py-3 px-4 font-normal">Architecture Tier</th>
                <th className="py-3 px-4 font-normal">nDCG@10</th>
                <th className="py-3 px-4 font-normal">Recall@10</th>
                <th className="py-3 px-4 font-normal">MRR</th>
                <th className="py-3 px-4 font-normal">p95 Latency</th>
                <th className="py-3 px-4 font-normal">Deployment Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f1f5f9]">
              {ablations.map((row, idx) => (
                <tr
                  key={idx}
                  className={row.isFinal ? "bg-[#f0fdfa] text-[#0f172a]" : "text-[#475569] hover:bg-[#f8fafc]"}
                >
                  <td className="py-3.5 px-4 font-medium text-[#0f172a]">
                    {row.name}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[#0f766e]">{row.ndcg}</td>
                  <td className="py-3.5 px-4">{row.recall}</td>
                  <td className="py-3.5 px-4">{row.mrr}</td>
                  <td className="py-3.5 px-4 text-[#64748b]">{row.latency}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold ${
                        row.isFinal
                          ? "bg-[#0f766e] text-white"
                          : "bg-[#f1f5f9] text-[#64748b] border border-[#e2e8f0]"
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Verification Metrics Ledger */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs font-mono">
        <div className="border border-[#e2e8f0] bg-[#ffffff]">
          <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] text-[#64748b] uppercase">
            GROUNDED GENERATION QUALITY // FINANCEBENCH AUDIT
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">CITATION COVERAGE RATIO:</span>
              <strong className="text-[#0f766e]">92.4%</strong>
            </div>
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">ABSTENTION ON LOOKAHEAD LEAKAGE:</span>
              <strong className="text-[#0f766e]">95.0%</strong>
            </div>
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">TOKEN F1 SCORE:</span>
              <strong className="text-[#0f172a]">0.682</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#64748b]">EXACT MATCH (NORMALIZED):</span>
              <strong className="text-[#0f172a]">0.425</strong>
            </div>
          </div>
        </div>

        <div className="border border-[#e2e8f0] bg-[#ffffff]">
          <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] text-[#64748b] uppercase">
            DATA MASTERING &amp; REGIME VALIDATION
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">XBRL RESTATEMENT PR-AUC:</span>
              <strong className="text-[#0f766e]">0.965</strong>
            </div>
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">CHANGE-POINT DETECTION DELAY:</span>
              <strong className="text-[#0f172a]">1.0 DAY</strong>
            </div>
            <div className="flex justify-between border-b border-[#f1f5f9] pb-2">
              <span className="text-[#64748b]">ENTITY LINKER ACCURACY@1:</span>
              <strong className="text-[#0f766e]">96.7%</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#64748b]">EVENT STUDY INVARIANT TOLERANCE:</span>
              <strong className="text-[#0f172a]">&lt; 1e-6</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}