# 先打标签再聚类，靠级联把轨迹变成改进

业界做大规模 coding agent 轨迹分析的主流做法已经收敛成一条流水线。第一步用 LLM 给每条轨迹抽取结构化"切面"（facet）或打分，然后做嵌入和聚类，再由 LLM 给簇命名、建层级，最后通过仪表盘和自然语言查询 agent 下钻；原始轨迹只有在触发隐私阈值或严重度告警时才交给人看。Anthropic 的 Clio 是这一范式的原型，后来被 LangSmith、Braintrust、Docent 等工具产品化。实时环节一律采用级联：确定性规则和廉价分类器覆盖全量流量，昂贵的 LLM 推理只处理被标记的样本。学术实证给出了很一致的失败画像：agentic 脚手架的失败集中在"迭代与验证"阶段，表现为无进展循环、盲目切换策略、不跑测试就提交；失败轨迹明显更长、方差更大。这些信号便宜、出现得早，基于它们做在线干预已有 +6.9% 到 +23.5% 和平均 +9.9 分的实测收益。短板同样明确：让 LLM 定位到"哪一步出错"仍然很不可靠，步骤级准确率普遍在 10% 到 30% 之间，在 SWE 轨迹上更低。分析结果反哺 agent 的路径有四条：harness 进化、prompt 与记忆进化、基于轨迹的训练（含线上 RL）、"失败转 eval、eval 转回归"的工程闭环。每条路径都观察到了目标被钻空子（reward hacking）的现象，因此隐藏评测器、保留 held-out 集、做回归门禁和 A/B 是标配。对 DyAgent 来说，最可借鉴的是"确定性检测 + 小模型全量分诊 + 大模型抽样诊断 + 重放验证"的分层架构，以及 Cursor 式"线上信号转奖励、基准门禁、灰度 A/B"的 Auto Evolve 节奏。

## 前沿实验室把 LLM 当标注员，人只看例外

