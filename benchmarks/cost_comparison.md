# 💰 Cost Comparison: Autonomic AI vs Cloud Agents

_This document provides a concrete financial comparison between using
Autonomic AI with local lightweight models vs. relying on cloud LLM APIs._

---

## Assumptions

| Parameter | Value | Source |
|---|---|---|
| Tasks per developer per day | 50 coding tasks | Typical IDE-agent usage |
| Working days per month | 22 | Standard calendar |
| Avg input tokens per task (monolith) | 50,000 | Full context injection (2000 items × ~25 tok/item) |
| Avg input tokens per task (Autonomic) | 500 | agent-brain routes only relevant context |
| Avg output tokens per task | 500 | Model response |
| GPT-4 Turbo input price | $10.00 / 1M tokens | OpenAI pricing (Jun 2026) |
| GPT-4 Turbo output price | $30.00 / 1M tokens | OpenAI pricing (Jun 2026) |
| Claude 3.5 Sonnet input price | $3.00 / 1M tokens | Anthropic pricing (Jun 2026) |
| Claude 3.5 Sonnet output price | $15.00 / 1M tokens | Anthropic pricing (Jun 2026) |
| Electricity cost (Apple Silicon) | ~$0.12/kWh | US average |
| M2 Pro power draw (inference) | ~15W | Apple Silicon efficiency |

---

## Monthly Cost: Cloud API (Monolith Approach)

### GPT-4 Turbo

| Component | Calculation | Monthly Cost |
|---|---|---|
| Input tokens | 50 tasks × 22 days × 50,000 tokens = 55M tokens | $550.00 |
| Output tokens | 50 tasks × 22 days × 500 tokens = 550K tokens | $16.50 |
| **Total** | | **$566.50** |

### Claude 3.5 Sonnet

| Component | Calculation | Monthly Cost |
|---|---|---|
| Input tokens | 55M tokens × $3.00/1M | $165.00 |
| Output tokens | 550K tokens × $15.00/1M | $8.25 |
| **Total** | | **$173.25** |

> [!WARNING]
> The monolith approach injects the full context window (50K+ tokens) every turn.
> This is the actual cost profile of agents like AutoGPT, Devin, and similar tools
> that push entire conversation histories into every API call.

---

## Monthly Cost: Cloud API (with Autonomic Brain Routing)

Using agent-brain's precision routing, input tokens drop from ~50K to ~500 per task.

### GPT-4 Turbo + Autonomic Brain

| Component | Calculation | Monthly Cost |
|---|---|---|
| Input tokens | 50 tasks × 22 days × 500 tokens = 550K tokens | $5.50 |
| Output tokens | 50 tasks × 22 days × 500 tokens = 550K tokens | $16.50 |
| **Total** | | **$22.00** |
| **Savings vs monolith** | | **$544.50/mo (96%)** |

### Claude 3.5 Sonnet + Autonomic Brain

| Component | Calculation | Monthly Cost |
|---|---|---|
| Input tokens | 550K × $3.00/1M | $1.65 |
| Output tokens | 550K × $15.00/1M | $8.25 |
| **Total** | | **$9.90** |
| **Savings vs monolith** | | **$163.35/mo (94%)** |

---

## Monthly Cost: 100% Local (Autonomic + Ollama)

Running a local model on Apple Silicon with Autonomic routing:

| Component | Calculation | Monthly Cost |
|---|---|---|
| LLM API cost | $0 (local inference via Ollama) | **$0.00** |
| Electricity | 15W × 8h/day × 22 days × $0.12/kWh | **$0.32** |
| Embedding model | Local ONNX, included in brain | **$0.00** |
| NATS broker | <1W overhead | **$0.00** |
| **Total** | | **$0.32** |

### Hardware Requirement (one-time)

| Hardware | Model Size | Estimated Price |
|---|---|---|
| MacBook Air M2 (16GB) | Up to 7B quantized | ~$1,199 |
| MacBook Pro M2 Pro (32GB) | Up to 14B quantized | ~$1,999 |
| Mac Studio M2 Ultra (192GB) | Up to 70B | ~$3,999 |
| Linux + RTX 4090 (24GB VRAM) | Up to 14B quantized | ~$2,500 |

> [!NOTE]
> Most developers already have a capable laptop. The incremental cost of
> running Autonomic locally is effectively **$0.32/month** in electricity.

---

## Summary: Cost Comparison Table

| Setup | Monthly Cost | Annual Cost | Savings vs GPT-4 Monolith |
|---|---|---|---|
| GPT-4 Turbo (monolith) | $566.50 | **$6,798** | — |
| Claude 3.5 Sonnet (monolith) | $173.25 | $2,079 | 69% |
| GPT-4 Turbo + Autonomic routing | $22.00 | $264 | **96%** |
| Claude 3.5 Sonnet + Autonomic routing | $9.90 | $119 | **98%** |
| **Local Qwen 7B + Autonomic (full stack)** | **$0.32** | **$3.84** | **99.9%** |

---

## Per-Team Cost Impact

For a team of 5 developers:

| Setup | Annual Cost (5 devs) |
|---|---|
| GPT-4 Turbo (monolith) | **$33,990** |
| Local Autonomic | **$19.20** |
| **Savings** | **$33,971/year** |

---

## The Trade-off: Quality vs Cost

The critical question: does a local 7B model produce _acceptable_ results?

With Autonomic AI's agent-brain routing:
- The model receives **precisely relevant context** (~500 tokens) instead of a noisy 50K blob
- **Project conventions are enforced** via `must_apply` constraints (immutability, error handling, type annotations)
- **Hook enforcement** ensures the model follows the routed skills, not its own defaults
- **Spine DAG workflows** provide deterministic control flow, so the model only needs to handle individual nodes, not the entire task orchestration

Run the comparison yourself:
```bash
python benchmarks/model_comparison.py --models qwen2.5-coder:1.5b,qwen2.5-coder:7b
cat benchmarks/results_model_comparison.md
```

---

## Data Sovereignty Bonus

Beyond cost, local inference provides:

| Benefit | Description |
|---|---|
| **No data exfiltration** | Proprietary code never leaves the machine |
| **No vendor lock-in** | Switch models anytime via Ollama |
| **No API outages** | Local inference is always available |
| **No rate limits** | Run as many tasks as your hardware allows |
| **Compliance** | Meets GDPR, HIPAA, SOC2 data residency requirements |

---

> **Bottom line:** Autonomic AI's precision routing makes cloud APIs 25x cheaper
> (96% savings). Going fully local makes it essentially free ($0.32/month)
> while keeping all code sovereign. The question is not cost — it's whether
> local models can match cloud quality. That's what the
> [model comparison benchmark](./model_comparison.py) proves.
