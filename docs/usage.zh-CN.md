# 时间大师使用说明

## 1. 首次使用

在项目目录中执行：

```bash
cd TimeMaster-Widget
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp time_master_config.example.py time_master_config.py
python3 time_master.py
```

## 2. 日常启动

以后日常使用只需要：

```bash
cd TimeMaster-Widget
source .venv/bin/activate
python3 time_master.py
```

如果你不想让挂件依赖当前 Terminal 会话，也可以直接使用项目自带的启动器：

```bash
cd TimeMaster-Widget
./start_time_master.command
```

这样挂件会在后台运行，之后关闭 Terminal 也不会一起退出。

停止时使用：

```bash
cd TimeMaster-Widget
./stop_time_master.command
```

在 macOS Finder 里也可以直接双击这两个 `.command` 文件。

## 3. 界面操作

- 左键拖动挂件位置
- 双击打开设置
- 右键打开菜单
- 右键菜单可打开「统计…」查看近 30 天专注数据
- 右键菜单可切换中文 / 英文
- 右键菜单可退出程序

## 4. 设置项说明

当前支持的设置项：

- 目标日期
- 专注时长（分钟或小时；留空则不新开会话；保存后立即开始，最短 1 分钟）
- 透明度
- 界面语言

配置会写入本地 `time_master_config.py`。

专注统计数据写入本地 `time_master_focus_stats.json`（按日期记录秒数与次数），该文件默认不提交到 Git。

## 5. 本地配置文件

配置示例文件：

- `time_master_config.example.py`

实际运行配置：

- `time_master_config.py`

常见字段：

- `LANGUAGE`
- `WIDGET_ALPHA`
- `TARGET_ISO`
- `COUNTDOWN_START_ISO`
- `FOCUS_DURATION_SECONDS`
- `FOCUS_STARTED_ISO`

## 6. 常见问题

### 运行时报找不到文件

通常是因为没有先进入项目目录。

正确做法：

```bash
cd TimeMaster-Widget
python3 time_master.py
```

### 关闭 Terminal 后挂件也一起退出

请改用：

```bash
cd TimeMaster-Widget
./start_time_master.command
```

这个启动器会把挂件放到后台运行，而不是绑定在当前 Terminal 进程上。

### 切换语言后布局和中文不完全一样

这是当前设计决定。英文版使用单独布局参数，以适应更长的文案。

### 改了配置但没有生效

请确认：

- 修改的是 `time_master_config.py`
- 格式是合法的 Python 赋值语句
- 时间使用 ISO 格式

## 7. 后续如果你自己要改

最常见的修改入口：

- 改尺寸 / 配色 / 文案：`tm_resources.py`
- 改主窗口逻辑：`tm_app.py`
- 改进度条 / 设置弹窗 / 卡片绘制：`tm_ui.py`
- 改配置逻辑：`tm_config.py`
