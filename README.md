# ALPHAZERO

## Overview

This repository contains game-AI experiments inspired by the core AlphaZero idea: combine Monte Carlo Tree Search (MCTS) with a neural network that predicts policy (best moves) and value (position outcome), then improve through self-play.

At the moment, the project includes:
- A **functional Tic-Tac-Toe AlphaZero-style implementation**
- A **chess engine under active development** (currently semi-functional)

## Current Status

- ✅ **Tic-Tac-Toe AI**: functional and playable (MCTS-driven, with AlphaZero-style training components in the codebase)
- 🚧 **Chess engine**: in progress; core board state + move generation/UI work exists, but full engine completeness is still being developed
- 🔭 **Future goal**: train and integrate an AlphaZero-style chess agent once the chess engine is fully ready

## Features

- AlphaZero-inspired architecture concepts:
  - Search using MCTS
  - Policy + value neural network design
  - Self-play training loop structure
- Implementations for small-board game experimentation (Tic-Tac-Toe)
- Early chess engine implementation with graphical board rendering via Pygame

## Project Structure (high level)

- `AlphaZero.py` - Core AlphaZero-style components (network blocks, MCTS/self-play/training classes)
- `MCTS.py` - Tic-Tac-Toe + MCTS gameplay loop implementation
- `chess_engine.py` - Chess game state and move logic (work in progress)
- `chess_main.py` / `main.py` - Pygame-based chess board runner
- `engine.py` - Alternate/earlier chess engine logic module
- `1.ipynb`, `2.ipynb`, `3.ipynb`, `3.py` - Experiments/prototypes and iterative development artifacts
- `images/` - Chess piece assets used by the Pygame interface

## How to Run / Try the Project

From the repository root:

1. Create and activate a Python environment.
2. Install dependencies used by the scripts (at minimum: `numpy`, `torch`, `tqdm`, `pygame`).
3. Try available entry points, for example:
   - `python MCTS.py` (Tic-Tac-Toe MCTS play loop)
   - `python chess_main.py` (current chess UI/engine runner)

> Note: Exact, version-pinned setup instructions are not yet defined in this repository (no lockfile/requirements file currently present). Update this section as dependency/version choices are finalized.

## Roadmap

- [x] Build a working AlphaZero-style Tic-Tac-Toe pipeline
- [ ] Stabilize and complete chess move-generation/rules implementation
- [ ] Improve chess engine robustness and validation
- [ ] Connect completed chess environment to AlphaZero-style self-play training
- [ ] Train and evaluate an AlphaZero-inspired chess agent
- [ ] Document reproducible training/evaluation workflows

## Credits & Inspiration

- Project concept inspired by **Google DeepMind AlphaZero**.
- AlphaZero reference idea: learning by self-play with neural network guidance + MCTS search.
