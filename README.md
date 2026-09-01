<p align="center">
  <a href="https://simpleagentlab.com/">
    <img src="./assets/logo.svg" width="88" alt="Simple Agent Lab logo">
  </a>
</p>

<h1 align="center">Simple Agent Lab</h1>

<p align="center"><strong>Simple yet effective methods for AI4AI.</strong></p>

<p align="center">
  <a href="https://simpleagentlab.com/">Website</a>
  ·
  <a href="https://github.com/simple-agent-lab">GitHub Organization</a>
</p>

Simple Agent Lab is an open AI research collective. We are working toward a
future where AI can help build AI, while the methods behind that progress
remain understandable to humans.

AI will increasingly write code, generate data, run experiments, evaluate
results, and improve models and systems. Improved AI can then help build the
next generation, forming a recursive loop of improvement. We believe this
future should remain simple, transparent, and verifiable so that people can
understand how progress happens and participate in deciding what comes next.

## Research

We explore:

- **AI4AI** — using AI to build, evaluate, and improve AI systems.
- **Self-Improving Systems** — systems that learn from evidence and become
  more capable over time.
- **Recursive Self-Improvement (RSI)** — the path from individual improvement
  loops toward systems that can improve how they improve.

Our direction is **AI4AI**. Our path is **Recursive Improvement**. Our
principle is **Simple**.

## Simple yet effective

Simple does not mean unsophisticated. Simplicity is what allows humans to keep
understanding and participating in a future built with AI. We want people to
see how a method works, verify why an improvement happened, and help decide
where it goes next.

Research is better when shared. We aim to share code, experiments,
evaluations, and failures so others can inspect, reproduce, and build on what
we learn.

## Selected work

- [**AI4AI Survey**](https://simpleagentlab.com/ai4ai/) — our survey of
  AI4AI, from long-horizon agents to recursive self-improvement: definitions,
  reliable horizons, and a closure audit of 35 systems.
  [[Paper](https://doi.org/10.20944/preprints202608.2108.v1)]
- [**AutoTrainess**](https://github.com/simple-agent-lab/AutoTrainess) — teaching language models to improve language
  models autonomously through a training-specialized Agent–Computer Interface.
  [[Paper](https://arxiv.org/abs/2606.31551)]
- [**Simple Long Horizon Agent**](https://github.com/simple-agent-lab/simple-long-horizon-agent) — a minimal,
  understandable agent loop for real long-horizon work.
Our members have studied or worked at ByteDance, UC Berkeley, Tsinghua
University, Shanghai Jiao Tong University, and Tongji University. All members
participate in a personal capacity. See our
[institutional affiliation disclaimer](https://simpleagentlab.com/disclaimer.html).

## About this repository

This repository contains the static website for Simple Agent Lab. It uses
plain HTML, CSS, and JavaScript and is deployed directly with GitHub Pages.

To preview it locally:

```bash
uv run python -m http.server 3000
```

Then open <http://localhost:3000/>.
