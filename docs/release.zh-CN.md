# 构建与发布（macOS）

本文面向**维护者**：用 **PyInstaller** 打 **`Time Master.app`**、可选 **DMG**，并发布到 **GitHub Releases**。只下载安装包的用户不必阅读，安装步骤见仓库根目录 [README](../README.md)。

## 环境准备

- **macOS**、**Python 3.10+**。
- 克隆仓库后，在**项目根目录**使用**项目内**虚拟环境（与 README 里「从源码运行」一致）：

```bash
cd /path/to/TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

**注意：** 若误在用户主目录建了 **`~/.venv`**，请删除后 **`cd` 到真实项目目录** 再重新 `python3 -m venv .venv`。

## 构建独立 `.app`

在**仓库根目录**、已 `source .venv/bin/activate` 且装好依赖时执行：

```bash
./scripts/build_mac_app.sh
```

生成 **`dist/Time Master.app`**（PyInstaller；开发依赖见 `requirements-dev.txt`）。

**应用图标：** 使用 **`assets/AppIcon.icns`**，由 **`assets/app_icon_1024.png`** 生成。建议约 **1024×1024** 方形、四周不要留大块空白。更新图标：`python3 scripts/make_app_icon.py`（需先 `pip install -r requirements-dev.txt`），再重新执行 **`build_mac_app.sh`**。

**Gatekeeper：** 未签名构建首次打开可能被拦截，需在 **系统设置 → 隐私与安全性** 放行，或对应用 **右键 → 打开**，直至你使用开发者证书签名分发。

## 构建 DMG

在已有 **`dist/Time Master.app`** 后执行：

```bash
./scripts/build_dmg.sh
```

若缺少 `.app`，**`build_dmg.sh` 会先调用 `build_mac_app.sh`**。

生成 **未压缩只读 DMG（`UDRO`）**，内含 **Time Master.app** 与 **「应用程序」** 替身，便于用户拖到应用程序文件夹。

**产物路径：** `dist/Time-Master-<版本>.dmg`。版本默认来自 `git describe --tags --always`，也可手动指定：

```bash
VERSION=1.0.0 ./scripts/build_dmg.sh
```

## 发布到 GitHub Releases

1. **提交并推送**当前默认分支上希望随版本发布的改动。  
2. **打标签并推送**，例如：`git tag v1.0.0 && git push origin v1.0.0`（版本号自定）。  
3. 在 GitHub：**Releases → Draft a new release** → 选择该 tag → 上传 **`dist/Time-Master-*.dmg`**（可选再附 **`.app` 的 zip**）。  
4. 在 **Release 正文** 写清：  
   - 实测的 **最低 macOS 版本**  
   - 执行构建的机器是 **Apple 芯片还是 Intel**（与产物架构一致）  
   - **首次打开 / 隐私与安全性** 简要说明（与上文 Gatekeeper 一致）

**日常：** 开发时用 `python3 time_master.py` 迭代；发版时重新打包并上传新 DMG。源码运行时配置在项目旁；安装版使用 **应用程序支持** 目录——迁移时需自行复制文件。

## 给最终用户的安装步骤（可贴在 Release 里）

1. 下载 **`.dmg`**。  
2. 双击打开，窗口中有 **Time Master** 与 **应用程序**。  
3. 将 **Time Master** **拖入「应用程序」**。  
4. 推出 DMG，从 **启动台** 或 **访达 → 应用程序** 打开 **Time Master**。

若提示未知开发者，请到 **系统设置 → 隐私与安全性** 允许，或使用 **右键 → 打开**。

## 数据存放位置（独立 `.app`）

安装版运行时，配置与专注统计在：

`~/Library/Application Support/TimeMaster-Widget/`

## 后续：签名与公证

默认构建**未签名**。若需减少安全提示，可使用 Apple **Developer ID** 对 `.app` 或 DMG **签名并公证**（与上述脚本无关的独立流程）。
