# 官网与公开发版

本页对应 M7。M6 的 [签名与仓库基础](RELEASE.md)保留当时的本地准备记录；
当前对外入口为个人仓库 [VyskoyeNebo/BasaltOS](https://github.com/VyskoyeNebo/BasaltOS)。

- 官网：`https://vyskoyenebo.github.io/BasaltOS/`
- 文档：`https://vyskoyenebo.github.io/BasaltOS/docs/QUICKSTART.html`
- 签名仓库：`https://vyskoyenebo.github.io/BasaltOS/x86_64`
- 公开版本：`https://github.com/VyskoyeNebo/BasaltOS/releases/tag/v0.1.1`

## 一个 Pages 站点

首页源文件在 `docs/site/`，Markdown 源文仍在 `docs/`。
`scripts/build-site.py` 生成静态首页和文档站，保留代码块、表格、目录与截图，
并提供本地搜索。字体使用系统字体栈，图片、CSS 和 JavaScript 全部同源，未引入外部资源或统计脚本。

唯一 Pages 工作流为 `.github/workflows/publish-pages.yml`：

1. 下载已公开 Release 的小附件，不下载 ISO 分片到 CI。
2. 使用 M6 验证脚本检查固定公钥、签名清单、仓库归档和包/数据库签名。
3. 生成官网与文档，把经过验证的 `x86_64/` 合并到同一站点。
4. 上传 Pages artifact 并部署。

原 M6 仓库索引不会覆盖官网首页；`gh-pages` 分支保留历史发布入口，当前发布源是 main 的 Actions。
GitHub Settings → Pages 的 Source 应为 **GitHub Actions**。

## 本地构建

在项目内创建隔离环境：

```powershell
Set-Location E:\BasaltOS
python -m venv work/m7/site-venv
work/m7/site-venv/Scripts/python.exe -m pip install -r docs/site/requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
work/m7/site-venv/Scripts/python.exe scripts/build-site.py --output out/preview/BasaltOS
work/m7/site-venv/Scripts/python.exe scripts/check-site.py --site out/preview/BasaltOS
python -m http.server 8187 --bind 127.0.0.1 --directory out/preview
```

然后访问 `http://127.0.0.1:8187/BasaltOS/`。输出目录存在时构建器拒绝覆盖，
可选择新的 `out/` 子目录。构建需要本地经过验签的 0.1.1 Release 小附件；
CI 会先下载、验证并放到同样的工作目录。

## 当前 0.1.1 与首版来源

`v0.1.0` 指向 M6 已验收提交 `c014311`，作为首版完整保留。
0.1.1 重新构建 ISO，补齐四个常用桌面入口并更新版本信息，使用新的签名清单和版本化附件。
两版标签和附件各自独立，不覆盖或强推旧版本。详见 [0.1.1 验收](DESKTOP-FIX-0.1.1.md)。

GitHub 单附件限制小于 2 GiB；本次 ISO 为 2.192 GiB，上传三个已验证分片。
独立 `.sha256` 对应重组后的完整 ISO；`SHA256SUMS.asc` 认证本次 0.1.1 清单。
`join-iso.py` 只是便捷源码工具，不在签名清单中。

## 更新发布

先审阅发行说明与签名身份，准备好本地附件，创建草稿并完成上传，再公开发布。
首版部署记录见 [M7 验收结果](M7-RESULTS.md)，当前版本见 [0.1.1 验收](DESKTOP-FIX-0.1.1.md)。
后续版本必须重新完成自己的构建、验签和验收，不能复用本次散列或把测试密钥称为生产密钥。
维护者使用 M6 的 `scripts/release.sh` 准备附件；正式离线密钥和轮换流程仍需落实。

官网更新会由 main 上的站点/文档提交触发同一个 Pages 工作流，也可以手动运行。
更换公开 Release 时，应同步审阅工作流的 Release tag、payload 版本和首页/指南中的版本信息。
Git 只保存源码、文档和小型截图，不提交 ISO、分片、构建目录、私钥或仓库二进制。

## 试用公开软件仓库

当前仓库仍为测试用途，安装系统默认不启用。先阅读 [测试密钥与信任边界](RELEASE.md)，再明确启用：

```bash
sudo basaltos-repo enable https://vyskoyenebo.github.io/BasaltOS/x86_64
sudo basaltos-update --check-only
sudo basaltos-update
```

取消试用：`sudo basaltos-repo disable`。保持包及数据库签名 Required，
遇到验签失败先检查时间、密钥有效期与部署状态，不通过关闭验签解决。