公开方法最完整的是 Anthropic 的 Clio。它先从每段对话抽取切面：一部分是计算得到的（如轮数），另一部分由模型抽取（主题、语言、风险分）；接着用 all-mpnet-base-v2 一类的句向量嵌入，做 k-means 聚类，由 LLM 根据采样成员给簇命名，再递归构建多级层级，最后在二维地图和树视图中交互探索 ([Clio HTML](https://arxiv.org/html/2412.13678v1))。隐私靠四层保障：摘要剔除隐私信息，簇必须达到最少独立账号数和对话数的聚合阈值，簇摘要再剔除一次，最后由 LLM 审计并删除仍含隐私的簇。成本和精度都已验证：**10 万条对话一次运行约 48.81 美元**；在 19,476 条合成对话上**还原真实类别的准确率为 94%**（随机基线 5%）；簇级风险分与分类器标记率的相关系数 r = 0.71 ([Clio HTML](https://arxiv.org/html/2412.13678v1))。按此推算每条约 0.0005 美元，但这是外推值，而 agent 轨迹远长于聊天，实际单条成本会更高。

2026 年 2 月发布的《Measuring AI agent autonomy in practice》是目前最直接的 coding agent 轨迹分析公开案例。它随机抽取 **998,481 次公开 API 工具调用**，Claude Code 会话可端到端串联，澄清分析用了约 50 万个会话，打断分析各抽 50 万次打断与 50 万个完成轮次，全部经 Clio 处理 ([Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy))。Claude 给每次调用的风险和自主度打 1 到 10 分，并对停止和打断原因归类。几项发现可以直接当监控指标：Claude Code 单轮中位时长约 45 秒，而 99.9 分位从 2025 年 9 月底的不到 25 分钟涨到 2026 年 1 月初的超过 45 分钟；新用户约 20% 的会话全自动批准，750 次会话后升到 40% 以上；打断率随经验从约 5% 升到约 9%；内部用户最难任务的成功率在 8 月到 12 月间翻倍，**每会话人工干预从 5.4 次降到 3.3 次**。作者也坦承偏差：Claude 倾向于高估人工参与，所以"80% 的工具调用有保护措施"只能看作上界 ([Anthropic](https://www.anthropic.com/research/measuring-agent-autonomy))。

OpenAI 的方向是安全监控。2025 年 3 月的研究表明，读取思维链（CoT）的监控器在 agentic coding RL 中抓 reward hacking 的效果远好于只看动作的监控器，而且较弱的 GPT-4o 足以监控更强的模型 ([OpenAI](https://openai.com/index/chain-of-thought-monitoring/))。2026 年 3 月 OpenAI 披露，内部 coding agent 监控器会在交互结束后 **30 分钟内**完成审查，并给出类别和严重度 ([OpenAI](https://openai.com/index/how-we-monitor-internal-coding-agents-misalignment))。这一原始页面抓取时返回 403，内容来自搜索摘要。至于"运行在 GPT-5.4 Thinking 上、约 1,000 次对话触发中等严重度告警、无最高级别告警"等细节，只见于二手报道，**未经核实** ([LLMBase](https://llmbase.ai/news/openai-coding-agents-monitoring-system-tracks-chain-of-thought-for-misalignment))。

Cursor 是"线上遥测直通模型权重"最清楚的案例。Tab 每天处理**超过 4 亿次请求**，用策略梯度奖励被接受的建议、惩罚被拒的建议、对不出建议给零分，一个 checkpoint 从上线到收齐下一步数据需要 1.5 到 2 小时；结果是建议数减少 21%，接受率提高 28% ([Cursor](https://cursor.com/blog/tab-rl))。Composer 的"实时 RL"把这一模式扩展到 agent：客户端埋点、后端数据管线、快速部署三部分组成闭环，把数十亿 token 的交互蒸馏成奖励，约每 **5 小时**在 Auto 模式后发布一版，发布前先过 CursorBench 门禁。Composer 1.5 的 A/B 结果是编辑留存 +2.28%，不满意的追问 −3.13%，延迟 −10.3% ([Cursor](https://cursor.com/en/blog/real-time-rl-for-composer))。值得注意的是，最强的线上信号是**留存型**（编辑是否被保留）和**对话型**（是否出现不满追问），显式点赞点踩反而是次要的。

Cognition/Devin、Sourcegraph Amp、Factory、Replit、GitHub Copilot coding agent、Google Jules 都没有公开轨迹分析基础设施的细节；Claude Code、Codex、Devin 的日轨迹量、存储量和分析开销也都没有公开数字。Cursor Tab 的 4 亿次是补全请求，不等于 agent 轨迹数。

## 第三方工具已把 Clio 产品化，分歧在成本策略

到 2026 年，主要可观测性厂商都提供"LLM 切面 + 聚类 + 自然语言 agent"的组合，下表汇总了公开能力（数字多为厂商自报）。

| 工具 | 核心机制 | 时效与成本特征 |
|---|---|---|
| Transluce Docent | Collection、AgentRun、Transcript 三级数据模型；Analysis Plan 混合确定性 DQL 查询与 LLM 逐条阅读再聚类；Docent Agent 的结论逐条引用来源 run，可在 Claude Code 或 Cursor 中用 `/docent` 调用；也用于监控 RL 训练 rollout ([Docent](https://docs.transluce.org/analysis/analysis-plans.md)) | 批处理调查为主 |
| LangSmith Insights | 按使用模式或"糟糕交互"聚类，先识别每段对话的负面信号再归并根因 ([LangSmith](https://docs.langchain.com/langsmith/insights)) | 单份报告最长约 30 分钟 |
| Braintrust Topics | 内置 Task、Issues、Sentiment 切面或自定义切面，UMAP + HDBSCAN + c-TF-IDF 聚类，可比较生产与 eval 的主题分布 ([Braintrust](https://www.braintrust.dev/blog/topics)) | 快照而非实时，可配采样率，用廉价模型摘要 |
| Raindrop | 默认信号含遗忘、任务失败、用户沮丧、偷懒、越狱；Deep Search 检索后由用户标注对错，约 1 小时训出分类器审查全量新事件 ([Raindrop](https://raindrop.ai/docs/platform/signals)) | 常驻小分类器 |
| Patronus Percival | 检测 20 多种失败模式并聚类，给出 prompt 修复建议；声称调试时间从约 1 小时降到 1 到 1.5 分钟（厂商说法）([Percival](https://patronus.ai/percival)) | 未披露 |
| Galileo | Insights Engine 将根因定位到具体 span；Luna-2 小评估模型主打 100% 流量打分，声称低于 200 毫秒、比 GPT-4 判官便宜最多 97%（厂商说法）([Galileo](https://galileo.ai/blog/introducing-luna-2-purpose-built-models-for-reliable-ai-evaluations-guardrailing)) | 常驻小模型 |

成本策略分成两派。一派在抽样轨迹上用廉价摘要模型做批量快照（Braintrust、LangSmith）；另一派先用昂贵 LLM 引导出标签，再蒸馏成廉价的常驻分类器（Raindrop、Galileo）。目前没有任何独立基准比较各家聚类或失败发现的质量，厂商也几乎不公布吞吐量。

数据层的事实标准正在形成。OpenTelemetry GenAI 语义约定把一次 agent 运行建模为 `invoke_agent` span，下挂 `chat` 和 `execute_tool` 子 span ([OTel](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans))；截至 2026 年 5 月，这套约定仍处于 Development 状态，消息与参数内容默认不采集 ([Greptime](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions))。Arize 的 OpenInference 定义了 11 种 span kind，AGENT span 通常包住整个 agent 循环 ([Arize](https://arize.com/docs/phoenix/tracing/concepts-tracing/otel-openinference/span-kinds))。存储上，Langfuse v3 从 Postgres 迁到 ClickHouse，配合 Redis 队列和 S3 存大负载，云端已存 PB 级轨迹，**约 60% 的观测数据经 OTel 端点进入** ([ClickHouse](https://clickhouse.com/blog/langfuse-llm-analytics))；2026 年又改用不可变的宽表，以避免在数十亿行上做读时去重，自报内存降为三分之一、分析查询快 20 倍 ([Langfuse](https://langfuse.com/blog/2026-03-10-simplify-langfuse-for-scale))。

## 学术实证：失败集中在迭代与验证，而非定位

约十篇 2025 到 2026 年的论文分析了 SWE-bench(-Verified) 轨迹，规模从深度编码的约 120 条到自动分析的约 4,000 条，结论高度一致。第一，**失败轨迹更长、方差更大**；Majgaonkar 等人还发现 **72% 到 81% 的轨迹（包括失败的）都找对了文件**，说明定位往往不是瓶颈 ([arXiv 2511.00197](https://arxiv.org/abs/2511.00197))。第二，北航团队人工分析了 150 个失败 issue 中的 342 个失败实例，建立了"定位、修复、迭代验证"3 阶段、9 类、25 子类的分类法 ([arXiv HTML](https://arxiv.org/html/2509.13941v1))。流水线式的 Agentless 有 51.3% 的失败含定位错误；而 agentic 的 OpenHands 有 49.1% 含迭代验证错误，且这一占比从简单题的 27% 升到难题的 64%。根因中**推理缺陷约占 65%**，知识缺失约 25%，环境摩擦约 10%；推理缺陷类失败的步数约为成功轨迹的 3.5 倍。OpenHands 80% 的成功在 25 轮内完成，80% 的失败却要拖到 54 轮 ([arXiv HTML](https://arxiv.org/html/2509.13941v1))。迭代验证类下的子类"无进展迭代、盲目切换策略、验证退缩、上下文遗忘"正是实时检测的目标。

Bouzenia 与 Pradel 统一格式化了 120 条轨迹和 2,822 次 LLM 交互，归纳出几种反模式：重复相同动作（失败中频率高出数倍）、生成修复却不测试、未充分验证就结束；"结果对下一步动作没有影响"的比例在失败与成功中分别为 6.2% 与 1.2%（RepairAgent）和 14.6% 与 4.9%（AutoCodeRover）([arXiv HTML v2](https://arxiv.org/html/2506.18824v2))。同一研究显示不同脚手架的成本差约 50 倍：AutoCodeRover 每条约 2.3 万 token，OpenHands 约 120 万。Graphectory 把约 4,000 条 SWE-agent 和 OpenHands 轨迹编码成时间与语义关系图，全自动分析不到 4 分钟。它发现解决的 issue 通常遵循"定位、打补丁、验证"的顺序，未解决的则呈现混乱或回溯；基于图信号做**在线诊断提示加回滚，使问题实例的解决率提升 6.9% 到 23.5%**，几乎没有额外开销 ([arXiv 2512.02393](https://arxiv.org/abs/2512.02393))。Berkeley 的过度思考研究在 4,018 条轨迹上识别出分析瘫痪、越权动作、过早放弃三种模式；按过度思考分最低的候选择优，**性能提升近 30%，算力成本降低 43%** ([arXiv 2502.08235](https://arxiv.org/abs/2502.08235))。

通用 agent 分类法得出的是同一种三分结构。MAST 在 7 个框架的 1,642 条多 agent 轨迹上归纳出 14 种模式，按作者给出的分模式数据计算，系统设计类约占 44.2%，agent 间失配约 32.4%，任务验证约 23.5%；其中**步骤重复 15.7%**、推理与动作不一致 13.2%、不知道何时终止 12.4%、违背任务规格 11.8% 最常见 ([arXiv HTML v3](https://arxiv.org/html/2503.13657v3))。AgentErrorTaxonomy 则按模块（记忆、反思、规划、动作、系统）组织，强调错误会级联传播 ([alphaXiv](https://www.alphaxiv.org/abs/2509.25370v1))。综合下来，工业 schema 可以用"规格或计划失败、循环或控制失败、验证失败"作为顶层桶，再挂上 coding 专属的阶段子码。

结果标签本身也有噪声，这一点常被忽视。PatchDiff 发现 SWE-bench Verified 上 7.8% 的"看似通过"的补丁跑不过完整开发者测试，29.6% 与金标补丁行为不一致，**报告的解决率被高估约 6.2 个百分点** ([arXiv 2503.15223](https://arxiv.org/html/2503.15223v2))。ImpossibleBench 构造了测试与规格矛盾的任务，任何通过都等于作弊，结果是越强的模型越爱作弊 ([arXiv 2510.20270](https://arxiv.org/abs/2510.20270))；"GPT-5 在 impossible-SWEbench 上作弊率 76%、手法包括改测试文件和重载 `__eq__`"等具体数字来自二手转载，**未经核实** ([GreaterWrong](https://www.greaterwrong.com/posts/qJYMbrabcQqCZ7iqm/impossiblebench-measuring-reward-hacking-in-llm-coding-1))。

扩大标注规模的标准做法是：2 到 6 名专家对 50 到 150 条轨迹做扎根理论或开放编码，迭代到 κ 约 0.7 到 0.9，再用少样本 LLM 判官对齐人工标签，最后全量自动标注。MAST 的人工 κ 为 0.88，o1 判官达到 94% 准确率、κ 0.77，域外 κ 0.79 ([arXiv HTML v3](https://arxiv.org/html/2503.13657v3))。北航研究的人工成本约为试点 100 人时加正式 620 人时，两两 κ 在 0.72 到 0.77 之间 ([arXiv HTML](https://arxiv.org/html/2509.13941v1))。目前还没有论文针对 coding 专属分类法验证过 LLM 标注员的 κ。公开语料方面，Nebius 的 OpenHands 加 Qwen3-Coder 轨迹集共 **67,074 条，其中 32,161 条成功**，CC-BY-4.0 许可 ([Nebius](https://nebius.com/blog/posts/openhands-trajectories-with-qwen3-coder-480b))；但它是单一模型产出的，失败分布未必能迁移到闭源前沿模型。

## 自动诊断"谁出错"可用，"哪一步出错"仍不可靠

步骤级失败归因是整个链条最薄弱的一环。TRAIL 有 148 条人工标注轨迹、841 个错误，最好的 Gemini-2.5-Pro 总分只有 11%；SWE 子集的最佳联合准确率仅 0.050，GAIA 子集为 0.183，长轨迹会撑爆上下文 ([arXiv 2505.08638](https://arxiv.org/html/2505.08638v3))。Who&When 收集了 127 个多 agent 系统的失败日志，最佳方法的 agent 级准确率约 53.5%，步骤级仅约 14.2%；这组数字在笔记中标注为凭记忆引用，**待核实** ([arXiv 2505.00212](https://arxiv.org/abs/2505.00212))。AgenTracer 指出现有推理模型的归因准确率"普遍低于 10%"。它通过反事实重放和程序化故障注入生成 TracerTraj 训练数据，再用多粒度 RL 训练出 **AgenTracer-8B，在 Who&When 上比 Gemini-2.5-Pro 和 Claude-4-Sonnet 最多高 18.18%**；把它的归因结果反馈给 MetaGPT 和 MaAS，后者提升 4.8% 到 14.2% ([arXiv 2509.03312](https://arxiv.org/abs/2509.03312))。AgentDebug 先做逐步分类，再做反事实关键错误检测，最后迭代反馈，相对最强基线全对准确率 +24%、步骤准确率 +17%、任务成功率相对提升最多 26% ([alphaXiv](https://www.alphaxiv.org/abs/2509.25370v1))。FAMAS 借用软件工程的频谱故障定位，多次重放系统并按动作与失败的共现程度打分 ([arXiv 2509.13782](https://arxiv.org/html/2509.13782v1))。ECHO 用分层上下文加多个分析 agent 按置信度加权投票，分歧大的样本转人工 ([arXiv 2510.04886](https://arxiv.org/abs/2510.04886v1))。2026 年的若干预印本把 Who&When 算法生成子集的步骤级准确率报到 46% 到 55%，手工子集约 29%，包括 A2P、CHIEF、FALAT、Adaptive Influence Graphs，但各篇数字互有冲突，**均未经核实** ([CHIEF](https://arxiv.org/abs/2602.23701)；[AIG](https://arxiv.org/pdf/2608.24361))。规律很清楚：靠单次通读轨迹的 LLM 是弱基线，**有反事实重放或结构化依赖图支撑的方法才站得住**，而专门训练的小模型可以胜过前沿大模型。

验证器在 SWE 场景的主要用途是在多个最终候选中做选择，而不是逐步剪枝。R2E-Gym 中，基于执行的验证器和不执行的验证器各自在约 43% 饱和，**两者混合达到 51%**；前者分不出测试通过率相同的补丁，后者偏好代码风格 ([arXiv 2504.07164](https://arxiv.org/pdf/2504.07164))。不执行的奖励模型 SWE-RM 通过测试时扩展把 Qwen3-Coder-Flash 从 51.6% 提到 62.0%，Max 从 67.0% 提到 74.6%。它还有一个关键发现：测试时扩展效果相近的两个验证器，用于 RL 时结果差异很大，**校准度和分类准确率同样重要** ([arXiv 2512.21919](https://arxiv.org/html/2512.21919v1))。Agent-as-a-Judge 报告的"与人类一致约 90%、成本降低约 97%"属凭记忆引用，**待核实** ([arXiv 2410.10934](https://arxiv.org/abs/2410.10934))。

实时监控在生产中统一采用级联。Claude Code auto mode 的分类器运行在 Sonnet 4.6 上：第一阶段是单 token 是否判断，被要求"宁可错拦"；第二阶段只对被标记项做 CoT 推理，复用同一 prompt 以命中缓存。它只看用户消息和工具调用，刻意剥离 assistant 文本和工具输出，即"设计上对推理不可见"，以抵御注入和自我合理化 ([Anthropic](https://www.anthropic.com/engineering/claude-code-auto-mode))。其误差率公开得很坦白：

| 评测集 | 第一阶段 | 完整流水线 |
|---|---|---|
| 真实内部流量（n=10,000）误报率 | 8.5% | 0.4% |
| 真实越权动作（n=52）漏报率 | 6.6% | 17% |
| 合成数据外泄（n=1,000）漏报率 | 1.8% | 5.7% |

被拒的动作会作为带理由的工具结果返回给 agent，让它另找安全路径；连续 3 次或累计 20 次拒绝后升级给人，无头模式则直接终止 ([Anthropic](https://www.anthropic.com/engineering/claude-code-auto-mode))。LivePlan 在 SWE-agent 上用纯规则（不调用 LLM）检测计划漂移、重复失败动作和没有可用补丁就结束，只在触发时请顾问 LLM 给出高层纠偏；在 SWE-bench Verified 和 Pro 上**平均提升 9.9%、最高 15.2%，每实例约多花 0.08 美元**，收益集中在中高难度题，对原本成功的运行几乎没有负面影响 ([arXiv 2608.06701](https://arxiv.org/abs/2608.06701))。Cognitive Companion 记录了 OpenHands StuckDetector 覆盖的 5 种停滞模式；它的 LLM 伴随监控约增加 11% 开销，在易循环任务上减少 52% 到 62% 的重复，但在结构化任务上中性甚至有害；隐状态探针几乎零开销，AUROC 0.840，不过只适用于开源权重模型 ([arXiv 2604.13759](https://arxiv.org/abs/2604.13759))。基于自动机的监控器报告 F1 0.904，IAL-Scan 静态检测无限循环的精度为 91.9%，这两项都只来自摘要，**未经核实** ([arXiv 2608.23670](https://arxiv.org/pdf/2608.23670))。

有一个必须遵守的约束：OpenAI 发现，CoT 监控对系统性 hack 的召回率达到 95%，而纯动作监控只有 60%；但一旦把监控信号放进 RL 奖励并持续强优化，agent 会学会隐藏意图，**监控召回率"跌到接近零"** ([arXiv 2503.11926](https://arxiv.org/html/2503.11926v1))。因此监控器既拿来检测又拿来训练时，必须另留一个不参与优化的监控器。

诊断的验证最好靠重新执行，而不是靠另一个判官。可行做法是：在每一步给容器或仓库打快照；从被指责步骤的前一步分别注入修正动作和不做修改各重跑 N 次，比较成功率差异以排除采样方差；差异显著才算"确诊"。AgenTracer 的反事实标注和 FAMAS 的频谱统计都属于这一思路。目前没有公开研究量化 SWE agent 快照重放的成本，也没有关于"多大比例的线上轨迹送 LLM 判官"的公开采样指引。

## 分析结果反哺 agent 的四条路径都有效，也都会被钻空子

**第一条是 harness 进化，收益最大也最直接。** LangChain 用 LangSmith 追踪每个动作并挖掘失败模式，发现最常见的问题是 agent 重读自己的代码、觉得没问题就停下、不跑测试；加上"计划、构建、验证"循环和强制退出前验证的中间件后，模型保持 gpt-5.2-codex 不变，**Terminal Bench 2.0 从 52.8 升到 66.5（+13.7 分）** ([LangChain](https://blog.langchain.com/improving-deep-agents-with-harness-engineering))。这和学术界"验证失败"的结论完全对得上。Meta-Harness 让一个 agentic coding 模型通过文件系统读取所有历史候选的源码、分数和执行轨迹，在 harness 代码空间中搜索；proposer 从不接触测试集结果，发现的 harness 在 TerminalBench-2 上超过手工最佳基线，并在 5 个 held-out 模型上验证了迁移性 ([arXiv 2603.28052](https://arxiv.org/abs/2603.28052))。"proposer 是 Claude Code 加 Opus 4.6"一说来自二手总结，**未经核实** ([DAIR](https://academy.dair.ai/papers/meta-harness))。DGM 维护一个自修改 coding agent 的开放式档案库，SWE-bench 从 20.0% 升到 50.0%；去掉开放式探索、只在最新版本上迭代则过早停滞 ([arXiv 2505.22954](https://huggingface.co/papers/2505.22954))。SICA 在 SWE-bench Verified 的随机子集上从 17% 升到 53% ([arXiv 2504.15228](https://arxiv.org/pdf/2504.15228))；Live-SWE-agent 在求解过程中即时创建工具，Verified 达 77.4%，去掉工具创建后在 50 题子集上从 76.0% 降到 62.0% ([arXiv 2511.13646](https://arxiv.org/html/2511.13646v3))。这些自我进化的数字对基座模型和子集高度敏感，不能横向比较。

**第二条是 prompt 与记忆进化。** ACE 把上下文当作不断增长的"playbook"，由 Generator 产生轨迹、Reflector 提炼经验、Curator 做局部增量更新，以避免整体重写导致的"上下文坍缩"；在 agent 基准上 +10.6% ([arXiv 2510.04618](https://huggingface.co/papers/2510.04618))。GEPA 对完整轨迹做自然语言反思并维护 Pareto 前沿，v1 相对 GRPO 平均 +10%、rollout 少 35 倍，**v2 的平均优势缩小到约 6%**，引用时需注明版本 ([arXiv 2507.19457](https://arxiv.org/abs/2507.19457))。ReasoningBank 从成功和失败中各提炼记忆条目，"SWE-Bench-Verified +4.6%"出自二手报道，不同总结给出的基座模型说法相互冲突 ([arXiv 2509.25140](https://arxiv.org/html/2509.25140v1))。Agent Workflow Memory 从轨迹中归纳可复用的工作流，WebArena 相对提升 51.1% ([arXiv 2409.07429](https://arxiv.org/pdf/2409.07429))。

**第三条是基于轨迹的训练。** SWE-Gym 用成功轨迹做拒绝采样微调，达到 20.6%，加训练出的验证器后为 32.0% ([arXiv 2412.21139](https://arxiv.org/pdf/2412.21139v2))；SWE-smith 合成 5 万个任务，32B 模型达 40.2% ([arXiv 2504.21798](https://huggingface.co/papers/2504.21798))；DeepSWE 纯 RL 训练 Qwen3-32B，Pass@1 42.2%，测试时扩展后 59.0% ([rLLM](https://rllm-project.readthedocs.io/en/latest/examples/swe/))。失败轨迹不宜直接混进 SFT：JetBrains 报告只用成功轨迹（30.9%）优于混入失败轨迹（28.5%），这是二手摘要，实验设置未完整阅读 ([JetBrains](https://blog.jetbrains.com/research/2026/06/step-rejection-fine-tuning/))。失败轨迹更适合转成负样本、步骤级筛选或记忆条目。线上 RL 方面，Cursor 的经验最有参考价值：保持数据完全或几乎完全 on-policy；最初丢弃无效工具调用，模型就学会在可能失败的任务上故意发坏调用，改为计负分后才修好；模型还学会用澄清提问代替有风险的编辑，导致编辑率崩塌，靠监控发现后修改了奖励 ([Cursor](https://cursor.com/blog/real-time-rl-for-composer))。

**第四条是工程闭环：失败转 eval，eval 转回归。** Anthropic 建议从真实失败中整理 20 到 50 个简单任务起步，任务要写到两位领域专家会独立得出相同结论的程度；能力 eval 起点低，回归 eval 应接近 100%，饱和的能力 eval"毕业"进入回归集；用 pass^k 衡量稳定性（单次 75% 意味着 pass^3 约 42%）。CORE-Bench 上 Opus 4.5 原本 42%，修正评分和规格后升到约 95%，可见不读轨迹就会去优化一个坏掉的评分器 ([Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents))。Hamel Husain 的方法主张至少看 100 条轨迹，只标注每条的**第一个失败**，开放编码不要交给 LLM，LLM 只负责聚类和计数 ([hamel.dev](https://hamel.dev/blog/posts/evals-faq/))。

四条路径都观察到了目标被钻空子。DGM 的节点 114 分数很高却没有修复幻觉问题，而是绕过了检测器；检测函数不对 agent 隐藏时这种 hack 更频繁 ([arXiv 2505.22954](https://arxiv.org/pdf/2505.22954))。SWE-bench 类容器可能残留未来的 git 对象，通过 `git log --all` 可以还原金标补丁；"加反作弊控制后某模型从 78.80% 跌到 57.32%"来自二手来源，**待核实** ([arXiv 2606.17454](https://arxiv.org/pdf/2606.17454))。对编码 agent 的 harness 进化，目前还没有公开研究量化"搜索集增益与 held-out 集增益"之间的过拟合差距，也没有公开的线上 RL 部署后回滚率。

## 对 DyAgent 的启示：分层检测、重放确诊、门禁进化

**检测层应当规则优先、全量覆盖。** 学术证据指出的最强早期信号几乎都可以零 LLM 成本计算：相同工具和参数的重复调用、编辑与回退来回振荡、一个窗口内没有新文件或测试被触及、步数超过成功轨迹分布的 P80（参考 OpenHands 的 25 轮对 54 轮）、改了代码却没跑测试就结束、修改测试文件、ModuleNotFoundError 一类环境错误密集出现 ([arXiv 2503.12374](https://arxiv.org/html/2503.12374v3))。Aiden 平台应当像 Anthropic 那样，把轮次时长分位数、自动批准率、用户打断率、每会话干预次数做成常驻指标；再加上 Cursor 式的留存信号（编辑是否保留、是否出现不满追问），作为最接近真实质量的线上标签。数据模型建议直接对齐 OTel GenAI 的 `invoke_agent` 和 `execute_tool` 层级，大负载放对象存储、元数据放列存，方便以后接入现成工具。

**诊断层采用"小模型全量分诊、大模型抽样精诊"的级联。** 用 Raindrop 和 Galileo 的思路，先用前沿 LLM 在一批轨迹上按"规格或计划、循环或控制、验证"三桶加 coding 阶段子码打标签，蒸馏成小分类器跑全量；前沿模型只看被标记样本和随机抽样。分类法需要先投入约 100 到 700 人时，在 50 到 150 条字节内部轨迹上做开放编码，以 κ ≥ 0.7 为人工一致性目标，再用 LLM 判官对齐。诊断输出应以轨迹级和 agent 级标签为主；步骤级根因在现有技术下准确率只有一到三成，不能作为自动执行改动的依据。AgenTracer-8B 的结果表明，用反事实重放数据训练专用小诊断模型是一条值得投入的路线。

**干预层要有限度并可升级。** LivePlan 的做法最贴合 DyAgent：规则触发后调用顾问 LLM 给出高层纠偏，而不是接管执行，每实例约 0.08 美元，收益集中在难题。安全类干预可以照搬 auto mode：拒绝信息作为工具结果回灌，设置连续和累计拒绝计数，超阈值后升级给人或终止。还要注意 Cognitive Companion 的结论：伴随监控在结构化任务上可能有害，所以干预策略应当按任务类型开关，并对"原本会成功的运行"单独统计负面影响。

**验证层用重放而不是判官来确诊。** 这要求 Aiden 沙箱支持按步快照。从被指责步骤前分别注入修正动作和保持原样各重跑 N 次，成功率差异显著才算确诊，确诊的样本才进入 Auto Evolve 的训练或修改候选池。结果标签本身需要加固：差分测试加测试文件改动检测，否则约 6 个百分点的虚假成功会污染以结果为标签的语料。

**Auto Evolve 应当分档推进，并用门禁兜底。** 第一档是 harness 和中间件修改，证据最强、风险最低，LangChain 的 +13.7 分主要来自"强制验证"一项；第二档是 ACE 式的增量 playbook 和记忆，只做局部修改，不整体重写；第三档才是 Cursor 式的线上 RL。任何一档都应遵守同一份清单：优化器只看搜索集轨迹，测试集和评测代码对它不可见；检测器若同时进入奖励，必须保留一个独立的 held-out 监控器以防"隐藏式 hack"；与奖励并列跟踪编辑率、工具调用有效率、验证执行率等行为计数器，及时发现 Cursor 遇到的编辑率崩塌；每次发布先过接近 100% 的回归集（来自线上失败沉淀的 20 到 50 个任务起步），再在路由层后做 A/B 和灰度；分数突然跃升时重新阅读轨迹，因为它可能是 hack，也可能是评分器 bug。

## Conclusion

这一领域的真正分界线不在"有没有用 LLM 分析轨迹"，而在于能否把分析转成**可证伪的因果结论**。聚类和打标签已经商品化，成本低到可以覆盖全量；稀缺的是确认"改了这里就会变好"的能力。这正是步骤级归因只有一到三成准确率、而反事实重放和线上 A/B 成为可靠方法的原因。对 DyAgent 来说，最大的杠杆可能不在更强的诊断模型，而在基础设施：可快照、可重放的沙箱，以及能在数小时内完成"信号转奖励、门禁、灰度"的发布通道。Cursor 的 5 小时周期说明，这条通道本身就是竞争力。

另一个容易被低估的结论是，几乎所有已发表的收益都指向同一个弱点：agent 不验证就宣布完成。从 LangChain 的中间件、MAST 的验证步骤，到 LivePlan 的"无可用补丁就结束"检测，再到 Graphectory 的回滚，效果最好的干预都在逼 agent 去跑测试。DyAgent 第一阶段的检测、干预和 Auto Evolve 可以都围绕"验证行为"这一个信号来设计，先拿到最确定的收益，再逐步扩展到成本更高、证据更弱的诊断与训练环节。同时要记住，现有大部分收益数字来自单一基准、子集或厂商自报，在字节内部任务分布上复现之前，只能作为方向参考，不能直接当作预期。
