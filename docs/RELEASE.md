# BasaltOS M6 发布流程

当前为测试发布 `0.1.0-m6`，不是生产签名身份。里程碑标签为 `m6-release`。
正式版本使用 `MAJOR.MINOR.PATCH`，开发版本附 `-m6`、`-rc.1` 等后缀。
Arch `pkgver` 不含连字符，因此演示包使用 `0.1.0_m6-1`，独立的 pkgrel 用于打包修订。
后续发版应先更新 PKGBUILD 的 pkgver/pkgrel、发行说明与测试记录，再选择对应版本号生成附件。

## 信任与测试密钥

公钥：`packaging/basaltos-key.asc`，完整主钥指纹：

```text
29DAFB5537B451968276DA003941AA503494B8B1
```

UID：`BasaltOS TEST Release <basaltos-release@basaltos.local>`。
Ed25519 主钥仅认证，签名子钥：`9D912C7E6F4DF3D23A8B14BB3C1B8918CCCAA8D5`。
创建于 2026-11-02，主/子钥 180 天后在 2027-05-01 到期。
该邮箱只是本地测试标识，不是可验证的组织身份或收件地址。

本次私钥仅保存在专属构建机 `/root/BasaltOS/work/m6-private/gnupg`，目录权限 700，
随机口令保存在同一测试目录的 600 文件中，不打印口令、不导出私钥。
宿主承载该目录的 VDI 位于 `E:\BasaltOS\work\`，整个 work 被 Git 忽略。
私钥和口令同机只是测试便利，不构成离线密钥保护。

**正式发布时私钥应离线保存。** 更换测试身份，主钥离线，仅在受控签名机/硬件令牌使用
必要的签名子钥；私钥、口令和撤销证书分别加密备份，限制签名人员与用途。
不要把私钥放入 Git、ISO、软件包、GitHub Secrets、Pages 或 Release 附件。
本流程的 GitHub Actions 只验证已有签名，不持有签名私钥。
密钥到期前发布经过认证的新公钥/过渡版本；泄漏时停止发布、发布撤销与替换信息，
通过独立渠道核对新指纹，再在客户端移除旧信任。不要仅凭相同邮箱认定密钥可信。
GnuPG 参数依据 [官方密钥管理文档](https://www.gnupg.org/documentation/manuals/gnupg/OpenPGP-Key-Management.html)。

## 构建仓库与 ISO

沿用 M5 专属 VirtualBox 构建机；禁止重新格式化已有工作盘或附加飞牛 OS/其他系统盘。
Linux 内使用原生 ext4 工作目录，所有官方包仍从清华镜像下载。

```bash
cd /path/to/BasaltOS
python scripts/check-m6-baseline.py
sudo bash scripts/setup-builder.sh
# 仅首次创建测试身份，既有身份不会被覆盖；该脚本含本机公钥回传 URL。
sudo bash scripts/init-release-key.sh
# 首次生成后，将导出的公钥与指纹放入 packaging/ 及 profile 的 keys/，审阅并提交。
sudo env BASALT_REPO_DIR="$PWD/repo/x86_64" bash scripts/build-repo.sh
```

本机 bootstrap 使用 `scripts/prepare-m6-vm.sh`：只导出公钥和签名仓库。
它也把公钥本地签入专属构建机的 pacman keyring，以便严格验证构建依赖。
复用 Calamares 的既有二进制，其 SHA-256 必须仍为
`962127440180c43f8b8752174de190c9e29c364178acbe1bd406003580e40f81`，
不重编译、不改变安装器行为，补充独立签名后加入 M6 仓库。

仓库包含至少两个包：自建 `basaltos-release` 与补签的 Calamares。
演示包仅安装 `/usr/share/basaltos/release-info` 和许可证，不覆盖桌面、os-release 或引导配置。
`repo-add --sign --key FINGERPRINT` 生成 `basaltos.db.tar.gz`、`basaltos.files.tar.gz`
及签名，`.db`、`.files` 别名和其签名也必须托管。
本机导出为普通文件别名，避免 Windows/Pages 对链接的差异。
依据 [repo-add 手册](https://man.archlinux.org/man/repo-add.8.en)。

本机完整 ISO 构建与 Release 附件生成由 `scripts/build-m6-vm.sh` 记录。
它挂载 `/dev/sda1` 到 `/mnt`，把 `BASALT_M4_WORK` 工作盘挂到既有 native 路径，
通过 arch-chroot 在新 `m6-source.XXXXXXXX` 目录构建，不格式化磁盘：

宿主先在项目目录另开终端运行 `python scripts/transfer-server.py`，再打包源码：

```powershell
Set-Location E:\BasaltOS
tar -cf work/m6-source.tar .gitattributes .gitignore profile scripts packaging docs README.md repo/README.md .github
# 在专属构建机 Live tty 中，已挂载构建系统/工作盘并准备好签名仓库后：
# curl -fsS http://10.0.2.2:8181/scripts/build-m6-vm.sh -o /tmp/build-m6-vm.sh
# bash /tmp/build-m6-vm.sh
```

下列命令对应脚本中的 Linux 构建阶段：

```bash
sudo env BASALT_MILESTONE=m6 \
  BASALT_BUILD_ROOT=/root/BasaltOS/work/m4-native/linux-build \
  BASALT_OUT_DIR=/root/BasaltOS/work/m4-native/out-m6 \
  BASALT_LOCAL_REPO=/root/BasaltOS/work/m4-native/repo-m6/x86_64 \
  bash scripts/build.sh

