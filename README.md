# APEX CLI

APEX is a general-purpose, local-first autonomous agent system. It provides an intent-driven interface for software development, system administration, data analysis, web research, document synthesis, and general task execution.

APEX runs locally on Windows, Linux, and macOS, with native hardware telemetry and acceleration support for local GPU endpoints (Ollama, vLLM, NVIDIA NIM) alongside cloud model providers.

---

## Purpose

The goal of APEX is to provide a single interface for executing multi-domain digital tasks. Rather than relying on separate applications or manual context switching, APEX accepts high-level objectives, creates execution plans, executes actions in isolated sandboxes, and verifies results.

---

## Core Features

- **Pre-Execution Governance & Risk Policy**: Evaluates tool action risk (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) before execution. Arbitrary shell (`run_command`) and Python (`execute_python_script`) executions require explicit approval. Unattended modes (headless, dashboard, daemon, mesh) default-deny actions requiring approval.
- **Workspace Containment**: Enforces workspace boundary containment across filesystem, document ingestion, and data tools, rejecting absolute paths outside the workspace, `..` path traversals, and symlink escapes.
- **Explicit Workspace Management**: Supports `apex init` and global `--workspace` parameters. Prohibits autonomous execution when the workspace is the user's home directory (`$HOME`).
- **Safe Checkpoint & Rollback**: Persists checkpoint metadata (`.apex/checkpoints.json`) and requires explicit confirmation before rollback, displaying affected files without implicitly deleting untracked files.
- **Document Ingestion**: Parses and indexes PDF (`.pdf`), PowerPoint (`.pptx`), Word (`.docx`), and text files into the Cognitive Knowledge Graph (`apex read`).
- **Local & Hybrid Model Routing**: Endpoint normalization supporting both `http://host:8000` and `http://host:8000/v1` without duplicate `/v1/v1` paths. Validates model IDs against `/v1/models` and `/api/tags`, surfacing actionable errors.
- **Tree Search Execution (LATS)**: Uses Monte Carlo Tree Search (MCTS) with Upper Confidence Bound for Trees (UCT) scoring to generate and evaluate candidate execution paths.
- **Anticipatory Intelligence & Daily Digest**: Offers proactive recommendations (`apex suggest`) and 2-minute daily activity summaries (`apex digest`).
- **4-Tier Memory & Knowledge Graph**: Combines Working, Episodic, Semantic AST, and Procedural memory with a local SQLite Cognitive Knowledge Graph (`.apex/cognitive_graph.db`).
- **Multi-Model Adversarial Debate**: Cross-examines proposed solutions between models before executing code (`apex debate`).
- **24/7 Background Ambient Mesh**: Optional background service for monitoring workspace health with strict governance safeguards (`apex mesh`).
- **Local Web Interface**: Includes a loopback-bound web dashboard (`apex serve`) hosted at `http://127.0.0.1:7860`. Non-loopback binding requires authentication token enforcement.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Git 2.30+
- (Optional) Local GPU inference server (Ollama, vLLM, or NVIDIA NIM)

### Clone & Virtual Environment Setup

```bash
# 1. Clone the repository
git clone https://github.com/evanunrue-art/apex-agent.git
cd apex-agent

# 2. Create and activate a virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install APEX package and all dependencies
pip install -e .
```

### Optional Extras Installation

```bash
# Install specific optional dependency sets
pip install -e ".[data]"     # Data analysis (pandas)
pip install -e ".[web]"      # Web dashboard (starlette, uvicorn)
pip install -e ".[docs]"     # Document ingestion (pypdf, python-docx)
pip install -e ".[all]"      # All optional extras
```

---

## Workspace Initialization

Before executing tasks, initialize a dedicated workspace directory:

```bash
# Initialize current directory as an APEX workspace
apex init

# Or initialize a specific workspace directory
apex init --workspace ./my-project
```

*Note: Autonomous execution is prohibited in the user's home directory (`$HOME`).*

---

## Command Reference

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `apex init` | Initializes an APEX workspace configuration | `apex init --workspace ./my-project` |
| `apex read` | Parses PDF, PPTX, DOCX, or text file into Knowledge Graph | `apex read "paper.pdf"` |
| `apex serve` | Launches local web dashboard (bound to `127.0.0.1:7860`) | `apex serve` |
| `apex ask` | Plain-language question answering | `apex ask "Explain how HTTP/3 works"` |
| `apex suggest` | Displays proactive anticipatory recommendations | `apex suggest` |
| `apex digest` | Generates a 2-minute daily productivity summary | `apex digest` |
| `apex run` | Executes a multi-step task | `apex run "Create a FastAPI service with unit tests"` |
| `apex intent` | Processes high-level human intent through governance policy | `apex intent "Inspect system logs and patch memory leaks"` |
| `apex research` | Runs multi-query web search synthesis | `apex research "Local LLM inference optimization"` |
| `apex analyze` | Computes dataset summary statistics | `apex analyze "data.csv"` |
| `apex sysadmin` | Displays system hardware telemetry and running processes | `apex sysadmin` |
| `apex debate` | Subjects a solution proposal to multi-model audit | `apex debate "Refactor auth pipeline" "Use plain JWT"` |
| `apex graph` | Queries the local Cognitive Knowledge Graph | `apex graph "database"` |
| `apex policy` | Displays risk classifications for tools | `apex policy` |
| `apex memory` | Displays status of all 4 memory tiers | `apex memory` |
| `apex skills` | Lists synthesized procedural skills | `apex skills` |
| `apex dgx` | Checks local GPU status and local model endpoints | `apex dgx` |
| `apex mesh` | Starts ambient background mesh service | `apex mesh` |
| `apex daemon` | Runs continuous background watchdog test suite | `apex daemon` |
| `apex undo` | Rolls back workspace to previous shadow snapshot | `apex undo --target 1 --force` |

---

## Configuration

Configuration parameters are stored in `.apex/config.yaml`:

```yaml
primary_provider: hybrid          # Options: hybrid, local_dgx, ollama, vllm, nim, openai, anthropic, deepseek
local_dgx_endpoint: http://localhost:11434
local_model: qwen2.5-coder:latest
cloud_model: gpt-4o

lats_max_depth: 5
lats_max_branches: 3
lats_exploration_weight: 1.414
max_context_tokens: 128000

enable_git_checkpoints: true
enable_skill_synthesis: true
strict_governance: true
```

---

## Testing

Run the automated test suite to verify governance enforcement, path containment, endpoint normalization, document ingestion, and CLI interfaces:

```bash
python -m unittest discover -s tests
```

---

## License

MIT License.
