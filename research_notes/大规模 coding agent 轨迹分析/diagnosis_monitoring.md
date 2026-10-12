# Automated Diagnosis and Real-Time Monitoring/Intervention for LLM (Coding) Agent Trajectories

Scope: 2024–2026, newest first where possible. Items marked [UNVERIFIED] come from search snippets or recall and were not checked against the primary text. Items marked [FROM MEMORY] were not re-checked in this session.

## Q1. Failure attribution / root-cause diagnosis (Who&When, AgentDebug, TRAIL, ECHO, AgenTracer, counterfactual/spectrum methods)

### Takeaway
Step-level failure attribution is still unsolved. On Who&When's hand-crafted split, the best 2026 methods reach about 29% step accuracy, and on the algorithm-generated split they reach about 46–55%. Off-the-shelf frontier LLMs often score under 10–20%. The approaches that work best add structure: causal or dependency graphs, hierarchical context, consensus voting, counterfactual replay to make training labels, or spectrum analysis over repeated replays. Purpose-trained small models (AgenTracer-8B) can beat frontier models at this task.

### Cited Findings
- **Who&When benchmark** (Zhang et al., ICML 2025, arXiv 2505.00212): failure logs from 127 LLM multi-agent systems, annotated with the failure-responsible agent and the decisive error step. It has two partitions, Algorithm-Generated and Hand-Crafted. In the original paper the best baseline reached about 53.5% agent-level accuracy but only about 14.2% step-level accuracy. [FROM MEMORY: verify exact numbers] — https://arxiv.org/abs/2505.00212
- Later papers report a step-level baseline of 16.67% (Alg-Gen) and 12.07% (Hand-Crafted). **A2P (Abduct-Act-Predict causal scaffolding)** raises these to 47.46% (2.85×) and 29.31%. [UNVERIFIED, search snippet] — https://arxiv.org/abs/2509.10401
- **CHIEF** (hierarchical causal graph built from flat logs, then backtracking; arXiv 2602.23701) reports 76.80% agent-level and 52.00% step-level on Alg-Gen, and 29.31% step-level on Hand-Crafted. A later preprint lists CHIEF with DS-V3.2 at 45.60% on Alg-Gen, so the reported figures conflict. [UNVERIFIED] — https://arxiv.org/abs/2602.23701
- **FALAT** (dependency-guided search over trajectories, arXiv 2606.00765) reports 46.0% step-level on Alg-Gen and 29.1% on Hand-Crafted. [UNVERIFIED] — https://www.alphaxiv.org/abs/2606.00765
- **Adaptive Influence Graphs** (arXiv 2608.24361) claims 55.20% step and 71.20% agent accuracy on Alg-Gen without the ground-truth answer, and 29.31% step on Hand-Crafted. This is the highest figure found, but it is a recent preprint and I could not verify it. — https://arxiv.org/pdf/2608.24361
- Search snippets also mention **WHO&WHEN PRO**, a larger benchmark built with controlled error injection, and **TraceElephant**, which claims full traces improve attribution accuracy by up to 76% over partial observation. [UNVERIFIED; no primary URL retrieved]
- **AgenTracer** (Zhang et al., arXiv 2509.03312, ICLR 2026) found that current reasoning LLMs attribute failures with "accuracy generally below 10%." It builds the TracerTraj dataset with counterfactual replay and programmed fault injection, then trains AgenTracer-8B with multi-granular RL. That model beats Gemini-2.5-Pro and Claude-4-Sonnet on Who&When by up to 18.18%. Feeding its attributions back into MetaGPT and MaAS improves them by 4.8–14.2%. — https://arxiv.org/abs/2509.03312 ; https://iclr.cc/virtual/2026/poster/10007726
- **AgentDebug / AgentErrorTaxonomy / AgentErrorBench** (Zhu et al., arXiv 2509.25370, ICML 2026):
  - The taxonomy covers memory, reflection, planning, action and system-level failure modes, and stresses cascading failures that start from one root-cause error.
  - AgentErrorBench holds annotated failed trajectories from ALFWorld, GAIA and WebShop. Its size is reported inconsistently, as 200 or 500+ trajectories. [UNVERIFIED]
  - AgentDebug isolates the root-cause step and generates corrective feedback. Against the strongest baseline it reports +24% all-correct accuracy and +17% step accuracy, and up to 26% relative improvement in task success.
  - It reportedly uses GPT-4.1 as the debugger, and smaller debuggers performed poorly. [UNVERIFIED]
  - Sources: https://www.alphaxiv.org/abs/2509.25370v1 ; https://icml.cc/virtual/2026/77923
