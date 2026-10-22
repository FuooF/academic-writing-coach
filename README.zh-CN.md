<div align="center">

# Academic Writing Coach

### 学术写作教练：明确段落目的，解释修改选择，练习可迁移的方法

**Agent Skill · MIT · Python 3.10+ · v0.1.0**

[功能介绍](#功能介绍) · [修改示例](#修改示例) · [工作流程](#工作流程) · [安装](#安装) · [使用](#使用) · [来源与许可证](#来源与许可证)

[English](README.md) | **简体中文**

</div>

---

Academic Writing Coach 帮助智能体修改英文论文段落、解释表达选择，并为写作者提供针对性练习。它包含简洁的 [技能规范](SKILL.md)、**覆盖 12 个主题的 24 张原创指导卡片**及本地检索工具，支持用中文或英文解释。

公开包自带可直接使用的指导卡片，也能连接单独保存的个人阅读资料。**本仓库及其发布包不包含 Manchester Academic Phrasebank 的全文句式库。**

## 功能介绍

修改学术文字，首先要明确段落想完成什么，以及现有证据能支持怎样的表述。本技能帮助智能体先作出这些判断，再选择表达。

| 模式 | 你提供 | 你得到 |
|---|---|---|
| **查表达 Lookup** | 写作目的、句间关系或表达难点 | 少量相关表达及各自的使用条件 |
| **改段落 Revise** | 草稿及必要的研究背景 | 保留原有事实的修订稿，以及按需提供的修改解释 |
| **做练习 Teach** | 想学会的一种写作方法 | 简短讲解、示例、练习题及对你作答的反馈 |

12 个主题包括引言、文献综合、方法、结果、讨论、结论、审慎措辞、批判性评价、定义、比较、因果及过渡。每个主题有两张原创指导卡片。卡片用于解释写作判断，不是第三方句式库的全文转载。

### 修改原则

| 原则 | 智能体应当怎么做 |
|---|---|
| **先判断目的，再选择句式** | 明确段落的任务，以及不同陈述之间的关系。 |
| **让表达强度服从证据** | 保留数字、引用、研究范围、技术含义和必要的不确定性。 |
| **按需读取相关内容** | 检索少量有用卡片，避免为一次小修改加载全库。 |
| **解释可以迁移的方法** | 说明关键修改的理由，并在需要时换一个主题让作者练习。 |

研究事实以作者提供的材料为准。本技能不认证研究新颖性、参考文献真实性或方法有效性，也不保证录用。它对文章质量和作者学习效果的提升幅度，尚未经过对照实验测量。

## 修改示例

以下均为自拟教学示例，不代表真实研究发现或效果评测结果。

| 写作问题 | 原稿 | 一种修订方式 | 修改理由 |
|---|---|---|---|
| 列出了两项研究，却没有说清比较关系。 | “Study A uses interviews. Study B uses surveys. They have different evidence.” | “Study A uses interviews, whereas Study B uses surveys.” | 明确方法之间的对照，不添加原稿未提及的分析操作。 |
| 把观察到的现象写成了因果结论。 | “Attendance was higher among students who used the reminder. The reminder caused higher attendance.” | “Students who used the reminder had higher attendance.” | 保留已经提供的观察，去掉没有依据的因果推断。 |
| 过渡句只报出下一话题，没有连接已有结果。 | “The cache reduced processing time and increased operating cost. Next, we discuss cost.” | “Having reported the processing-time reduction, we next examine the cache's additional operating cost.” | 把下一话题与已提供的结果连接起来，不擅自断言收益能够抵消成本。 |

具体改法取决于上下文和证据。若你要求“只返回修改后的正文”，技能应直接给出修订稿，不强行附加教学内容。

## 工作流程

```mermaid
flowchart LR
    A[草稿或写作目标] --> B[明确段落目的]
    B --> C[核对现有证据与范围]
    C --> D[检索相关指导]
    D --> E[修订或示范]
    E --> F[按需解释与练习]
```

通用操作规则保存在 [SKILL.md](SKILL.md)；较大修改可参考 [修订评价要点](references/revision-rubric.md)；原创指导卡片保存在 [moves.json](references/moves.json)。智能体只需读取当前任务相关的内容。

## 安装

### 环境要求

- 能加载本地 skill 文件夹并读取支持文件的智能体。
- 安装、检索和可选导入工具需要 **Python 3.10 或更新版本**，仅使用标准库，无需安装第三方 Python 包或连接网络服务。

没有 Python 时，也可以直接阅读技能规范和指导卡片。安装器提供 Codex 与 Claude 目录选项；验证范围包括包结构和本地工具，不代表已经测试过所有版本智能体的完整集成。

### 下载后在本地安装

将本仓库下载为 ZIP，解压，在包含 `SKILL.md` 和 `scripts/` 的仓库根目录打开终端。根据使用的工具选择一条命令：

```bash
# 安装到 Codex
python scripts/install.py --target codex

# 安装到 Claude
python scripts/install.py --target claude
```

PowerShell 和 POSIX shell 均可运行上述命令。如果你的 Python 3.10+ 解释器名为 `python3`，请相应替换 `python`。

| 目标 | 默认安装位置 |
|---|---|
| Codex | 设置了 `CODEX_HOME` 时为 `$CODEX_HOME/skills/academic-writing-coach`；否则为 `~/.codex/skills/academic-writing-coach` |
| Claude | `~/.claude/skills/academic-writing-coach` |
| 自定义位置 | `<destination>/academic-writing-coach` |

如需安装到当前项目或其他技能目录：

```bash
python scripts/install.py --target codex --destination ../my-project/.agents/skills
```

`--destination` 指定技能文件夹的上一级目录，不是最终的 `academic-writing-coach` 目录。安装器遇到已有同名安装时会拒绝覆盖。个人语料应保存在安装目录之外，以便独立维护和更新。

手动安装时，将本包复制到目标技能目录下的 `academic-writing-coach` 文件夹中，保留 `SKILL.md`、`references/`、`scripts/` 以及来源和许可证文件。最终路径应为 `<技能目录>/academic-writing-coach/SKILL.md`。

## 使用

当智能体发现安装后的技能后，可以尝试：

```text
$academic-writing-coach 修改下面的文献综述段落，讲清不同研究之间的关系，保留全部引用，并用中文说明最值得学习的两处修改。
```

```text
$academic-writing-coach 帮我判断这段讨论需要表达对比、解释还是限定。给出英文修订稿，并用中文说明措辞选择。
```

```text
$academic-writing-coach 教我区分结果陈述和结果解释。先给一个简短示例，再出一道练习题，等我作答后反馈。
```

`$academic-writing-coach` 是 Codex 中显式调用的写法。其他智能体如采用不同语法，请使用相应的技能选择方式。

### 不通过智能体，直接检索

在包目录中运行：

```bash
python scripts/lookup.py search "literature synthesis 文献综合" --limit 4 --dataset builtin --json
python scripts/lookup.py get literature.compare-evidence --json
python scripts/lookup.py status
```

检索支持英文和中文词语；将搜索返回的 ID 传给 `get`，即可读取完整卡片。`--dataset builtin`、`local` 或 `all` 分别选择内置卡片、私有导入资料或两者。

## 可选：连接个人资料库

导入器接受配套本地 Phrasebank 整理流程生成的 `content.json`，其中包含页面说明、来源网址及小节内容。该整理流程目前已有的私人归档包含 12 个页面、130 个小节。**这些是使用者自行提供的本地资料，不随公开包分发。** 导入器不会爬取网站，也不授予使用或转载所导入内容的权利。

请把资料目录放在本仓库和已安装技能目录之外。例如在 PowerShell 中运行：

```powershell
python scripts/import_local.py --input "D:\my-reading\content.json" --data-dir "D:\my-private-writing-data"
python scripts/lookup.py search "literature review" --dataset local --data-dir "D:\my-private-writing-data" --json
```

在 POSIX shell 中也可以使用：

```bash
python scripts/import_local.py --input "$HOME/my-reading/content.json" --data-dir "$HOME/my-private-writing-data"
python scripts/lookup.py search "literature review" --dataset local --data-dir "$HOME/my-private-writing-data" --json
```

请将路径换成自己的文件位置。已有导入语料时，导入器默认拒绝替换；明确添加 `--replace` 后才替换语料。该参数用于导入工具，不是安装更新参数。

首次安装时，可以连接已经存在的私人资料目录：

```bash
python scripts/install.py --target codex --data-dir /path/to/my-private-writing-data
```

也可以每次检索时传入 `--data-dir`，或设置 `ACADEMIC_WRITING_COACH_DATA_DIR` 环境变量。没有私有资料时，内置卡片仍然可用。公开发布工具会排除私人资料和本地安装配置。

## 来源与许可证

[Academic Phrasebank](https://www.phrasebank.manchester.ac.uk/) 由曼彻斯特大学的 John Morley 创建，是此前个人知识库整理项目的参考来源，也在此作为写作资源提供链接。网站声明 Academic Phrasebank 属于曼彻斯特大学的知识产权；大学的 [版权声明](https://www.manchester.ac.uk/copyright/) 要求转载其网站材料时取得许可。

公开 skill 包含独立撰写的规则、指导卡片、示例和工具，不分发已经保存的 Manchester 网页、完整句式列表、本地归档的 `content.json`，也不分发其翻译和注释。注明来源本身并不能授权转载这些材料。未来如要加入第三方内容，需要具有覆盖该用途的许可证或授权。

本项目的原创材料采用 [MIT License](LICENSE)。MIT 不适用于外部资源或用户私有导入的内容。来源与权利范围详见 [SOURCES.md](SOURCES.md) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。本项目与曼彻斯特大学没有隶属关系，也未获其背书。

双语 README 的组织方式参考了 [Kiterlin/anti-defensive-writing](https://github.com/Kiterlin/anti-defensive-writing)，未打包其文案、图片或实现。

## 仓库目录

```text
academic-writing-coach/
├── SKILL.md                 # 智能体操作规范
├── agents/openai.yaml       # Codex 展示信息
├── references/              # 原创卡片与修订评价要点
├── scripts/                 # 检索、导入、安装及打包工具
├── tests/                   # 本地工具检查
├── docs/PUBLISHING.md       # 发布与 GitHub 上传说明
├── README.md
├── README.zh-CN.md
├── SOURCES.md
├── THIRD_PARTY_NOTICES.md
├── LICENSE
└── VERSION
```

## 验证与发布

以下命令用于完整源码包。精简的 `.skill` 运行包包含安装器和教学资料，不包含测试与发布构建工具；它是 ZIP 格式，解压后可运行 `python scripts/install.py --target codex`。

```bash
python -m unittest discover -s tests -v
python scripts/build_release.py --output ../release-artifacts
```

分发时使用生成的公开压缩包。GitHub 上传步骤与检查事项见 [发布指南](docs/PUBLISHING.md)。生成压缩包不会自动创建 GitHub 仓库或发布内容。

欢迎围绕具体写作判断或可复现的工具行为改进项目。贡献时提供原创示例和预期行为；未取得适当再分发许可的第三方句式库不应提交到仓库。
