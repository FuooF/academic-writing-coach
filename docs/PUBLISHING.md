# Publishing and licensing

[English README](../README.md) · [中文说明](../README.zh-CN.md)

The source package is prepared for a new GitHub repository named `academic-writing-coach`. No account name, remote URL, live release, or completed hosted CI run is assumed. The instructions below do not publish anything until the maintainer performs the upload or Git push.

## What can be uploaded

Upload the contents of the public `academic-writing-coach/` source directory: its code, original teaching material, documentation, tests, metadata, and workflow files. The `LICENSE` file grants MIT permissions for project-owned material; [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) explains the boundary.

The complete Manchester corpus, the earlier HTML/Markdown archive, imported `*.private.json` files, local configuration, and user drafts are not part of this distribution. Keep the local data directory outside the repository. If you receive a separate private data folder together with this package, do not upload that folder or attach it to a public release.

## Why source attribution alone is insufficient

Review date: **22 October 2026**. This is a release-design assessment based on published terms, not a legal determination for every jurisdiction or use.

The [Phrasebank home page](https://www.phrasebank.manchester.ac.uk/) discusses incorporating suitable generic expressions into one's own writing and identifies university ownership. The copyright link in its footer leads to a [notice requiring permission to reproduce university material](https://www.manchester.ac.uk/copyright/). The [About page](https://www.phrasebank.manchester.ac.uk/about-academic-phrasebank/) discusses phrase reuse in academic writing; that discussion is not an open license for redistribution of the complete compilation.

We did not find an open license covering redistribution of the full Phrasebank corpus on those pages. The project initiator has not supplied a separate redistribution authorization. Consequently, this public package uses original coaching material and source links, with optional import of user-local files.

Attribution documents provenance. It does not by itself grant rights to copy a compilation, translate it, or license it to downstream GitHub users. Converting web content into JSON or Markdown does not resolve that permission question. A license displayed on another university resource does not automatically apply to Phrasebank.

Copyright exceptions depend on purpose and circumstances. [The UK Intellectual Property Office's guidance](https://www.gov.uk/guidance/exceptions-to-copyright) describes limits on research, private study, quotation, and teaching exceptions. A free educational repository should not assume that those exceptions authorize publication of an entire third-party teaching resource. The legal treatment of an individual commonplace expression can differ from that of explanatory text, tables, or a selected compilation.

If a future release should include the source corpus, obtain permission that covers the actual proposed material and distribution: original text and tables, any translation or adaptation, public GitHub hosting, downloads, forks, modification, commercial use if intended, and any downstream licensing. Apply the permission actually granted; do not automatically label the material MIT. GitHub's [licensing guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) explains the importance of an explicit repository license but does not supply rights to upstream content.

## Validate and build

From the public repository root with Python 3.10 or later:

```bash
python -m unittest discover -s tests -v
python scripts/build_release.py --output ../release-artifacts
```

Keep the output directory outside the source repository. The builder uses `release-manifest.json`, includes license and provenance files, and emits checksums. Inspect the built archive's file list before publication, especially after changing the release manifest or reference content. An allowlist reduces accidental inclusion; it is not a substitute for reviewing what is inside listed files.

The `.skill` file, if generated, is a ZIP-formatted portable artifact. Codex and Claude Code can be installed using the included Python installer from the source directory or an extracted runtime archive. A `.skill` extension does not mean that every application supports one-click import.

## Upload to GitHub

1. Create a new repository under your own account, preferably named `academic-writing-coach`.
2. Upload the public source directory's **contents**, so `README.md`, `SKILL.md`, and `LICENSE` are at the repository root. Do not upload the parent outputs directory or the private corpus directory. GitHub's web uploader does not unpack a ZIP into source files.
3. Alternatively, initialize a local Git repository in the public source folder and push it to the remote URL GitHub provides. Review `git status` before the first commit; hidden files such as `.github/` and `.gitignore` belong in the source repository.
4. Enable GitHub Actions if it is disabled. The supplied CI runs tests on Linux and Windows. Hosted workflow results are only known after the workflow actually runs in your repository.
5. For a manual release, create a release tagged `v0.1.0` and attach the public build artifacts and checksum file. Do not attach local corpus files.

The included release workflow also builds and attaches public artifacts when a version tag is pushed. It requires the repository's normal `GITHUB_TOKEN` contents-write permission; no personal token or external service key is required. Tag and `VERSION` must agree. A maintainer can use manual release upload if Actions publishing is unavailable.

The current copyright holder line names “Academic Writing Coach contributors”. Maintainers may add their correct credited identity for their contributions; do not substitute the university as author or imply its endorsement. Repository owner-specific badges and remote install URLs can be added after the actual GitHub location exists.

## 中文发布说明

可公开上传的是本项目原创的 skill 指令、24 张教学卡、脚本、测试和说明文档，使用 MIT 许可证。Manchester 原文、逐条译文、原网页和私人全文包不随公开版分发。当前版本已能独立使用；本地导入只是让使用者连接自己持有、且其使用有依据的资料。

README 注明来源有助于透明说明，但不能替代全文再分发授权。官网关于句式用于论文的说明，与公开再发布整个资料集合属于不同范围。公开版不会通过更换文件格式、增加署名或加入“仅供学习”声明来假定获得上游权利。

上传前运行测试和打包命令，只上传公开源代码目录的内容或公开构建产物。单独交付的私人语料、`.local-data-config.json` 和用户稿件应保留在仓库之外。若以后获得整库授权，应按授权的实际条款单独处理资料许可。