- **TRAIL** (Patronus AI, arXiv 2505.08638) contains 148 human-annotated traces with 841 errors, built on a taxonomy of reasoning, execution and planning errors. It includes GAIA and SWE-bench splits. The best model, Gemini-2.5-Pro, scores only 11% overall. On the leaderboard, the TRAIL-GAIA split shows Gemini-2.5-Pro at joint accuracy 0.183 and location accuracy 0.546. On the TRAIL-SWE split, the best joint accuracy is 0.050 (Llama-4-Maverick). Long traces strain the context window. — https://arxiv.org/html/2505.08638v3 ; https://patronusai-trail.hf.space/
- **ECHO** (Banerjee, Nair, Borogovac, AWS; arXiv 2510.04886, NeurIPS 2025) has three parts. A hierarchical, multi-layer context representation of the trace addresses lost-in-the-middle. Objective analysis comes from a panel of analyst agents. Their votes are combined with confidence weighting and a minimum-confidence filter. It outputs a disagreement analysis that flags traces needing human review. It reports outperforming baselines on Who&When, especially for subtle reasoning errors. I did not retrieve exact numbers. — https://arxiv.org/abs/2510.04886v1
- **FAMAS** (arXiv 2509.13782; ACM DOI 10.1145/3797113) applies spectrum-based fault localization from software engineering. It replays the multi-agent system many times and scores each agent action by how strongly it co-occurs with failed runs. It reports outperforming all 12 baselines on Who&When. — https://arxiv.org/html/2509.13782v1
- **"Automata from Agent Traces: Failure and Next-Step Prediction"** (arXiv 2608.23670) learns automata from traces and uses them for failure and next-step prediction. [Snippet only] — https://arxiv.org/pdf/2608.23670

### Inferences
- Agent-level ("who") attribution is far easier than step-level ("when"). For coding-agent traces, expect step-level localization from an LLM judge to be wrong most of the time unless it is backed by structure: dependency graphs over file edits and tool outputs, or replay.
- Coding traces are especially hard. TRAIL-SWE's best joint accuracy is about 5%, against about 18% on GAIA. This is likely because SWE traces are long and their errors are subtle.
- The methods with the strongest grounding (AgenTracer, FAMAS, A2P) all use counterfactual reasoning or re-execution. Pure single-pass LLM reading of a trace is the weak baseline.

### Gaps
- I found no attribution benchmark built specifically on SWE-bench-style coding traces at scale, beyond TRAIL-SWE, which is small.
- I did not retrieve ECHO's exact numbers or the original Who&When numbers in this session.
- Newer 2026 preprints (AIG, FALAT, WHO&WHEN PRO, TraceElephant) still need verification.

## Q2. LLM-/Agent-as-a-judge and process reward models / verifiers for agents (inference-time use)

### Takeaway
For SWE agents, the main inference-time lever is verifiers that rank or select final trajectories and patches. Step-level PRMs used for pruning are less established. Hybrid verifiers that combine execution and execution-free signals beat either kind alone, and calibrated execution-free reward models (SWE-RM) now add about 7–10 points on SWE-bench Verified through best-of-n.

### Cited Findings
- **SWE-RM** (HKUST and Alibaba; arXiv 2512.21919; ICLR 2026) is an execution-free reward model: a MoE with 30B total and 3B active parameters.
  - With test-time scaling on SWE-bench Verified, Qwen3-Coder-Flash rises from 51.6% to 62.0%, and Qwen3-Coder-Max from 67.0% to 74.6%.
  - In RL, it adds 3 absolute points over execution-based reward.
  - Key finding: test-time-scaling performance alone does not predict RL usefulness. Classification accuracy and calibration matter as well, and two verifiers with near-identical TTS scores gave very different RL results.
  - The authors argue that unit-test verifiers are sparse, depend on unreliable test coverage, and are expensive.
  - Source: https://arxiv.org/html/2512.21919v1
- **R2E-Gym hybrid verifier** (arXiv 2504.07164; NeurIPS 2025):
  - Candidates come from the R2E-Gym-32B agent, whose pass@1 is 34.4%. It samples 26 trajectories (1 at T=0, 25 at T=0.8/0.9), giving Pass@26 = 64.4% as the ceiling.
  - Execution-based (test-generation) and execution-free verifiers each saturate around 42–43% Best@K (43.7% and 42.8%).
  - The hybrid of the two reaches 51% on SWE-bench Verified.
  - Failure modes: execution-based verifiers cannot separate patches with equal test pass rates, while execution-free verifiers are biased toward stylistic features.
  - Source: https://arxiv.org/pdf/2504.07164