sudo env BASALT_REPO_DIR=/root/BasaltOS/work/m4-native/repo-m6/x86_64 \
  BASALT_RELEASE_DIR=/root/BasaltOS/work/m4-native/release-m6/0.1.0-m6 \
  bash scripts/release.sh 0.1.0-m6 --existing-iso /path/to/basaltos-YYYY.MM.DD-x86_64.iso
```

也可直接 `sudo env ... bash scripts/release.sh 0.1.0-m6`，先构建再生成附件；
需配置同样的本地签名仓库与输出环境变量。输出目录已存在时拒绝覆盖已签名产物。
本机默认 GNUPGHOME 为上述测试路径；正式签名机应显式设置自己的 GNUPGHOME、
`BASALT_SIGNING_KEY` 并更新经过审核的公钥，使用 gpg-agent/硬件令牌授权。

该流程保证受保护的 M5 配置不变、正常更新/恢复路径保留，验证 ISO 卷标 basaltos、
大小 >500 MB 且 <8 GB。它提供可复现的构建步骤，**不承诺逐字节复现**：Arch 滚动仓库、
包时间戳和 ISO 日期均会变化，正式可重复构建还应固定包版本、源码与构建环境。

## 客户端导入与启用

ISO 仅带公钥与固定指纹。原有 Arch keyring 初始化保留，新增
`basaltos-keyring.service` 在 Live 原有 pacman-init 之后、安装后每次首启按需执行：
检查指纹、`pacman-key --init`、`--populate archlinux`、`--add`、`--lsign-key`。
安装器没有改动，服务随根文件系统复制到目标，重新初始化目标持久 keyring。
本地签名建立已核对公钥的信任，不是对任意未知签名放行。
依据 [pacman-key 手册](https://man.archlinux.org/man/pacman-key.8.en)。

ISO 的两份 pacman.conf 都带默认关闭的模板：

```ini
# [basaltos]
# SigLevel = Required
# Server = https://OWNER.github.io/REPOSITORY/x86_64
```

`Required` 在这个仓库要求包与数据库签名；官方仓库保持原有 Required DatabaseOptional，
本地文件继续 Required。新仓库加在官方仓库之后，减少同名包遮盖风险。
信任 keyring 的影响不是按仓库隔离，项目签名密钥仍是强信任边界，必须慎重保管。
参见 [pacman.conf 手册](https://man.archlinux.org/man/pacman.conf.5.en)。

```bash
# 发布后用真实 HTTPS 地址替换占位符：
sudo basaltos-repo enable https://OWNER.github.io/REPOSITORY/x86_64
sudo basaltos-update --check-only
sudo basaltos-update
# 暂停自建仓库：
sudo basaltos-repo disable
```

辅助工具拒绝未替换的 OWNER/REPOSITORY。验收只用本地 HTTP：
`sudo basaltos-repo enable http://10.0.2.2:8181/repo/x86_64 --allow-http`。
HTTP 仅为本机测试，签名验证仍严格启用；正式用 HTTPS，签名不提供传输保密性或防回放保证。

`--check-only` 只在临时目录同步数据库，临时复制**公钥和信任数据**，不复制私钥，
只读链接已安装包清单；不写真实 pacman 库/keyring、不创建快照、不安装软件。
它仍会联网下载已启用仓库的元数据。`--dry-run` 仍按 M5 语义真实创建快照和 boot 备份。
正常 `basaltos-update` 继续先快照/boot 备份，再 `pacman -Syu` 更新所有已启用仓库。
启用后会向所选托管商请求数据库和包，托管商可看到访问 IP 等常规请求信息；
本流程不添加项目遥测客户端或跟踪页面代码。

## 校验 Release 附件

