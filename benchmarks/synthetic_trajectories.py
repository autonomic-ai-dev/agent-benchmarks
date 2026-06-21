"""Synthetic trajectory generator for bootstrapping LoRA training data.

A fresh Autonomic install has zero trajectories. This generator creates
realistic training samples from common coding patterns so that the LoRA
pipeline can be exercised immediately.

The generated trajectories simulate agent-brain route_task → agent-spine
workflow → outcome sequences that would naturally accumulate during
development.

Usage:
    python synthetic_trajectories.py --count 500 --output train.jsonl
    python synthetic_trajectories.py --count 1000 --output train.jsonl --seed 42
    python synthetic_trajectories.py --count 200 --output train.jsonl --validate

Produces JSONL compatible with agent-muscle validate --data.
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Domain knowledge: realistic coding tasks and conventions
# ---------------------------------------------------------------------------

TASK_TEMPLATES: list[dict] = [
    {
        "category": "error_handling",
        "tasks": [
            "Add comprehensive error handling to the database connection function",
            "Handle timeout errors in the HTTP client with retry logic",
            "Add input validation to the API endpoint handler",
            "Replace unwrap() calls with proper Result propagation in Rust",
            "Add try-except blocks for file I/O operations",
        ],
        "conventions": [
            "Use explicit try/except blocks with specific exception types",
            "Log errors with structured context before re-raising",
            "Never silently swallow exceptions",
            "Validate inputs at system boundaries using schemas",
        ],
        "expected_patterns": ["try", "except", "raise", "logging", "ValueError"],
    },
    {
        "category": "immutability",
        "tasks": [
            "Refactor the order processing to use immutable data patterns",
            "Replace in-place list mutations with comprehensions",
            "Convert mutable class to frozen dataclass",
            "Use spread operators instead of direct object mutation",
            "Return new arrays instead of modifying the input",
        ],
        "conventions": [
            "Always create new objects; never mutate existing ones in place",
            "Return updated copies of arrays/objects rather than modifying fields",
            "Use frozen dataclasses for data models",
            "Prefer list comprehensions over append loops",
        ],
        "expected_patterns": ["frozen=True", "copy", "new", "comprehension", "spread"],
    },
    {
        "category": "type_safety",
        "tasks": [
            "Add type annotations to all function parameters and return types",
            "Replace Any with proper union types",
            "Add Zod schema validation to the Express endpoint",
            "Convert JavaScript to TypeScript with strict types",
            "Add type guards for discriminated unions",
        ],
        "conventions": [
            "Add explicit type annotations on all public APIs",
            "Use unknown instead of any for untrusted inputs",
            "Define component props with named interfaces",
            "Use Zod schemas for boundary validation",
        ],
        "expected_patterns": ["-> ", ": str", ": int", "Optional", "Union"],
    },
    {
        "category": "testing",
        "tasks": [
            "Write pytest unit tests following the AAA pattern",
            "Add edge case tests for the discount calculator",
            "Write integration tests for the database layer",
            "Add test coverage for error paths",
            "Create mock fixtures for external API calls",
        ],
        "conventions": [
            "Follow AAA (Arrange-Act-Assert) pattern",
            "Target minimum 80% test coverage",
            "Use pytest.raises for error assertions",
            "Verify test isolation with fresh fixtures",
        ],
        "expected_patterns": ["def test_", "assert", "pytest", "mock", "fixture"],
    },
    {
        "category": "security",
        "tasks": [
            "Fix the SQL injection vulnerability in the search function",
            "Sanitize HTML inputs to prevent XSS",
            "Replace hardcoded API keys with environment variables",
            "Add rate limiting to the authentication endpoint",
            "Implement parameterized queries for database access",
        ],
        "conventions": [
            "Never hardcode secrets in source code",
            "Use parameterized queries or ORMs to prevent SQL injection",
            "Sanitize all HTML inputs",
            "Verify authentication and authorization on all endpoints",
        ],
        "expected_patterns": ["parameterized", "os.environ", "sanitize", "rate_limit"],
    },
    {
        "category": "performance",
        "tasks": [
            "Optimize the N+1 query problem with a JOIN",
            "Add caching to the frequently-called lookup function",
            "Replace synchronous file reads with async I/O",
            "Batch database inserts instead of inserting one-by-one",
            "Add connection pooling to the database client",
        ],
        "conventions": [
            "Prefer batch operations over loops with individual calls",
            "Use connection pooling for database connections",
            "Cache expensive computations with LRU or TTL caches",
            "Profile before optimizing — measure first",
        ],
        "expected_patterns": ["JOIN", "batch", "cache", "pool", "async"],
    },
    {
        "category": "refactoring",
        "tasks": [
            "Extract the repeated validation logic into a shared utility",
            "Split the 500-line handler into focused modules",
            "Replace the god object with dependency injection",
            "Convert callback-based code to async/await",
            "Apply the adapter pattern to the payment provider",
        ],
        "conventions": [
            "Keep files under 400 lines",
            "Prefer many small focused files over few large ones",
            "Avoid deep nesting — max 4 levels, prefer early returns",
            "Extract repeated logic into shared utilities (DRY)",
        ],
        "expected_patterns": ["def ", "class ", "import", "return", "if not"],
    },
    {
        "category": "concurrency",
        "tasks": [
            "Fix the race condition in the request counter",
            "Add a mutex to protect shared state",
            "Convert the thread pool to use structured concurrency",
            "Implement a producer-consumer queue with backpressure",
            "Add graceful shutdown handling for background workers",
        ],
        "conventions": [
            "Use structured concurrency patterns",
            "Protect shared mutable state with locks or actors",
            "Handle cancellation and timeouts explicitly",
            "Prefer message passing over shared memory",
        ],
        "expected_patterns": ["lock", "mutex", "async", "await", "semaphore"],
    },
]

CODE_SNIPPETS: dict[str, list[str]] = {
    "python": [
        "def fetch_user(user_id: int) -> dict:\n    db = get_connection()\n    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()\n    return dict(row)",
        "def process_orders(orders: list[dict]) -> list[dict]:\n    for order in orders:\n        order['total'] = order['quantity'] * order['price']\n    return orders",
        "def search_users(name: str) -> list:\n    query = f\"SELECT * FROM users WHERE name LIKE '%{name}%'\"\n    return db.execute(query).fetchall()",
        "import requests\ndef get_weather(city: str):\n    response = requests.get(f'https://api.weather.com/v1/{city}')\n    return response.json()",
        "def calculate_discount(price, discount):\n    return price * (1 - discount / 100)",
    ],
    "typescript": [
        "async function fetchData(url: string) {\n  const response = await fetch(url);\n  return response.json();\n}",
        "let counter = 0;\nasync function handle(req: Request) {\n  counter++;\n  const result = await process(req);\n  counter--;\n  return result;\n}",
        "app.post('/api/users', async (req, res) => {\n  const { name, email } = req.body;\n  const user = await db.users.create({ name, email });\n  res.json(user);\n});",
    ],
    "rust": [
        "fn read_config(path: &str) -> Config {\n    let content = fs::read_to_string(path).unwrap();\n    let config: Config = serde_json::from_str(&content).unwrap();\n    config\n}",
        "fn process_items(items: &mut Vec<Item>) {\n    for item in items.iter_mut() {\n        item.status = Status::Processed;\n    }\n}",
    ],
}

OUTCOMES: list[str] = ["success", "failure", "escalated", "skipped"]
OUTCOME_WEIGHTS: list[float] = [0.7, 0.15, 0.1, 0.05]


# ---------------------------------------------------------------------------
# Trajectory generation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrajectoryEntry:
    """A single training trajectory entry."""
    instruction: str
    input_code: str
    output_conventions: str
    language: str
    category: str
    outcome: str
    route_confidence: float
    routed_skills: list[str]
    routed_rules: list[str]
    execution_id: str
    timestamp_ms: int


def generate_trajectory(rng: random.Random, seq: int) -> TrajectoryEntry:
    """Generate a single synthetic trajectory."""
    template = rng.choice(TASK_TEMPLATES)
    task = rng.choice(template["tasks"])
    category = template["category"]

    # Pick a language and code snippet
    lang = rng.choice(["python", "python", "python", "typescript", "rust"])
    snippets = CODE_SNIPPETS.get(lang, CODE_SNIPPETS["python"])
    code = rng.choice(snippets)

    # Select conventions to include (2-3 per trajectory)
    num_conventions = rng.randint(2, min(3, len(template["conventions"])))
    conventions = rng.sample(template["conventions"], num_conventions)
    conventions_text = "\n".join(f"- {c}" for c in conventions)

    # Generate outcome
    outcome = rng.choices(OUTCOMES, weights=OUTCOME_WEIGHTS, k=1)[0]
    confidence = round(rng.uniform(0.6, 0.99), 2) if outcome == "success" else round(rng.uniform(0.3, 0.7), 2)

    # Generate skills/rules
    routed_skills = [f"skill-{category}-{i}" for i in range(rng.randint(1, 3))]
    routed_rules = [f"rule-{category}" for _ in range(rng.randint(1, 2))]

    # Execution ID
    raw = f"{seq}-{task}-{code[:30]}"
    exec_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    # Timestamp (spread over the last 30 days)
    now_ms = int(time.time() * 1000)
    offset = rng.randint(0, 30 * 24 * 60 * 60 * 1000)
    ts = now_ms - offset

    return TrajectoryEntry(
        instruction=task,
        input_code=code,
        output_conventions=conventions_text,
        language=lang,
        category=category,
        outcome=outcome,
        route_confidence=confidence,
        routed_skills=routed_skills,
        routed_rules=routed_rules,
        execution_id=exec_id,
        timestamp_ms=ts,
    )


def generate_trajectories(count: int, seed: int | None = None) -> list[TrajectoryEntry]:
    """Generate N synthetic trajectories."""
    rng = random.Random(seed)
    return [generate_trajectory(rng, i) for i in range(count)]


# ---------------------------------------------------------------------------
# JSONL output (compatible with agent-muscle validate --data)
# ---------------------------------------------------------------------------

def trajectory_to_jsonl(entry: TrajectoryEntry) -> dict:
    """Convert a trajectory to the training JSONL format expected by agent-muscle."""
    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are a coding assistant. Follow these project conventions:\n"
                    f"{entry.output_conventions}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{entry.instruction}\n\n"
                    f"```{entry.language}\n{entry.input_code}\n```"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    f"I'll apply the project conventions to improve this code. "
                    f"Key changes based on the routed context:\n"
                    f"{entry.output_conventions}\n\n"
                    f"[This is a synthetic training example for the {entry.category} category]"
                ),
            },
        ],
        "metadata": {
            "execution_id": entry.execution_id,
            "category": entry.category,
            "language": entry.language,
            "outcome": entry.outcome,
            "route_confidence": entry.route_confidence,
            "routed_skills": entry.routed_skills,
            "routed_rules": entry.routed_rules,
            "timestamp_ms": entry.timestamp_ms,
            "synthetic": True,
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic training trajectories for LoRA fine-tuning"
    )
    parser.add_argument("--count", type=int, default=500,
                        help="Number of trajectories to generate (default: 500)")
    parser.add_argument("--output", default="train.jsonl",
                        help="Output JSONL file path (default: train.jsonl)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--validate", action="store_true",
                        help="Validate output with agent-muscle after generation")
    parser.add_argument("--stats", action="store_true",
                        help="Print distribution statistics")
    args = parser.parse_args()

    print(f"Generating {args.count} synthetic trajectories...")
    trajectories = generate_trajectories(args.count, args.seed)

    # Write JSONL
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for t in trajectories:
            f.write(json.dumps(trajectory_to_jsonl(t)) + "\n")

    print(f"Written {args.count} entries to {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")

    # Stats
    if args.stats or True:  # always print stats
        from collections import Counter
        categories = Counter(t.category for t in trajectories)
        outcomes = Counter(t.outcome for t in trajectories)
        languages = Counter(t.language for t in trajectories)

        print(f"\n--- Distribution ---")
        print(f"Categories: {dict(categories)}")
        print(f"Outcomes:   {dict(outcomes)}")
        print(f"Languages:  {dict(languages)}")
        print(f"Avg confidence: {sum(t.route_confidence for t in trajectories) / len(trajectories):.2f}")

    # Validate
    if args.validate:
        print(f"\nValidating with agent-muscle...")
        result = subprocess.run(
            ["agent-muscle", "validate", "--data", str(output_path)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"✓ Validation passed")
        else:
            print(f"✗ Validation failed:")
            print(result.stderr[:500])


if __name__ == "__main__":
    main()