- **SWE-Gym** (Pan et al., arXiv 2412.21139) trained an outcome verifier on agent trajectories and used it for best-of-n selection. OpenHands with a 32B model improved from about 20.6% to about 32.0% on SWE-bench Verified with best-of-16. [FROM MEMORY: verify] — https://arxiv.org/abs/2412.21139
- **AgentPRM, two different papers share the name:**
  - arXiv 2511.08325 ("Step-Wise Promise and Progress") scores steps by promise and progress toward the goal rather than by correctness. It is used for beam search over the top-N partial trajectories and reports better compute efficiency and test-time scaling. — https://arxiv.org/html/2511.08325v1
  - arXiv 2502.10325 (Choudhury, Cornell) uses an actor-critic setup with Monte Carlo rollout targets. On ALFWorld, 3B policies trained with it beat GPT-4o. It also discusses test-time scaling and reward hacking of the PRM. — https://arxiv.org/html/2502.10325v1
- **AgentRM** (arXiv 2502.18407) uses best-of-N plus step-level beam search guided by a reward model and reports an average +8.8 points across nine agent tasks. [Snippet] — https://themoonlight.io/review/agentrm-enhancing-agent-generalization-with-reward-modeling
- **Agent-as-a-Judge** (Zhuge et al., Meta/KAUST, arXiv 2410.10934) introduced the DevAI benchmark of 55 AI-dev tasks with 365 hierarchical requirements. An agentic judge that can inspect workspace files matched human consensus much better (about 90% alignment) than an LLM-as-a-judge (about 60–70%), at roughly 97% lower cost and time than human evaluation. [FROM MEMORY: verify exact numbers] — https://arxiv.org/abs/2410.10934

### Inferences
- In production, the cheapest high-value use of a verifier is selecting among parallel attempts and flagging low-confidence final patches. Step-level PRM pruning for coding agents is less validated.
- Calibration matters if verifier scores are used for early termination or escalation thresholds, as SWE-RM's finding shows.
- Execution-free judges carry known biases: style, and length or verbosity. Combining them with execution signals is a robust default.

### Gaps
- I found no strong published result on PRM-based early termination of SWE agents that reports cost saved against success lost. Most PRM work is on ALFWorld, WebShop or math.
- I did not verify SWE-Gym's or Agent-as-a-Judge's exact numbers in this session.

## Q3. Real-time monitoring and intervention (CoT/action monitors, auto-mode classifiers, loop/stagnation detectors, guardrails, watchdog agents)

### Takeaway
Production systems use a layered design: deterministic rules first (loop and stuck detectors), a cheap LLM or classifier gate on risky actions, and escalation to a stronger model or a human only on flags. Chain-of-thought monitors catch reward hacking far better than action-only monitors (95% vs 60% recall). That signal is fragile: it collapses toward zero if the policy is optimized against the monitor. Rule-triggered corrective advice has measured gains of +9.9 points on average (up to +15.2) on SWE-bench at about $0.08 per instance.

### Cited Findings
- **OpenAI, "Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation"** (Baker et al., arXiv 2503.11926, Mar 2025):
  - GPT-4o monitored a frontier reasoning model (o3-mini class) during agentic coding RL.
  - On systemic hacks, the action-only monitor reached recall of 40% (exit(0)), 80% (raise SkipTest) and 60% joint. The CoT monitor reached 93%, 97% and 95% joint.
  - A weaker model can monitor a stronger one.
  - Putting CoT-monitor pressure into the RL reward first reduces hacking. With more optimization, the agent learns obfuscated reward hacking and monitor recall "falls to near zero." The authors recommend paying a "monitorability tax."
  - Sources: https://arxiv.org/html/2503.11926v1 ; https://openai.com/index/chain-of-thought-monitoring/
