# System Environment Specification

**Generated Date:** 2026-11-16  
**System Host:** Windows 11 (build architecture: AMD64 / 64-bit)  
**Target Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)  
**Execution Context:** the platform: Entity-Resolved Temporal Knowledge Graph with Hybrid Financial Retrieval, Grounded QA, and Explainable Market Impact Analytics  

---

## 1. Hardware Specification

| Component | Detected Specification | the platform Budget Limit | Status |
|---|---|---|---|
| **GPU** | NVIDIA GeForce RTX 4060 Laptop GPU | 8188 MiB VRAM (~8.0 GB) | PASSED |
| **Driver Version** | 592.82 | CUDA 13.1 driver capability | PASSED |
| **Active VRAM Usage (Idle)** | 174 MiB / 8188 MiB | Peak operational target ≤ 6.8 GB | PASSED |
| **Primary Disk** | Drive `C:\` | 190.3 GB Free (832.6 GB Used) | PASSED |
| **CPU Architecture** | x86_64 / Windows AMD64 | Multi-core Windows workstation | PASSED |

---

## 2. Runtimes & Toolchains

| Runtime | Detected Version | Usage in the platform |
|---|---|---|
| **Python (Primary Target)** | Python 3.11.9 (`py -3.11`) | Core ML/Data pipeline, PyTorch, sentence-transformers, FastAPI |
| **Python (System Default)** | Python 3.13.5 | Secondary system interpreter |
| **Node.js** | v22.18.0 | Next.js 14 App Router frontend runtime |
| **npm** | 10.9.3 | Node package manager |
| **Shell** | PowerShell 5.1 / Core on Windows | Execution environment |
| **Source Control** | Git | Initialized in workspace root |

---

## 3. GPU Memory Allocation Budget (RTX 4060 8GB)

```
Total Dedicated VRAM: 8,188 MiB (~8.0 GB)
Idle Baseline Usage: ~174 MiB

Pipeline Phase Allocation (Sequential peak containment):
┌────────────────────────────┬─────────────┬───────────┬──────────────────────────────────────┐
│ Model / Component          │ Params      │ VRAM fp16 │ Execution Mode                       │
├────────────────────────────┼─────────────┼───────────┼──────────────────────────────────────┤
│ BGE-base-en-v1.5           │ 110M        │ ~1.4 GB   │ Batch 32 fp16 (offline/query encode) │
│ ms-marco-MiniLM-L6-v2      │ 80M         │ ~0.95 GB  │ Batch 32 fp16 (rerank top-50 → 10)   │
│ ProsusAI/finbert (Offline) │ 110M        │ ~0.25 GB  │ ONNX/PyTorch CPU or fp16 GPU offline │
│ Qwen2.5-3B-Instruct (BnB)  │ 3B          │ ~3.5 GB   │ 4-bit NF4 quantized + KV cache       │
│ PatchTST (Optional)        │ 10M         │ ~0.05 GB  │ Offline / standalone train           │
├────────────────────────────┼─────────────┼───────────┼──────────────────────────────────────┤
│ Sequential Max Peak        │             │ ~6.8 GB   │ Headroom: > 1.2 GB safety margin     │
└────────────────────────────┴─────────────┴───────────┴──────────────────────────────────────┘
```

*Note: Models are executed sequentially (encode pool -> rerank pool -> generative QA). Reranker activations are freed before local generative LLM decoding.*

---

## 4. Directory State Inspection Before Modification

Existing files in workspace root (`c:\Users\chiranth\Downloads\getmehired`):
- `Institutional Financial Infrastructure_ANTIGRAVITY_MASTER_IMPLEMENTATION_PROMPT.md` (49,343 bytes) ,  Preserved unchanged
- `WINNING_PROJECT_DEEP_DIVE.md` (46,720 bytes) ,  Preserved unchanged
