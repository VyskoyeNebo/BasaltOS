# BasaltOS pacman 仓库

生成目录为 `repo/x86_64/`，不纳入 Git。包含签名软件包、`basaltos.db.tar.gz`、
`basaltos.files.tar.gz` 及对应签名/别名。发布时将它们作为版本化 Release 附件中的
仓库归档，再从 `gh-pages` 分支的 Actions 工作流部署到 Pages；Git 仅保存源码。

占位地址：`https://OWNER.github.io/REPOSITORY/x86_64`，尚未公开部署。
完整步骤见 `docs/RELEASE.md`。