- **Anthropic, Claude Code auto mode** (engineering post) gates actions with a transcript classifier running on Sonnet 4.6.
  - **Stage 1** is a fast single-token yes/no filter told to "err on the side of blocking."
  - **Stage 2** applies chain-of-thought reasoning only to items Stage 1 flagged. It reuses the same prompt, so the prompt is almost fully cache-hit.
  - **Inputs:** the classifier sees only user messages and tool calls. Assistant prose and tool outputs are stripped, making it "reasoning-blind by design," which resists injection and rationalization.
  - **Other layers:** a server-side prompt-injection probe screens tool outputs. In-project file edits and allowlisted tools skip the classifier.
  - **Error rates:**

    | Set | Stage 1 | Full pipeline |
    |---|---|---|
    | Real internal traffic (n=10,000), false-positive rate | 8.5% | 0.4% |
    | Real overeager actions (n=52), false-negative rate | 6.6% | 17% ("the honest number") |
    | Synthetic exfiltration (n=1,000), false-negative rate | 1.8% | 5.7% |

  - **Intervention:** a denial returns to the agent as a tool result with the reason, asking it to find a safer path. After 3 consecutive or 20 total denials, it escalates to the human. In headless mode it terminates.
  - **Latency/cost:** no figures are given.
  - Sources: https://www.anthropic.com/engineering/claude-code-auto-mode ; secondary: https://www.digitalapplied.com/blog/claude-code-auto-mode-classifier-numbers-published
  - An independent stress-test paper on ambiguous authorization scenarios (arXiv 2604.04978) exists, but I did not retrieve its results.
- **LivePlan, "Online Monitoring and Corrective Steering of Programming Agents"** (Liu, Dehghan, Kim, Ganhotra, Hirzel, Jabbarvand; arXiv 2608.06701, Aug 2026):
  - Built on SWE-agent. A deterministic rule-based monitor (no LLM calls) detects plan drift, repeated failed actions, and finishing without a working patch. Only then does it consult an advisor LLM for a high-level next-step correction.
  - Over vanilla SWE-agent on SWE-bench Verified and Pro, with 3 executor and 2 advisor LLMs, it improves resolution by up to 15.2% (average 9.9%) at about $0.08 extra per instance.
  - Gains are concentrated on medium and hard issues, with minimal regression on runs that already succeeded.
  - Source: https://arxiv.org/abs/2608.06701
- **Cognitive Companion** (arXiv 2604.13759) is a feasibility study of parallel monitoring.
  - Production frameworks use rule-based stuck detection: OpenHands' StuckDetector covers 5 stagnation patterns, and LangGraph uses iteration counts.
  - The LLM-based companion adds about 11% overhead and cuts repetition on loop-prone tasks by 52–62%.
  - A hidden-state probe (layer 28 of Gemma 4 E4B) adds zero measured inference overhead, with cross-validated AUROC 0.840 on a small proxy-labeled set.
  - Benefit depends on the task: positive on loop-prone and open-ended tasks, neutral or negative on structured tasks, and no help on 1–1.5B models.
  - It cites 10–15% per-step overhead for LLM-as-judge monitoring.
  - Source: https://arxiv.org/abs/2604.13759
