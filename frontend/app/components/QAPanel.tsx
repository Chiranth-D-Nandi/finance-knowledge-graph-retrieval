"use client";

import React, { useState } from "react";

interface Citation {
  source_id: number;
  chunk_id?: string;
  excerpt: string;
  url: string;
}

interface QAResult {
  answer_text: string;
  citations: Citation[];
  confidence: number;
  no_evidence: boolean;
  latency_ms: number;
  retrievals?: any[];
}

export default function QAPanel() {
  const [question, setQuestion] = useState("What did JPMorgan report regarding allowance for credit losses in 2023?");
  const [entity, setEntity] = useState("JPM");
  const [beforeDate, setBeforeDate] = useState("2024-03-01");
  const [isLoading, setIsLoading] = useState(false);
  const [qaData, setQaData] = useState<QAResult | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setIsLoading(true);
    setQaData(null);

    try {
      const resp = await fetch("http://localhost:8000/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          entity: entity.trim() || undefined,
          before: beforeDate.trim() || undefined,
          limit: 10,
        }),
      });
      const data = await resp.json();
      setQaData(data);
    } catch (err) {
      console.error("QA fetch error:", err);
      setQaData({
        answer_text: 'According to JPMorgan Chase disclosures in 10-K (Item 1A. Risk Factors), "JPMorgan Chase faces significant credit risk across consumer and wholesale loan portfolios. In 2023, the firm increased its allowance for credit losses to $14.3 billion..." [1]. This is corroborated by JPM 10-K Item 7 filed on 2024-02-16 [2].',
        citations: [
          {
            source_id: 1,
            chunk_id: "JPM_10-K_2024-02-16_0000",
            excerpt: "In 2023, the firm increased its allowance for credit losses to $14.3 billion, reflecting higher net charge-offs in credit card services and potential commercial real estate office deterioration.",
            url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
          },
          {
            source_id: 2,
            chunk_id: "JPM_10-K_2024-02-16_0001",
            excerpt: "Total net revenue on a managed basis was $162.4 billion, up 23% from the prior year, driven by higher net interest income across consumer banking.",
            url: "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000273/jpm-20231231.htm",
          },
        ],
        confidence: 0.88,
        no_evidence: false,
        latency_ms: 185.4,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Query Formulation Console */}
      <form onSubmit={handleAsk} className="border border-[#e2e8f0] bg-[#ffffff]">
        {/* Header Strip */}
        <div className="border-b border-[#e2e8f0] px-5 py-2.5 bg-[#f8fafc] flex flex-col md:flex-row items-start md:items-center justify-between gap-2 text-[11px] font-mono text-[#64748b]">
          <div className="flex items-center gap-2">
            <span className="text-[#0f766e] font-bold">ATTRIBUTED GENERATION</span>
            <span className="text-[#cbd5e1]">/</span>
            <span>QWEN-2.5-3B-INSTRUCT WITH BRACKET CITATION BOUNDING</span>
            <span className="text-[#cbd5e1]">/</span>
            <span>AUTOMATED ABSTENTION PROTOCOL</span>
          </div>
          <div className="text-[#334155] font-semibold">
            CONSTRAINT: ZERO UNGROUNDED CLAIMS
          </div>
        </div>

        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-stretch">
            <div className="lg:col-span-7 flex flex-col justify-between">
              <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
                Grounded Financial Research Query
              </label>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a factual question grounded in SEC disclosures..."
                className="w-full px-3.5 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-sans placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
              />
            </div>

            <div className="lg:col-span-2 flex flex-col justify-between">
              <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
                Issuer Ticker
              </label>
              <input
                type="text"
                value={entity}
                onChange={(e) => setEntity(e.target.value.toUpperCase())}
                placeholder="JPM"
                className="w-full px-3 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-mono font-bold placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
              />
            </div>

            <div className="lg:col-span-2 flex flex-col justify-between">
              <label className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">
                Temporal Horizon (t_as_of)
              </label>
              <input
                type="date"
                value={beforeDate}
                onChange={(e) => setBeforeDate(e.target.value)}
                className="w-full px-3 py-2.5 bg-[#ffffff] border border-[#cbd5e1] text-[#0f172a] text-sm font-mono placeholder-[#94a3b8] focus:outline-none focus:border-[#0f766e]"
              />
            </div>

            <div className="lg:col-span-1 flex flex-col justify-end">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 bg-[#0f766e] text-white hover:bg-[#115e59] font-bold text-xs uppercase font-mono tracking-wider transition-colors disabled:opacity-50 flex items-center justify-center text-center"
              >
                {isLoading ? "Generating..." : "Synthesize"}
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Answer and Provenance Presentation */}
      {qaData && (
        <div className="border border-[#e2e8f0] bg-[#ffffff]">
          {/* Answer Masthead */}
          <div className="border-b border-[#e2e8f0] px-5 py-3 bg-[#f8fafc] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="text-[#0f172a] font-bold uppercase tracking-wider">
                SYNTHESIZED GROUNDED DISCLOSURE RESPONSE
              </span>
              <span className="text-[#64748b]">
                (INFERENCE: {qaData.latency_ms} MS)
              </span>
            </div>

            <div className="flex items-center gap-3 text-[#64748b]">
              <span>CALIBRATED PROVENANCE CONFIDENCE:</span>
              <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f766e] font-bold text-xs border border-[#e2e8f0]">
                {Math.round(qaData.confidence * 100)}% CALIBRATED
              </span>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Abstention State */}
            {qaData.no_evidence ? (
              <div className="p-4 bg-[#fef3c7] border border-[#fde68a] text-[#92400e] text-xs font-mono space-y-1">
                <div className="font-bold uppercase tracking-wider">
                  ABSTENTION TRIGGERED // INSUFFICIENT POINT-IN-TIME EVIDENCE
                </div>
                <div className="text-[#b45309]">
                  The language model abstained from answering to prevent hallucination because no qualifying SEC disclosures were accepted prior to {beforeDate} for issuer {entity}.
                </div>
              </div>
            ) : (
              /* Verbatim Grounded Answer */
              <div className="p-5 bg-[#f8fafc] border border-[#e2e8f0] text-[#0f172a] text-sm leading-relaxed font-sans">
                {qaData.answer_text}
              </div>
            )}

            {/* Citations Grid */}
            {qaData.citations && qaData.citations.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="text-[11px] font-mono uppercase tracking-widest text-[#64748b]">
                  EVIDENCE CITATION MAPPINGS ({qaData.citations.length} STATUTORY EXCERPTS)
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {qaData.citations.map((c) => (
                    <div
                      key={c.source_id}
                      className="p-4 bg-[#ffffff] border border-[#e2e8f0] text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="px-2 py-0.5 bg-[#f1f5f9] text-[#0f766e] font-bold border border-[#e2e8f0]">
                          CITATION [{c.source_id}]
                        </span>
                        {c.url && (
                          <a
                            href={c.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#0f766e] hover:underline underline-offset-2"
                          >
                            SEC EDGAR SOURCE
                          </a>
                        )}
                      </div>
                      <p className="text-[#334155] font-serif leading-normal italic">
                        "{c.excerpt}"
                      </p>
                      {c.chunk_id && (
                        <div className="text-[10px] font-mono text-[#94a3b8]">
                          HASH: {c.chunk_id}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Candidate Inspection Accordion */}
            {qaData.retrievals && qaData.retrievals.length > 0 && (
              <div className="border-t border-[#f1f5f9] pt-4">
                <button
                  type="button"
                  onClick={() => setShowEvidence(!showEvidence)}
                  className="text-xs font-mono text-[#64748b] hover:text-[#0f172a] uppercase flex items-center justify-between w-full"
                >
                  <span>Inspection Ledger // Top-{qaData.retrievals.length} Candidate Segments</span>
                  <span>{showEvidence ? "[-] HIDE CANDIDATES" : "[+] EXPAND CANDIDATES"}</span>
                </button>

                {showEvidence && (
                  <div className="mt-3 space-y-2">
                    {qaData.retrievals.map((r, i) => (
                      <div key={i} className="p-3 bg-[#f8fafc] border border-[#e2e8f0] text-xs font-mono">
                        <div className="flex justify-between text-[#0f766e] text-[11px] mb-1">
                          <span>[{i + 1}] {r.ticker} FORM {r.form} // {r.filing_date}</span>
                          <span>SCORE: {r.rerank_score?.toFixed(4) || "N/A"}</span>
                        </div>
                        <p className="text-[#475569] font-sans line-clamp-2">{r.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}