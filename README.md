# ⚡ APEX CLI: Autonomous Tree-Search & Hybrid Cognitive Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Architecture: LATS + MCTS](https://img.shields.io/badge/Architecture-LATS%20%2B%20MCTS-magenta.svg)](#-key-architectural-breakthroughs)
[![Hardware Acceleration: NVIDIA DGX](https://img.shields.io/badge/Hardware-NVIDIA%20DGX%20Spark-green.svg)](#-nvidia-dgx--localcloud-hybrid-engine)

**APEX** is a next-generation autonomous CLI agentic assistant designed to deliver a paradigm shift in AI-assisted software engineering. Built to transcend linear ReAct frameworks (such as Claude Code, OpenHands, Hermes, and Aider), APEX unifies **Language Agent Tree Search (LATS)**, a **4-Tier Cognitive Memory System**, **Voyager Dynamic Skill Synthesis**, **NVIDIA DGX Hardware Acceleration**, and **Shadow-Git Instant Checkpointing**.

---

## 🚀 Key Architectural Breakthroughs

### 1. Language Agent Tree Search (LATS) & Parallel Speculative Trajectories
Unlike traditional ReAct loops that execute step-by-step linearly, APEX evaluates coding decisions using **Monte Carlo Tree Search (MCTS)**.
- Spawns parallel branch hypotheses for complex software engineering challenges.
- Evaluates environmental feedback (exit codes, linter errors, test suite results, AST diffs).
- Backpropagates trajectory quality using Upper Confidence Bound for Trees (UCT), dynamically pruning failed paths and selecting optimal branches.

### 2. Hierarchical 4-Tier Cognitive Memory Architecture
- **Working Memory**: Dynamic context window manager featuring adaptive token budgeting and active log compression ([context_budget.py](file:///c:/new/apex/core/context_budget.py)).
- **Episodic Memory**: Cross-session trajectory store indexing problem-solving history and developer preferences ([episodic.py](file:///c:/new/apex/memory/episodic.py)).
- **Semantic Memory**: AST code symbol graph indexer cataloging class definitions, functions, and file import maps in real time ([semantic.py](file:///c:/new/apex/memory/semantic.py)).
- **Procedural Memory (Voyager Skill Engine)**: Auto-synthesizes reusable Python/Bash tools during execution and stores them in `.apex/skills/` for future tasks ([procedural.py](file:///c:/new/apex/memory/procedural.py)).

### 3. NVIDIA DGX Local / Cloud Hybrid Engine
- Natively connects to local GPU inference servers (**vLLM**, **Ollama**, **NVIDIA NIM**) running on NVIDIA DGX Spark microservers (`http://localhost:11434` or `http://localhost:8000/v1`).
- **Smart Model Routing**: Routes high-throughput sub-tasks (file scanning, AST indexing, error log parsing) to local DGX GPUs while leveraging frontier cloud APIs (OpenAI, Anthropic, Gemini, DeepSeek) for strategic reasoning.
- Live hardware telemetry monitor tracking GPU VRAM usage and NVML stats directly in the CLI status bar.

### 4. Shadow-Git Checkpointing & Zero-Risk Undo
- Automatically creates lightweight shadow Git commit stashes before high-risk operations or multi-file edits.
- Enables 1-click zero-risk experimentation with full workspace rollback capabilities (`apex undo`).

### 5. Multi-Agent Swarm Framework
- **Architect Agent**: System design, DAG task breakdown, and blueprint planning.
- **Coder Agent**: Surgical code implementation and minimal-diff patch generation.
- **Auditor Agent**: Real-time static analysis, security auditing, and syntax checking.
- **Debugger Agent**: Automated stack trace parsing and targeted bug fixing.

---

## 📁 System Architecture & Directory Structure

```
c:/new/
├── pyproject.toml              # Build backend & CLI entrypoint specification
├── requirements.txt            # Package dependencies
├── README.md                   # Complete system documentation
├── apex/
│   ├── main.py                 # Typer CLI Command Interface
│   ├── config.py               # Hardware detection & configuration loader
│   ├── core/
│   │   ├── orchestrator.py    # Core Cognitive ReAct + LATS Tree Engine
│   │   ├── lats_tree.py        # Language Agent Tree Search & MCTS Evaluator
│   │   └── context_budget.py   # Context window optimizer & token budget manager
│   ├── memory/
│   │   ├── memory_manager.py   # Unified 4-Tier Memory Coordinator
│   │   ├── episodic.py         # Session trajectory memory
│   │   ├── semantic.py         # AST code graph indexer
│   │   └── procedural.py       # Voyager skill synthesizer
│   ├── providers/
│   │   ├── router.py           # Local DGX + Cloud Hybrid Router
│   │   ├── local_dgx.py        # vLLM / Ollama / NIM local GPU driver
│   │   └── cloud_llm.py        # Unified OpenAI / Anthropic / Gemini / DeepSeek API
│   ├── tools/
│   │   ├── registry.py         # Unified Tool Registry & Dispatcher
│   │   ├── terminal.py         # Async PTY & Subprocess runner
│   │   ├── filesystem.py       # Ripgrep search & AST diff patcher
│   │   ├── git_checkpoint.py   # Shadow Git stash & rollback engine
│   │   └── browser.py          # Visual headless browser tool
│   ├── agents/
│   │   ├── base.py             # Swarm Agent base class
│   │   └── __init__.py         # Architect, Coder, Auditor, Debugger Agents
│   └── ui/
│       ├── tui.py              # Textual / Rich split-screen dashboard
│       └── views.py            # Status bars, GPU gauges, and thought streams
└── tests/
    └── test_core.py            # Automated integration and unit test suite
```

---

## 📦 Installation & Setup

### Prerequisites
- **Python**: 3.10 or higher
- **Git**: 2.30+
- **NVIDIA GPU (Optional for Local DGX Acceleration)**: NVIDIA Drivers + Ollama or vLLM running on `localhost`.

### Quick Installation

```bash
# Clone or navigate to APEX workspace
cd c:\new

# Option A: Install as an editable package (Recommended)
pip install -e .

# Option B: Install via requirements file
pip install -r requirements.txt
```

---

## 🎮 Command-Line Interface (CLI) Reference

APEX provides intuitive commands for managing execution, inspecting hardware, querying memory, and rolling back changes:

| Command | Description | Example |
| :--- | :--- | :--- |
| `apex run` | Execute an autonomous software engineering task | `apex run "Create a FastAPI backend with unit tests"` |
| `apex dgx` | Inspect local NVIDIA DGX hardware & model endpoints | `apex dgx` |
| `apex memory` | Display status across all 4 memory tiers | `apex memory` |
| `apex skills` | List dynamically synthesized Voyager skills | `apex skills` |
| `apex undo` | Rollback workspace state to previous shadow snapshot | `apex undo` |

---

## ⚙️ Configuration (`.apex/config.yaml`)

APEX automatically generates a configuration file in `.apex/config.yaml` upon first run. You can customize providers, local endpoints, and tree-search parameters:

```yaml
primary_provider: hybrid          # Options: hybrid, local_dgx, openai, anthropic, deepseek
local_dgx_endpoint: http://localhost:11434
local_model: qwen2.5-coder:latest
cloud_model: gpt-4o

lats_max_depth: 5
lats_max_branches: 3
lats_exploration_weight: 1.414
max_context_tokens: 128000

enable_git_checkpoints: true
enable_skill_synthesis: true
```

---

## 🧪 Testing & Verification

APEX includes a test suite covering hardware detection, tool execution, memory indexing, Git checkpointing, LATS node evaluation, and CLI commands.

Run the test suite with:

```bash
python -m unittest discover -s tests
```

**Expected Output**:
```
.......
----------------------------------------------------------------------
Ran 7 tests in 2.995s

OK
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