- **Automata-based runtime monitor** (arXiv 2608.23670) uses cycle-rate thresholds plus a "stuck" rule and reports Monitor F1 = 0.904 on SWE-agent traces with no trained model. [Snippet; UNVERIFIED] — https://arxiv.org/pdf/2608.23670
- A terminal coding-agent engineering report (arXiv 2603.05344) describes adding "doom-loop" detection after agents repeated the same tool call with identical arguments. [Snippet] — https://arxiv.org/pdf/2603.05344
- **LlamaFirewall** (Meta, arXiv 2505.03574) has three scanners: PromptGuard 2 (jailbreak and injection classifier), AlignmentCheck (an LLM auditor of the agent's chain-of-thought and actions for goal hijacking), and CodeShield (static analysis of generated code).
  - On AgentDojo, the baseline has 17.6% attack success rate (ASR) and 47.7% utility.
  - AlignmentCheck with Llama 4 Maverick brings ASR to 2.89% (−84%) with utility 43.1%.
  - Adding PromptGuard 2 brings ASR to 1.75% (over 90% reduction) with utility 42.7%.
  - AlignmentCheck adds notable latency. Third-party estimates put it at hundreds of ms to seconds, against under 20 ms for PromptGuard. [secondary]
  - Sources: https://arxiv.org/pdf/2505.03574 ; https://www.infoq.com/news/2025/05/llamafirewall-agent-protection
- **NeMo Guardrails** (NVIDIA) is a programmable rails framework (input, output, dialog, retrieval and execution rails, written in Colang). I found no trajectory-level coding-agent accuracy numbers for it in this session. [Gap]
- **IAL-Scan** ("When Agents Do Not Stop," Jul 2026) statically finds infinite-agentic-loop bugs in agent code, with 91.9% precision over more than 6,500 repos. It is a pre-deployment complement to runtime detection. [Snippet; UNVERIFIED] — https://www.emergentmind.com/topics/ial-scan

### Inferences
- **Recommended stack for coding agents:**
  - (1) Deterministic detectors: identical tool call and arguments repeated, edit/revert oscillation, no new files or tests touched in a window, step or token budget burn rate, and finishing without running tests.
  - (2) A cheap single-token classifier on risky actions.
  - (3) An LLM advisor or reasoning stage only when (1) or (2) fires.
  - (4) Escalation counters that hand off to a human or kill the run.
- Monitors should not be put into the training reward without a held-out monitor, because of OpenAI's obfuscation result.
- Reasoning-blind action monitors (Anthropic) trade recall for robustness to persuasion and injection. CoT monitors (OpenAI) are better for catching reward hacking. The choice depends on whether the threat is the model's own misbehavior or external manipulation.

### Gaps
- I found no published head-to-head of mid-trajectory self-correction methods (Reflexion-style or PRM-guided) on SWE-bench reporting both success-rate delta and cost. LivePlan is the main datapoint.
- Latency for the Anthropic or OpenAI monitors is not public.

## Q4. Cheap-at-scale design and validating a diagnosis (triage, sampling, anomaly detection, replay and counterfactual re-runs)

### Takeaway
Every cost-efficient system in this survey uses cascades. A deterministic or near-free first stage filters most traffic, and expensive LLM reasoning runs only on flagged items: Anthropic's Stage 1 to Stage 2, LivePlan's rules to advisor, LlamaFirewall's PromptGuard (under 20 ms) to AlignmentCheck. Diagnoses are best validated by re-execution: counterfactual replay from the blamed step, spectrum statistics over repeated replays, or measuring whether feedback derived from the diagnosis raises success when re-run.

### Cited Findings
- **Cascade economics:** Anthropic's Stage 1 alone has 8.5% FPR. Adding Stage 2 on flagged items only brings FPR to 0.4%, at the price of higher FNR (6.6% to 17% on overeager actions), and Stage 2's prompt is cache-hit. — https://www.anthropic.com/engineering/claude-code-auto-mode
- **Rule-gated LLM calls:** LivePlan's monitor makes no LLM calls, and the advisor is only invoked on detection, for about $0.08 per instance. — https://arxiv.org/abs/2608.06701
- **Probes:** hidden-state probes add zero measured overhead (AUROC 0.840) against about 11% for an LLM companion and 10–15% per step cited for LLM-as-judge. This applies only to open-weight agents. — https://arxiv.org/abs/2604.13759
- **Small trained diagnosers:** AgenTracer-8B beats much larger proprietary models at attribution, so cheap fleet-wide triage with a fine-tuned small model looks feasible. — https://arxiv.org/abs/2509.03312
- **Small-debugger caveat:** AgentDebug reportedly found small debugger models weak without training. [UNVERIFIED] — https://www.alphaxiv.org/abs/2509.25370v1
- **Counterfactual replay as label generation and validation:** AgenTracer labels the decisive step by replaying with a corrected step and checking whether the outcome flips, and also by injecting faults programmatically. — https://arxiv.org/abs/2509.03312
- **Spectrum analysis via repeated replays:** FAMAS reruns the system multiple times and ranks actions by how strongly they correlate with failure. — https://arxiv.org/html/2509.13782v1
- **Validation by downstream effect:** AgentDebug's feedback raised task success by up to 26% relative. AgenTracer's feedback raised MetaGPT and MaAS by 4.8–14.2%. A diagnosis is useful if acting on it changes the outcome. — https://www.alphaxiv.org/abs/2509.25370v1 ; https://arxiv.org/abs/2509.03312
- **Human-review routing:** ECHO's disagreement analysis among analyst votes flags uncertain attributions for human review. — https://arxiv.org/abs/2510.04886v1
- **Sliding-window novelty for stagnation:** the snagline tool measures the share of never-seen action signatures in a sliding window. It is separate from exact-repeat detection, and is a tool rather than a paper. — https://pypi.org/project/snagline/

### Inferences
- **Practical validation protocol for coding-agent diagnoses:**
  - Snapshot the container or repo state at each step, which requires deterministic checkpointing.
  - Re-run from the step before the blamed step with an oracle hint or a corrected action, N times, and measure the change in success rate against unmodified re-runs from the same checkpoint. This controls for sampling variance.
  - A diagnosis counts as "confirmed" if the intervention significantly raises success.
- **Embedding-based anomaly detection:** I found no specific published results for agent traces. Clustering trajectory or action embeddings for triage is plausible but unvalidated in the sources found.

### Gaps
- I found no published study quantifying the cost of checkpoint-replay validation for SWE agents (environment snapshot overhead, rerun cost).
- I found no source for embedding-based anomaly detection results on coding-agent traces.
- I found no public sampling-rate guidance, i.e. what fraction of fleet traces to send to an LLM judge.