附件目录含 ISO、`pacman-repo-VERSION.tar.gz`、公钥、SHA256SUMS、SHA256SUMS.asc、
RELEASE-NOTES.md 模板和 UPLOAD.txt。签名清单绑定 ISO、仓库归档和公钥散列。
GitHub 单附件必须小于 2 GiB，本次 ISO 超过该限制，脚本额外生成 1 GiB 的
`.iso.part00`、`.part01`、`.part02` 并把各片散列加入同一签名清单。
完整 ISO 保留在本地，GitHub Release 上传分片，不能直接上传本次完整 ISO。
依据 [GitHub Release 限制](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。

```bash
# 使用独立渠道核对公钥完整指纹后：
gpg --show-keys --with-fingerprint basaltos-key.asc
gpg --import basaltos-key.asc
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

仅下载分片时，先验签，再验证现有文件并重组：

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS
python scripts/join-iso.py --release-dir 附件目录 --version 0.1.0-m6 --output 新ISO路径
```

重组工具逐片检查散列，并检查完整 ISO 的散列；拒绝覆盖已有文件，支持 Windows/Linux Python。
它不替代前一步 GPG 身份校验。重组后的文件可以按普通 ISO 使用。

只下载公钥且从同一被篡改站点核对指纹不足以建立身份信任。
Windows 可先用 `Get-FileHash ISO路径 -Algorithm SHA256` 核对散列；完整认证仍需 GPG 验签。
本轮未托管到公网，不能把占位地址当作可用软件源。

## GitHub Release 与 gh-pages

本轮没有 Git remote、账号或真实仓库 URL，**没有执行 push、Release 上传或公开部署**。
本地 `gh-pages` 分支作为发布工作流入口，内容是源码和工作流，不提交 ISO 或仓库二进制。
GitHub Pages 设置选择 **GitHub Actions**，而不是直接从分支目录发布。
工作流只允许从 gh-pages 分支手动触发，下载经过审核的 Release 附件，验证固定公钥、
清单签名、散列、每个包及数据库签名，再将普通文件部署到 Pages。
这种方式保留 gh-pages 入口，同时避免二进制不断膨胀 Git 历史。
依据 [GitHub 官方 Pages 工作流文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

配置实际 Git remote 后，人工审阅并执行：
本轮两个本地标签已创建，通用 UPLOAD.txt 模板中的 `git tag` 步骤不必重复。

```bash
git push origin main gh-pages m6-release 0.1.0-m6
cd /path/to/out/releases/0.1.0-m6
# 填完发行说明后先创建草稿，不直接公开：
gh release create 0.1.0-m6 --verify-tag --draft --title 'BasaltOS 0.1.0-m6' \
  --notes-file RELEASE-NOTES.md basaltos-0.1.0-m6-x86_64.iso.part* \
  pacman-repo-0.1.0-m6.tar.gz basaltos-key.asc SHA256SUMS SHA256SUMS.asc
# 在 GitHub 审核并公开 Release，再触发：
gh workflow run publish-pages.yml --ref gh-pages -f version=0.1.0-m6
```

为 github-pages environment 设置允许分支 gh-pages，并按组织政策配置人工审核。
工作流不构建 ISO、不接收私钥；Actions 版本按当前官方示例选择，正式使用前应审核并固定提交散列。
本地可用 `python scripts/prepare-pages.py --version 0.1.0-m6 --release-dir 附件目录 --output 新目录`
验证同一份部署逻辑。Pages 内容不含 ISO。

## 对象存储或 Nginx

把 `prepare-pages.py` 产出的静态目录放到对象存储 HTTPS 站点或 Nginx 根目录即可。
保留 `.db`/`.files` 及其签名别名，禁止内容重写、自动解压或“优化”这些二进制文件。
软件包和签名使用不可变版本文件名；保留旧版本用于历史安装/回滚。
建议先上传独立版本目录、验证所有签名，再切换服务入口，避免数据库与签名分批发布的短暂不一致。
客户端若遇到验签失败应中止并重试/调查，不能临时关闭 SigLevel。

示意静态根目录 `/srv/basaltos/0.1.0-m6/` 下放 `x86_64/`，Nginx `root` 指向该目录，
配置 TLS 后，把客户端 URL 改为自己的 `https://repo.example/.../x86_64`。
对象存储使用对应前缀与 MIME 原样分发，检查缓存策略；不要上传签名私钥。

## 更新失败与回滚

更新仍使用 M5 的 Snapper pre/post 与独立 boot/ESP 备份，失败时保留事务 ID，
`sudo basaltos-update --recovery-info ID` 输出相应离线恢复命令。
固定 `rootflags=subvol=@` 不能直接套用 snapper rollback；完整步骤与边界见
[SECURITY.md](SECURITY.md)。快照不是外置备份，不包含固件密钥/NVRAM。
本轮针对已安装系统运行实际仓库同步/演示包安装及回归验收，
没有把它等同于所有版本升级、断电或磁盘损坏恢复已验证。
