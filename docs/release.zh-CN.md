# macOS 发行说明（档 B）

本项目通过 **PyInstaller** 生成 **`Time Master.app`**，并可用脚本再打 **DMG**，方便用户「下载 → 打开磁盘映像 → 拖到应用程序」。

## 构建产物

| 产物 | 命令 | 说明 |
|------|------|------|
| `dist/Time Master.app` | `./scripts/build_mac_app.sh` | 可双击运行；内含 Python 与 PySide6。 |
| `dist/Time-Master-<版本>.dmg` | `./scripts/build_dmg.sh` | 内含同上 `.app`，以及指向 **应用程序** 的替身。 |

若尚未构建 `.app`，`build_dmg.sh` 会先自动执行 `build_mac_app.sh`。

文件名中的版本默认取 **`git describe --tags --always`**；若无 tag 则用 `0.0.0`。可手动指定：

```bash
VERSION=1.0.0 ./scripts/build_dmg.sh
```

## 发布到 GitHub Releases 的检查清单

1. 打标签并推送（示例）：`git tag v1.0.0 && git push origin v1.0.0`
2. 在 GitHub：**Releases → Draft a new release**，选择对应 tag。
3. 上传 **`Time-Master-*.dmg`**（如需也可另附 **`.app` 的 zip`**）。
4. 在 Release 正文中写明：
   - 已测试的 **最低 macOS 版本**
   - **Apple Silicon / Intel**（当前打包结果取决于你执行构建的机器架构，务必写清楚）
   - **首次打开**：未签名应用可能被拦截，需到 **系统设置 → 隐私与安全性** 点 **「仍要打开」**，或对应用 **右键 → 打开** 一次

## 给最终用户的安装步骤（可贴在 Release 里）

1. 下载 **`.dmg`** 文件。
2. 双击打开，窗口里会有 **Time Master** 与 **应用程序**。
3. 把 **Time Master** **拖进「应用程序」**。
4. 推出 DMG，从 **启动台** 或 **访达 → 应用程序** 打开 **Time Master**。

若提示来自未知开发者，请到 **系统设置 → 隐私与安全性** 允许，或使用 **右键 → 打开**。

## 数据存放位置

独立 `.app` 运行时，配置与专注统计在：

`~/Library/Application Support/TimeMaster-Widget/`

## 后续：签名与公证

档 B 默认 **未签名**。若需减少安全提示，可使用 Apple **Developer ID** 对 `.app` 或 DMG **签名并公证**（需开发者计划年费），流程独立于上述脚本。
