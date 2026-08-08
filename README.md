# APEX CLI

APEX is a general-purpose, local-first autonomous agent system. It provides an intent-driven interface for software development, system administration, data analysis, web research, document synthesis, and general task execution.

APEX runs locally on Windows, Linux, and macOS, with native hardware telemetry and acceleration support for local GPU endpoints (Ollama, vLLM, NVIDIA NIM) alongside cloud model providers.

---

## Purpose

The goal of APEX is to provide a single interface for executing multi-domain digital tasks. Rather than relying on separate applications or manual context switching, APEX accepts high-level objectives, creates execution plans, executes actions in isolated sandboxes, and verifies results.

---

## Core Features

- **Document Ingestion & Reference Processing**: Parses and indexes PDF (`.pdf`), PowerPoint (`.pptx`), Word (`.docx`), and plain text/markdown documents into the Cognitive Knowledge Graph for reference and multi-document synthesis (`apex read`).
- **Local & Hybrid Model Routing**: Connects to local LLM inference servers (`http://localhost:11434` or `http://localhost:8000/v1`) and cloud provider APIs (OpenAI, Anthropic, Gemini, DeepSeek), routing sub-tasks based on task complexity.
- **Tree Search Execution (LATS)**: Uses Monte Carlo Tree Search (MCTS) with Upper Confidence Bound for Trees (UCT) scoring to generate and evaluate candidate execution paths.
- **Anticipatory Intelligence Engine**: Analyzes workspace files and telemetry to offer proactive recommendations (`apex suggest`).
- **Daily Productivity Digest**: Synthesizes task history and skill state into a daily summary (`apex digest`).
- **4-Tier Memory System**:
  - *Working Memory*: Dynamic token context budget and message window manager.
  - *Episodic Memory*: Session trajectory and past task recorder.
  - *Semantic Memory*: Codebase symbol and AST indexer.
  - *Procedural Memory*: Dynamic skill synthesizer storing reusable Python and Bash tools in `.apex/skills/`.
- **Cognitive Knowledge Graph**: Indexes session actions, file changes, reference documents, and research notes into a local SQLite database (`.apex/cognitive_graph.db`).
- **Policy Governance & Risk Evaluation**: Categorizes actions into risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and applies safety rules to command execution.
- **Shadow Git Checkpointing**: Takes Git commits before high-risk edits to allow 1-click workspace rollbacks.
- **Multi-Model Adversarial Debate**: Runs cross-examination of proposed solutions between models before executing code.
- **24/7 Background Ambient Mesh**: Optional background service for monitoring workspace health and running periodic verification tests.
- **Web Interface**: Includes a local web dashboard (`apex serve`) hosted at `http://localhost:7860`.

---

## Installation

### Requirements
- Python 3.10+
- Git 2.30+
- (Optional) Local GPU inference server (Ollama, vLLM, or NVIDIA NIM)

### Setup

```bash
# Option 1: Install as an editable package (Recommended)
pip install -e .

# Option 2: Install dependencies via requirements file
pip install -r requirements.txt
```

---

## Command Reference

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `apex read` | Parses PDF, PPTX, DOCX, or text file into Knowledge Graph | `apex read "paper.pdf"` |
| `apex serve` | Launches local web dashboard at `http://localhost:7860` | `apex serve` |
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
| `apex undo` | Rolls back workspace to previous shadow snapshot | `apex undo` |

---

## Configuration

Configuration parameters are stored in `.apex/config.yaml`:

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

## Testing

Run the automated test suite to verify document ingestion, tool execution, memory indexing, LATS search, and CLI interfaces:

```bash
python -m unittest discover -s tests
```

---

## License

MIT License.
