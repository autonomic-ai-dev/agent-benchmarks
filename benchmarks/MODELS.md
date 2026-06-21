# Recommended Models for Autonomic AI Benchmarking

The following models are the recommended set for proving the
"lightweight model accuracy boost" claim. They span the full
parameter range from 1.3B to 14B.

## Tier 1: Primary (always benchmark these)

| Model | Params | Ollama ID | Notes |
|---|---|---|---|
| Qwen 2.5 Coder 1.5B | 1.5B | `qwen2.5-coder:1.5b` | Smallest viable coder |
| Qwen 2.5 Coder 3B | 3B | `qwen2.5-coder:3b` | Sweet spot for Apple Silicon |
| Qwen 2.5 Coder 7B | 7B | `qwen2.5-coder:7b` | Default benchmark model |
| DeepSeek Coder 1.3B | 1.3B | `deepseek-coder:1.3b` | Smallest DeepSeek |
| DeepSeek Coder 6.7B | 6.7B | `deepseek-coder:6.7b` | Strong coder baseline |

## Tier 2: Extended (include when possible)

| Model | Params | Ollama ID | Notes |
|---|---|---|---|
| CodeLlama 7B | 7B | `codellama:7b` | Meta's coding model |
| StarCoder2 7B | 7B | `starcoder2:7b` | BigCode project |
| Gemma 2 2B | 2B | `gemma2:2b` | Google's lightweight |
| Gemma 2 9B | 9B | `gemma2:9b` | Google's mid-range |
| DeepSeek Coder V2 Lite | 16B | `deepseek-coder-v2:16b` | MoE architecture |

## Quick-Start Commands

```bash
# Pull Tier 1 models
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder:1.3b
ollama pull deepseek-coder:6.7b

# Run Tier 1 comparison
python benchmarks/model_comparison.py \
  --models qwen2.5-coder:1.5b,qwen2.5-coder:3b,qwen2.5-coder:7b,deepseek-coder:1.3b,deepseek-coder:6.7b

# Pull Tier 2 models
ollama pull codellama:7b
ollama pull starcoder2:7b
ollama pull gemma2:2b
ollama pull gemma2:9b

# Run full comparison
python benchmarks/model_comparison.py \
  --models qwen2.5-coder:1.5b,qwen2.5-coder:3b,qwen2.5-coder:7b,deepseek-coder:1.3b,deepseek-coder:6.7b,codellama:7b,starcoder2:7b,gemma2:2b,gemma2:9b
```

## Model Selection Rationale

- **Qwen 2.5 Coder**: Currently the highest-performing coding model
  family at small parameter counts. The 1.5B → 3B → 7B range lets us
  measure how brain context scales with model size.

- **DeepSeek Coder**: Strong alternative with different training data
  distribution. The 1.3B model is the smallest viable coder on the market.

- **CodeLlama**: Meta's specialist model; widely deployed and well-benchmarked.

- **StarCoder2**: BigCode's open-source coder; different architecture
  and training approach.

- **Gemma 2**: Google's efficient architecture; good test of whether
  brain context helps non-specialist models with coding tasks.

- **DeepSeek Coder V2**: Mixture-of-Experts architecture; interesting
  to see if brain context interacts differently with MoE routing.
