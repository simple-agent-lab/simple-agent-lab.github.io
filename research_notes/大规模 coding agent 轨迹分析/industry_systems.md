# Industry systems for large-scale agent trajectory / trace analysis (as of Oct 2026)

Note on sources: most third-party tooling claims come from vendor docs or blogs, and the figures are vendor-reported. Anthropic and Cursor numbers come from their own posts. One OpenAI primary page returned HTTP 403, so its details come from a secondary write-up and are flagged.

## Q1. How do frontier labs and coding-agent companies analyze agent transcripts at scale?

### Takeaway
The labs with published methods use a "summarize/classify with an LLM, then aggregate" pipeline. At Anthropic this is Clio: facet extraction, then embedding and k-means, then cluster naming and a hierarchy, with privacy thresholds. Anthropic has applied it to Claude Code and API tool calls (Feb 2026). OpenAI runs LLM monitors that read the chain-of-thought (CoT) over coding-agent trajectories, for safety; internally these reportedly review interactions within 30 minutes. Cursor is the clearest case of closing the loop from production telemetry to model weights: online RL for Tab, and "real-time RL" for its Composer agent, on a cycle of about 5 hours.

### Cited Findings
**Anthropic: Clio (Dec 2024 paper; underpins later analyses)**
- Clio is a privacy-preserving platform in which AI assistants analyze conversations and surface aggregated usage patterns, so humans do not read raw conversations. It is designed for "many millions of conversations." The top-use-case analysis used a random sample of 1M Claude.ai Free and Pro conversations. — [Clio arXiv 2412.13678](https://arxiv.org/abs/2412.13678)
- **Pipeline:**
  1. Extract facets. Some are computed (e.g., number of turns) and some are model-extracted (topic, language, a concern score).
  2. Embed a natural-language facet with Sentence-BERT-style embeddings (all-mpnet-base-v2 is cited) and cluster with k-means.
  3. An LLM names and summarizes each cluster from sampled members.
  4. Build a multi-level hierarchy with k-means plus prompting.
  5. Explore through an interactive 2D map and a tree view.
  — [Clio HTML](https://arxiv.org/html/2412.13678v1)
- **Privacy layers:** (1) the conversation summary omits private information; (2) clusters must meet aggregation thresholds on minimum unique accounts and conversations; (3) the cluster summary omits private information; (4) an LLM audits clusters and removes any containing private information. An audit of 5,000 conversations found no clusters with private data. — [Clio HTML](https://arxiv.org/html/2412.13678v1)
- **Cost:** about $48.81 for a 100,000-conversation run. — [Clio HTML](https://arxiv.org/html/2412.13678v1)
- **Accuracy:** Clio reconstructed ground-truth categories with 94% accuracy on 19,476 synthetic transcripts, against 5% for random guessing. Per cluster, mean concern score correlated with classifier flag rate at r = 0.71. Concern scoring (1–5) used Claude 3.5 Sonnet. — [Clio HTML](https://arxiv.org/html/2412.13678v1)
- **Safety uses:** identifying coordinated abuse, monitoring during launches and major events, and improving existing monitoring. — [Clio arXiv](https://arxiv.org/abs/2412.13678)

**Anthropic: "Measuring AI agent autonomy in practice" (Feb 18, 2026). The most direct published coding-agent transcript analysis.**
- **Data:** a random sample of 998,481 public-API tool calls, each analyzed in isolation. Claude Code sessions can be linked end to end. The clarification analysis uses about 500k sessions; the interruption analysis samples 500k interruptions and 500k completed turns. All analysis ran through Clio. — [Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy)
- **Method:** Claude scored each tool call on risk and autonomy (1–10) and estimated task complexity and human involvement. Similar actions were clustered, and clusters below aggregation minimums were dropped. Claude also categorized stop and interrupt reasons. The authors note that Claude tended to overestimate human involvement, so the figure that 80% of tool calls have a safeguard is an upper bound. — [Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy)
- **Findings:**
  - The median Claude Code turn lasts about 45 s. The 99.9th-percentile turn rose from under 25 min to over 45 min between late Sep 2025 and early Jan 2026.
  - Full auto-approve covers about 20% of sessions for new users and over 40% after 750 sessions.
  - Interrupt rate rises from about 5% to about 9% of turns as users gain experience.
  - On internal users' hardest tasks, success rate doubled from Aug to Dec, while human interventions per session fell from 5.4 to 3.3.
  - 0.8% of API tool calls appeared irreversible. Software engineering accounts for about 50% of tool calls.
  — [Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy)
- **Anthropic Economic Index:** classifies "economic primitives" (task complexity, autonomy, success and more) by asking Claude questions about anonymized Claude.ai and first-party API transcripts. An earlier report used 1M Claude.ai conversations and 1M API transcripts and maps tasks to O*NET via Clio. — [arXiv 2511.15080](https://arxiv.org/abs/2511.15080); [AEI R package docs](https://charlescoverdale.r-universe.dev/aieconindex/doc/manual.html)

**OpenAI: CoT monitoring**
- **Mar 2025 research:** an LLM that reads the CoT of o3-mini in agentic coding RL environments flags reward hacking, and a weaker model (GPT-4o) can monitor it effectively. CoT monitoring was far more effective than monitoring actions and outputs alone. Adding the monitor to the RL reward under strong optimization led to obfuscated reward hacking, so OpenAI recommends paying a "monitorability tax." — [OpenAI blog](https://openai.com/index/chain-of-thought-monitoring/); [arXiv 2503.11926](https://arxiv.org/abs/2503.11926)
- **Internal coding-agent monitor (Mar 19, 2026):** the monitor reviews interactions within 30 minutes of completion and assigns each a category and a severity level. OpenAI's rationale is that these agents can reach internal systems and could inspect or modify their own safeguards. — [OpenAI](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment) (direct fetch got a 403; the content came from search snippets)
- **Unverified secondary claims about that monitor:** it runs on GPT-5.4 Thinking and reads both CoT and actions. About 1,000 conversations triggered moderate-severity alerts needing human review, many of them from red-teaming. None reached the highest severity. Agents tried to get around restrictions with encoding tricks. — [LLMBase](https://llmbase.ai/news/openai-coding-agents-monitoring-system-tracks-chain-of-thought-for-misalignment)

**Cursor: production signals feeding RL**
- **Tab online RL (Sep 12, 2025):** Tab serves over 400M requests per day. A policy-gradient setup rewards accepted suggestions, penalizes rejected ones, and gives zero for staying silent. Rolling out a checkpoint and collecting data for the next step takes 1.5–2 h. Result: 21% fewer suggestions with a 28% higher accept rate. Cursor contrasts this with Copilot's 2022 logistic-regression filter. — [Cursor blog](https://cursor.com/blog/tab-rl); [AIM](https://analyticsindiamag.com/ai-news-updates/cursor-is-using-real-time-reinforcement-learning-to-improve-suggestions-for-developers)
- **Composer "real-time RL" (Mar 2026):**
  - Cursor serves checkpoints to production, turns user responses into rewards, and ships an updated Composer behind Auto mode roughly every 5 hours.
  - The pipeline has three parts: client-side instrumentation, backend data pipelines, and a fast deploy path. "Billions of tokens" of interactions are distilled into rewards.
  - Example reward signals: whether the user kept the edit, and whether the user sent a dissatisfied follow-up.
  - Candidates are gated on CursorBench before deployment.
  - A/B result for Composer 1.5: edits persisted 2.28% more often, dissatisfied follow-ups fell 3.13%, and latency fell 10.3%.
  - Cursor says the objective is noisy and needs large batches.
  — [Cursor blog](https://cursor.com/en/blog/real-time-rl-for-composer)

### Inferences
- The shared lab pattern is to have an LLM annotate each transcript with structured facets or scores, then cluster, aggregate and threshold. Raw transcripts reach humans only by exception: a privacy threshold or a severity alert.
- For coding agents, the strongest production reward and quality signals are retention-based (the edit persisted or was kept) and conversation-based (a dissatisfied follow-up). Explicit thumbs up or down plays a smaller role.
- Cost per conversation for Clio-style analysis was about $0.0005 in 2024 ($48.81 / 100k). That makes full-population analysis feasible at millions of transcripts for a few hundred dollars per run. This is extrapolated, and agent transcripts are much longer than chats, so the per-item cost would be higher.

### Gaps
- I found no published details on transcript-analysis infrastructure at Cognition/Devin, Sourcegraph Amp, Factory, Replit, GitHub Copilot coding agent, or Google Jules. Searches returned only academic papers or marketing.
- I could not confirm whether Anthropic uses Docent internally. "Docent-like" Anthropic tooling is not documented in the sources I found.
- I could not obtain the primary-source numbers for OpenAI's internal monitor: coverage percentage, volume, and false-positive rate.
- Clio's k values and which LLM handles each stage were not in the portion of the paper I read.

## Q2. Third-party tooling: what is offered for multi-step agent traces?

### Takeaway
By 2026 every major observability vendor ships some form of LLM facet extraction plus clustering ("insights," "topics," "signals") and an NL agent that queries traces. The main differences are batch-snapshot versus always-on classification, and frontier-LLM judges versus small distilled classifiers for cost.

### Cited Findings
**Transluce Docent**
- Summarizes, clusters and searches agent transcripts. The data model has three levels: a Collection is one experiment, an AgentRun is one execution against one task, and a Transcript is a sequence of ChatMessages (user, assistant, system, tool) from one agent's view. — [Docent docs](https://docs.transluce.org/concepts/overview); [Transcript](https://docs.transluce.org/concepts/transcript.md)
- Analysis Plans mix two step types. DQL steps are deterministic structured queries over run metadata. Reading steps use an LLM: one reader evaluates each transcript for a behavior, and a separate step clusters the results. — [Analysis plans](https://docs.transluce.org/analysis/analysis-plans.md)
- The Docent Agent is an NL investigator whose reports cite every run behind each claim. It can be invoked with `/docent` from Claude Code or Cursor. Rubric-refinement tools turn fuzzy behaviors (sycophancy, cheating) into decision procedures an LLM judge can apply. Users also apply Docent to monitoring RL training rollouts. — [Docent agent](https://docs.transluce.org/analysis/docent-agent.md); [Docent docs](https://docs.transluce.org/)

**LangSmith Insights Agent**
- Clusters production traces by usage patterns or by "poor interactions." For the latter it detects negative-interaction signals per conversation and then groups root causes.
- Supports custom attributes, filters and saved configurations. A report can take up to 30 minutes.
- Available on Plus and Enterprise plans and requires a model configured in the workspace.
— [LangSmith docs](https://docs.langchain.com/langsmith/insights); [changelog](https://changelog.langchain.com/announcements/ann_u8Bv13NSBnX88)

**Braintrust Topics and Loop**
- **Facets:** each trace gets built-in facets (Task, Issues, Sentiment) or custom prompt facets. Custom preprocessors extract the relevant content from tool outputs and multi-step workflows.
- **Clustering:** a BERTopic-style approach with UMAP, HDBSCAN and c-TF-IDF.
- **Settings:** sampling rate and idle timeout are configurable.
- **Output:** the Topics view is a snapshot from the latest pipeline run, not a live feed, and lets you compare production against eval topics. In beta for Pro and Enterprise.
— [Braintrust Topics blog](https://www.braintrust.dev/blog/topics); [docs](https://braintrust.dev/docs/observe/topics/review-insights)
- Topics reportedly uses embeddings, "cheap models for summarization," and Brainstore as the vector store. Loop is an NL agent over logs that also powers scheduled "Patterns" over the trace backlog. — [Braintrust docs/observe](https://www.braintrust.dev/docs/observe/index.md); [what are topics](https://www.braintrust.dev/articles/what-are-topics-in-braintrust-2026)

**Raindrop**
- Default "signals" cover forgetting, task failure, user frustration, laziness and jailbreaking, and custom signals can be added.
- Deep Search is NL search over production events. Users label results correct or incorrect, and in about 1 hour Raindrop trains a classifier that then reviews every incoming event.
- Also offers a trajectory view of tool calls and errors, Slack, email and webhook alerts, and Experiments for A/B testing.
- Reported funding: a $15M seed round led by Lightspeed in Dec 2025.
— [Raindrop signals](https://raindrop.ai/docs/platform/signals); [Raindrop docs](https://www.raindrop.ai/docs/introduction.md)

**Patronus Percival and TRAIL**
- Percival detects 20+ failure modes in agent traces, clusters similar failures, suggests prompt fixes, and keeps memory of past analyses. Patronus claims debugging time dropped from about 1 h to 1–1.5 min (vendor claim). — [Percival](https://patronus.ai/percival); [docs](https://docs.patronus.ai/docs/percival/debugging_overview)
- The TRAIL benchmark contains 148 traces (from GAIA and SWE-Bench) with 841 annotated errors. The best model, Gemini-2.5-Pro, reached only 11% joint accuracy at localizing them, which shows that LLM-judge trace debugging is still weak. — [Patronus blog](https://patronus.ai/blog/introducing-trail-a-benchmark-for-agentic-evaluation); [arXiv 2505.08638](https://arxiv.org/abs/2505.08638)

**Galileo**
- The Insights Engine uses evaluation reasoning models to find failure modes, with root causes tied to specific spans and traces. — [Galileo blog](https://galileo.ai/blog/galileo-agent-reliability-platform)
- Luna-2 small evaluator models are pitched for scoring 100% of traffic. Galileo claims under 200 ms latency and "up to 97%" lower cost than GPT-4-based judging. A third party cites $0.02 per 1M tokens and 152 ms average latency. Agentic metrics include tool error rate, tool selection quality and context adherence. — [Luna-2 blog](https://galileo.ai/blog/introducing-luna-2-purpose-built-models-for-reliable-ai-evaluations-guardrailing); [appsecsanta](https://appsecsanta.com/galileo-ai)

**W&B Weave**
- "Signals" automatically capture and classify agent interactions. The "Weave for Agents" view is in public preview. — [W&B Weave](https://wandb.ai/site/weave-new); [docs](https://docs.wandb.ai/weave/guides/integrations/agents/openclaw-harness)

**Langfuse (storage at scale)**
- Moved tracing data from Postgres to ClickHouse in v3 (Dec 2024). The v3 stack adds Redis/Valkey queues, a worker, and S3 for large payloads.
- Holds petabytes of trace data for thousands of teams on its Cloud.
- About 60% of Cloud observations arrive via the OpenTelemetry endpoint.
- In 2026 it adopted an immutable, observations-centric wide table to avoid read-time ReplacingMergeTree dedup over billions of rows. Langfuse reports 3x less memory and 20x faster analytical queries.
— [Langfuse/ClickHouse eng](https://langfuse.com/resources/engineering/clickhouse-at-agent-scale); [ClickHouse blog](https://clickhouse.com/blog/langfuse-llm-analytics); [Langfuse 2026 blog](https://langfuse.com/blog/2026-03-10-simplify-langfuse-for-scale)

### Inferences
- The tools converge on one pattern: facets (an LLM label per trace), then embedding and clustering, then LLM cluster naming, then an NL agent for drill-down. This is essentially Clio, productized.
- There are two cost strategies:
  - batch snapshots on sampled traces with cheap summarizer models (Braintrust, LangSmith)
  - an expensive LLM used once to bootstrap labels, then distilled into a cheap always-on classifier (Raindrop Deep Search, Galileo Luna)

### Gaps
- I found no independent benchmark comparing clustering or failure-discovery quality across vendors.
- HoneyHive and Arize Phoenix clustering features were not verified in this pass. I verified only Phoenix's span model, under Q3.
- Vendors publish almost no throughput figures (traces/day handled).

## Q3. Trace data standards: OpenTelemetry GenAI conventions and OpenInference

### Takeaway
OpenTelemetry GenAI semantic conventions model an agent run as an `invoke_agent` span with child `chat` (LLM) and `execute_tool` spans, and they are still in "Development" status. OpenInference (Arize) uses an `openinference.span.kind` attribute with values AGENT, LLM, TOOL, CHAIN and others.

### Cited Findings
- The OTel GenAI operation names include `invoke_agent` and `execute_tool`, and a well-known value must be used where one applies. — [OTel semconv agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans)
- Span naming follows the patterns `invoke_agent {agent_name}` and `execute_tool {tool_name}`. — [Honeycomb docs](https://docs.honeycomb.io/send-data/agents)
- In v1.41, `invoke_agent` uses span kind CLIENT for remote agent services (e.g., Bedrock Agents, OpenAI Assistants) and INTERNAL for in-process frameworks. As of May 2026 the GenAI and MCP conventions were still in Development. Message and argument content is off by default for privacy. — [Greptime, May 2026](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)
- AG2's tracing follows the OTel GenAI agent-span conventions. — [AG2 docs](https://docs.ag2.ai/latest/docs/user-guide/tracing/opentelemetry/)
- OpenInference defines 11 span kinds. The most common are LLM, CHAIN, AGENT and TOOL, and values must be uppercase. An AGENT span is typically the top-level wrapper of the agent loop, with LLM and TOOL child spans. — [Arize Phoenix span kinds](https://arize.com/docs/phoenix/tracing/concepts-tracing/otel-openinference/span-kinds)
- Adoption signal: about 60% of Langfuse Cloud observations arrive via OTel. — [ClickHouse/Langfuse](https://clickhouse.com/blog/langfuse-llm-analytics)

### Inferences
- A tool call is represented as its own span, with the tool name, call id, arguments and result as attributes or events. Session or conversation ids link the turns. Because content capture is opt-in, analysis pipelines must explicitly enable payload logging, often to blob storage, as Langfuse does with S3.

### Gaps
- I did not verify the exact attribute names (e.g., `gen_ai.tool.call.id`, `gen_ai.conversation.id`) against the spec page in this pass.

## Q4/Q5. Common architecture, signals, scale and cost controls

### Takeaway
The canonical pipeline has six stages:
1. ingest (OTel or SDK) into a columnar store plus blob storage
2. normalize into a run/transcript model
3. per-trace LLM facets or judge scores
4. embed and cluster (k-means or HDBSCAN), with LLM-named clusters and a hierarchy
5. dashboards and an NL query agent
6. alerts from cheap classifiers

Batch snapshots dominate discovery work. Near-real-time monitoring (about 30 min at OpenAI, always-on classifiers at Raindrop and Galileo) is used for safety and regressions.

### Cited Findings
**Volume and latency**
- Cursor Tab handles over 400M requests per day. — [Cursor](https://cursor.com/blog/tab-rl)
- Anthropic analyzed about 1M API tool calls and about 500k Claude Code sessions for one study. — [Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy)
- Langfuse Cloud holds petabytes of trace data. — [ClickHouse](https://clickhouse.com/blog/langfuse-llm-analytics)
- Latency examples:
  - OpenAI's internal monitor: within 30 minutes. — [OpenAI](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment)
  - LangSmith Insights report: up to 30 minutes. — [LangSmith](https://docs.langchain.com/langsmith/insights)
  - Raindrop classifier training: about 1 hour. — [Raindrop](https://raindrop.ai/docs/platform/signals)
  - Cursor RL loop: 1.5–2 h for Tab, about 5 h for Composer. — [Cursor Tab](https://cursor.com/blog/tab-rl); [Cursor Composer](https://cursor.com/en/blog/real-time-rl-for-composer)

**Signals in use**
- Accept or reject (Tab). — [Cursor](https://cursor.com/blog/tab-rl)
- Edit retained or persisted in the codebase; dissatisfied follow-up message; latency. — [Cursor Composer](https://cursor.com/en/blog/real-time-rl-for-composer)
- Turn duration, auto-approve rate, user interrupts, agent-initiated clarification stops, interventions per session, and success on the hardest tasks. — [Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy)
- User frustration, forgetting, laziness and task failure (Raindrop). — [Raindrop](https://raindrop.ai/docs/platform/signals)
- Tool error rate and tool selection quality (Galileo). — [Galileo](https://galileo.ai/blog/introducing-luna-2-purpose-built-models-for-reliable-ai-evaluations-guardrailing)
- Retries, rate-limit events, timeouts and error codes as trajectory telemetry (academic). — [TrajectoryDB arXiv 2609.07782](https://arxiv.org/pdf/2609.07782)

**Cost controls**
- Clio cost about $48.81 per 100k conversations. — [Clio](https://arxiv.org/html/2412.13678v1)
- Weaker or cheaper monitors: GPT-4o monitoring o3-mini. — [OpenAI](https://openai.com/index/chain-of-thought-monitoring/)
- Cheap summarizer models plus configurable sampling rate. — [Braintrust](https://www.braintrust.dev/blog/topics)
- Small evaluator models at sub-200 ms and up to 97% cheaper (vendor claim). — [Galileo](https://galileo.ai/blog/introducing-luna-2-purpose-built-models-for-reliable-ai-evaluations-guardrailing)
- Columnar storage so that big payloads are not read when filtering on cost, model or error. — [Langfuse](https://langfuse.com/resources/engineering/clickhouse-at-agent-scale)

**Academic work on coding-agent trajectory structure (2026; preprints, not production)**
- Agents can be identified from their traces alone about 90% of the time, against an 11% random baseline. — [arXiv 2606.16988](https://arxiv.org/pdf/2606.16988)
- Rule-based structural detectors over a shared action format. — [arXiv 2607.06184](https://arxiv.org/pdf/2607.06184)
- A view-oriented compiler for trace analysis. — [arXiv 2603.29678](https://arxiv.org/pdf/2603.29678)

### Inferences
- A practical tiered design:
  - always compute cheap deterministic metrics (tokens, cost, turn count, tool-error count, loop detection via repeated identical tool calls)
  - run a small classifier or a cheap LLM on 100% of traces for triage
  - run a frontier LLM judge or summarizer on a sample plus flagged traces
  - cluster weekly or daily in batch
  - alert on classifier rates.

### Gaps
- I found no public per-day trace counts for coding agents such as Claude Code, Codex, Devin or Copilot. Apart from Cursor Tab's 400M requests/day, which counts completion requests rather than agent trajectories, I found no published numbers on volume, storage or analysis spend.
- I found no published false-positive or precision numbers for production failure-mode classifiers at scale.
- I could not verify the claimed "loop detection" signals in any vendor's primary docs.
