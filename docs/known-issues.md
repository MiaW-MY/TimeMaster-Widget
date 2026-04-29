# Known issues / 已知问题

## EN: English main-card layout feels off (title vs mascot + whole functional block)

**Status:** Open — recorded for follow-up; layout not changed in this note.

**Symptoms:**

1. **Title vs mascot:** The last letter of **Time Master** (the **r**) sits very close to the small cat in the top-right. The user reports this used to look correct and regressed after recent layout work.
2. **Whole functional block:** Beyond the title, the **overall position of the main functional area** (title + rows/progress bars + related controls as one visual block) also seems **shifted or unbalanced** compared to before — it “looks wrong” on the card, not only the **r**/cat gap.
3. **Horizontal “nudge right” (follow-up screenshot):** The user reports the **entire centered column** (title + four rows) looks **slightly shifted to the right** vs the card — **more empty space on the left** than on the right inside the rounded card.

**Historical baseline (user-labeled screenshots, also on disk):** **Figure 1 / 图1 = before** (`docs/reference-main-layout-before.png`): main content **left pillar** — title **Time Master**, four rows, and bars share a **common left edge** with **more air on the right** inside the card. **Figure 2 / 图2 = now** (`docs/reference-main-layout-current.png`): the same content reads as a **centered column** (roughly equal side margins; bars sit nearer the card’s horizontal middle). The **current** code uses **`AlignHCenter`** for that stack, so the “moved right vs memory” feeling is **largely alignment policy** (left pillar → centered column), **plus** mascot/title crowding.

**Code investigation — main view, horizontal (no code changes):**

- **English `card_margins`** in `tm_resources.py` are `(10, 16, 10, 1)` → **left and right are both 10 px**; there is **no** left/right asymmetry in layout margins for **en** (unlike **zh**, which uses `(7, 9, 11, 4)` — **left 7, right 11**).
- In `tm_app.py`, **`title_label`**, **`focus_body`**, **`day_row`**, **`month_row`**, and **`year_row`** are added to **`card_layout`** with **`Qt.AlignmentFlag.AlignHCenter`**, and widths are **`BAR_W` (110)** for the title slot, `focus_body`, and each `RowWidget` on the main path — so **layout math uses one vertical centerline** for that stack.
- The **mascot** is drawn in **`CardFrame.paintEvent`** only; it is **not** a layout item, so it **does not** move the `QVBoxLayout` geometry — but it can change **optical** balance (heavy detail top-right while the text column is mathematically centered).

**Conclusion:** English **left/right margins are still symmetric**; there is **no** hidden “nudge all content right by a few px” margin hack. The main column is explicitly **`AlignHCenter`**. Together with the **historical baseline** (older UI = **left pillar**), today’s “shifted right vs memory” is **largely expected** when comparing to that screenshot — not only mascot **optics**. Remaining work: **title vs cat** (width / mascot slot, see §8 proposal) and, if product wants the **old** feel, **restore left-pillar alignment** for main (e.g. `AlignLeft` + consistent left inset) instead of only tweaking margins. Pin the commit where centering landed with **`git log -p -- tm_app.py`** (search `AlignHCenter`, `_set_main_rows_layout_alignment`, `addWidget` for title/rows).

**Relevant code (for later fixes):**

| Area | File | Detail |
|------|------|--------|
| Title slot width & alignment | `tm_app.py` | `_apply_title_slot_main`: `title_label.setFixedWidth(BAR_W)`; label left-aligned in slot; slot horizontally centered in `card_layout`. |
| Card margins (per language) | `tm_resources.py` | e.g. English `LANGUAGE_LAYOUTS["en"]["card_margins"] = (10, 16, 10, 1)`. |
| Vertical balance (main vs focus/celebration) | `tm_app.py` | `_set_card_vertical_balance`, stretch insertion on `card_layout` — can change perceived vertical placement of the block when entering/leaving focus or celebration. |
| Row / body horizontal alignment | `tm_app.py` | `_set_main_rows_layout_alignment` — aligns `focus_body` and row widgets in `card_layout`. |
| Row / bar geometry | `tm_ui.py` | `RowWidget` (e.g. bar width `BAR_W`, inner layouts). |
| Mascot paint position | `tm_ui.py` | `CardFrame.paintEvent`: `drawPixmap(self.width() - self.top_pixmap.width() - 4, 9, ...)`. |
| Mascot size | `tm_app.py` | `load_pixmap(..., 31)` — height 31 px. |

**Likely causes (hypothesis):** (1) Title tied to `BAR_W` and centered can crowd the mascot band (see earlier note). (2) **Functional block** oddness may combine **vertical stretch behavior**, **label left-align vs bar geometry inside `RowWidget`**, and **optical weight** of the painted mascot vs a narrow centered column — **not** from asymmetric **English** left/right margins (those are symmetric). (3) Any true horizontal drift vs an older revision should be confirmed with **git diff** on layout constants.

**Possible directions when fixing:** Reconcile English margins and title width with mascot reserve; audit main vs focus vs post-celebration paths so default main layout matches baseline; compare row/column alignment to Chinese baseline (`docs/requirements.en.md`).

---

## 中文：英文主卡布局观感异常（标题与小猫 + 整体功能区）

**状态：** 待处理 — 本文仅作记录，不包含布局修改。

**现象：**

1. **标题与小猫：** 英文主界面下，**Time Master** 最后一笔（**r**）与右上角小猫几乎贴在一起；用户反馈此前观感正常，近期布局调整后变差。
2. **整体功能区位置：** 不单是 **r** 与小猫的问题——**整块主功能区**（标题、各行文案与进度条、相关控件在视觉上形成的整体）相对以前的版本，**水平/垂直上的位置也像是被挪过**，在卡片上显得**不协调、奇怪**，与记忆中的「对的样子」不一致。
3. **整块略偏右（新截图）：** 用户观感：中间一列（标题 + 四行）相对圆角卡片**整体略靠右**，**左侧留白大于右侧**。

**历史基线（用户标注：图1 = 之前，图2 = 现在；仓库内已存图）：** **图1** 见 `docs/reference-main-layout-before.png`：**左柱布局**，标题与四行+进度条**左缘对齐**，卡片内**右侧留白更大**。**图2** 见 `docs/reference-main-layout-current.png`：**整列居中**，左右留白更对称、进度条更接近卡片水平中线。当前代码主路径对标题与各行使用 **`AlignHCenter`**，故「相对图1像往右挪」**主要是「左柱 → 居中列」的策略变化**，再叠小猫/标题过近等观感。

**代码核查 — 主界面水平方向（仅查阅、未改代码）：**

- 英文 **`LANGUAGE_LAYOUTS["en"]["card_margins"]`** 为 `(10, 16, 10, 1)`，**左右均为 10**，布局上**没有**故意做「左窄右宽」或整体右移的左右不对称（**中文** `(7, 9, 11, 4)` 才是左右不同：左 7、右 11）。
- `tm_app.py` 中 **`title_label`、`focus_body`、`day_row`、`month_row`、`year_row`** 在 **`card_layout`** 里均以 **`AlignHCenter`** 加入，主路径宽度均为 **`BAR_W`（110）** —— 几何上**共用同一竖直中线**。
- **小猫**仅在 **`CardFrame.paintEvent`** 绘制，**不参与** `QVBoxLayout` 排布；不会改变列的几何中心，但会加强**右上视觉重量**，容易让人觉得「内容偏左/偏右」与真实中线不一致。

**结论：** 英文左右边距仍**对称**；主列在代码里是明确的 **`AlignHCenter`**。结合**旧版左柱布局**的截图，当前「相对记忆偏右」**主要是对齐策略从靠左改为居中**，不只有小猫造成的**光学错觉**。若产品要**恢复旧版靠左柱**的观感，应在主界面改**水平对齐策略**（例如主列 `AlignLeft` + 统一左内边距），而不是只微调 `card_margins`。标题与猫仍可按文档后续方向（加宽标题槽 / §8 布局占位等）处理。居中改动落在哪次提交可用 **`git log -p -- tm_app.py`** 搜 `AlignHCenter`、`_set_main_rows_layout_alignment`、`addWidget` 等定位。

**相关代码：** 见上表；整体位置还与 **`card_layout` 内居中与拉伸**、**主界面与专注/庆祝态切换** 等有关，排查时宜对照中文基线与历史截图或提交记录。

**可能原因（推测）：** （1）标题槽与 `BAR_W` 绑定并居中，易与 mascot 区域抢水平空间。（2）功能区观感异常更多来自 **垂直 stretch**、**行内左对齐文案与进度条几何**、**绘制型装饰不参与布局** 等叠加；**英文左右边距本身是对称的**，不宜再归因于「英文 card_margins 左右不对称」。（3）若与历史版本有像素级差异，用 **git diff** 核对常量。

**后续修复时可考虑：** 为英文单独预留标题/右侧安全区、核对主界面默认态与专注/庆祝退出后是否恢复一致、与中文布局基线对齐（见 `docs/requirements.zh-CN.md`）。

---

## EN: Progress bars missing after focus celebration → Continue (main view)

**Status:** Open — reproduced from UI screenshot after completing a focus session, tapping **Continue** (tap gate), returning to the normal main card.

**Symptom:** Only **one** progress bar (typically the **year** row) remains visible; the bars for **target / today / month** rows appear **gone**. Labels and copy look like the normal main screen, but the upper rows lack their bars; **large empty area** at the bottom of the card may also look like the block shifted upward.

**Relevant code:**

| Area | File | Detail |
|------|------|--------|
| Celebration hides bars on three rows | `tm_app.py` | `_render_celebration`: `set_bar_visible(False)` on `target_row`, `day_row`, `month_row` (lines ~326–337). |
| Year row during celebration | `tm_app.py` | `_render_celebration`: `year_row.setVisible(False)` — year row is not given `set_bar_visible(False)`. |
| Return to main | `tm_app.py` | `_exit_focus_celebration` → `_reset_row_widgets_default` → each row `reset_row_style()`. |
| Row reset vs bar visibility | `tm_ui.py` | `RowWidget.reset_row_style` sets `self.bar.setVisible(True)` only; it does **not** set `self._bar_row.setVisible(True)`. |
| Hide path | `tm_ui.py` | `set_bar_visible(False)` hides **both** `self.bar` and `self._bar_row`. |

**Root cause (confirmed in code):** After celebration, `reset_row_style()` turns the inner `ProgressBar` visible again but leaves **`_bar_row` hidden** because `set_bar_visible(False)` hid the container. The **year** row never had `set_bar_visible(False)` in celebration, so its bar row still shows — matching “only the last bar visible”.

**Fix direction (when implementing):** In `reset_row_style`, also show `_bar_row` (e.g. `self._bar_row.setVisible(True)`), or call `self.set_bar_visible(True)`, or mirror the two-widget contract of `set_bar_visible` — so exiting celebration fully restores bar chrome for all rows.

---

## 中文：专注完成庆祝后点「继续」回到主界面，多行进度条丢失

**状态：** 待处理 — 有截图：完成一次 **Focus** 后，在庆祝/轻触继续界面点击继续，回到**主界面**时，**多行进度条不见了**。

**现象：** 文案已恢复为正常的 Target / Today / Month / Year 四行，但上面几行的**进度条不显示**，往往只剩**最后一行（本年）**一条进度条；卡片**下半大块空白**，整体也像被顶上去。

**相关代码：** 见上表。庆祝态 `_render_celebration` 对前三行调用了 `set_bar_visible(False)`；`year_row` 在庆祝时被 `setVisible(False)`，**没有**对年行调 `set_bar_visible(False)`。退出庆祝时 `_reset_row_widgets_default` → `reset_row_style()` 只把 **`bar`** 设为可见，**没有**恢复 **`_bar_row`**，与 `set_bar_visible(False)` 隐藏整行条带的行为不对称。

**根因（代码已核对）：** `set_bar_visible(False)` 同时隐藏了 `bar` 和 `_bar_row`；`reset_row_style` 只恢复了 `bar`，**容器 `_bar_row` 仍为隐藏**，故前三行条带不显示；年行未走 `set_bar_visible(False)`，故仍能看到一条 — 与截图一致。

**修复方向：** 在 `reset_row_style` 中一并恢复 `_bar_row` 可见性，或统一改为调用 `set_bar_visible(True)`，保证退出庆祝后主界面四行条带全部恢复。

---

## EN: Focus session screen — title not centered; progress bar missing

**Status:** Open — from screenshot: active focus view (“Focus” + countdown + “Stop focus”), English.

**Symptoms:**

1. **Title:** The **Focus** title sits **high and toward the left**, not **visually centered** on the card; user expects it centered like the countdown/button block (and per earlier layout goals).
2. **Progress bar:** **No** countdown progress bar is visible under the remaining time line, though the product intent was a **narrow, centered** bar for focus.

**Relevant code:**

| Area | File | Detail |
|------|------|------|
| Focus branch | `tm_app.py` | `refresh_rows` when `_focus_active`: sets `title_label` text to `title_focus`, configures `target_row` only; **returns early** (~517) without calling `_apply_title_slot_main()` (still uses main title slot: fixed `BAR_W`, **left**-aligned label in a horizontally centered slot — short “Focus” reads as **off-center left**). |
| Title alignment in focus | `tm_app.py` | Focus path sets `target_row.set_label_text_alignment(HCenter)` but **does not** change `title_label` alignment for focus-only centering. |
| Bar on `target_row` | `tm_app.py` | Focus path calls `target_row.reset_row_style()` then `set_row(..., prog)` — does **not** call `set_bar_visible(True)`. |
| Shared visibility bug | `tm_ui.py` | If `target_row` previously had `set_bar_visible(False)` (celebration), `reset_row_style()` still does not restore **`_bar_row`** → bar area stays hidden in focus (same mechanism as post-celebration main view). |

**Likely causes:** (1) **Title:** Main-window title uses `_apply_title_slot_main` (left text in centered narrow slot); focus branch never switches title to true center alignment. (2) **Bar:** Either the **`_bar_row` / `reset_row_style`** gap after celebration, or focus branch should **explicitly** `set_bar_visible(True)` after any state that hid bars.

**Fix direction:** For focus mode, center `title_label` text (or add a focus-specific title layout); ensure `target_row.set_bar_visible(True)` and/or fix `reset_row_style` so `_bar_row` is always shown when returning to any mode that needs a bar.

---

## 中文：专注进行中界面 — 「Focus」标题未居中；无进度条

**状态：** 待处理 — 截图：英文专注中界面（标题 **Focus**、剩余时间文案、**Stop focus** 按钮）。

**现象：**

1. **标题：** **Focus** 偏左上，在卡片上**没有视觉居中**；与中间倒计时、按钮的居中感不一致，也与此前「专注页布局」目标不符。
2. **进度条：** 剩余时间下方**看不到**专注**进度条**（预期为相对内容区**收窄、居中**的条）。

**相关代码：** 见上表。`refresh_rows` 在专注态**提前 return**，未再次调用 `_apply_title_slot_main`；标题槽仍是主界面那套（`BAR_W` 槽居中、槽内文字**左对齐**），短词 **Focus** 会显得**靠左**。专注行只调了 `target_row` 的标签居中，**未**单独处理顶层 `title_label`。进度条若 `target_row` 曾在庆祝态被 `set_bar_visible(False)`，则与已知 **`reset_row_style` 未恢复 `_bar_row`** 的问题同源，专注态也会**整条不显示**。

**修复方向：** 专注态单独把标题设为居中（或专用布局）；进入专注时确保 **`set_bar_visible(True)`** 并修复 **`reset_row_style`** 对 **`_bar_row`** 的恢复，避免从庆祝/其他态带入隐藏条带。

---

## EN: Focus completion (“Completed”) screen — tap hint gone; copy overlaps; not vertically centered

**Status:** Open — from screenshot: post-focus celebration card (“Completed”, confetti, **Round …** / **Nice work!** / **Today …**).

**Symptoms:**

1. **“Tap to continue” missing / unreadable:** The expected hint (`celebration_tap_hint` — e.g. **Tap to continue**) does not read as a separate prompt; user sees only a faint, clipped, or merged fragment (e.g. **“continue”**) overlapping other lines instead of a clear call-to-action.
2. **Overlapping celebration copy:** Lines such as **Today …** and the tap hint **stack on the same vertical band** — text **collides** instead of clear spacing.
3. **Vertical centering not met:** The **whole functional block** (session summary + praise + today subline + tap affordance) sits **too low** on the card; large empty space above and content **not** visually centered in the card body. **“Completed”** also crowds the top-right kitten (same family as main-title vs mascot issue).

**Relevant code:**

| Area | File | Detail |
|------|------|--------|
| Celebration layout | `tm_app.py` | `_render_celebration`: `_set_card_vertical_balance(True, top_ratio=2, bottom_ratio=1)`, `card_layout.setSpacing(5)`, `month_row.setContentsMargins(0, 0, 0, 10)` — pulls block **upward** in stretch terms but final geometry still depends on row heights + overlay. |
| Tap overlay | `tm_ui.py` | `ClickToResumeOverlay.set_pick_mode`: **transparent** full-card overlay; hint label **small** (8 pt), **muted** color, `AlignBottom` in `QVBoxLayout` with bottom margin `28`; full card remains **clickable**. |
| Z-order | `tm_app.py` | After `_render_celebration`, `tap_gate.raise_()` and `update_pick_hint_geometry()` — hint competes visually with **focus_body** rows occupying the **lower** part of the card. |
| Title | `tm_app.py` | Same `title_label` / `_apply_title_slot_main` width as main — **Completed** long word + right mascot. |

**Likely causes:** (1) **Hint:** Transparent overlay + bottom-anchored tiny label **shares the same region** as the last celebration row (`month_row` “Today …”), so text **overdraws**; wrap/max-width or margin may clip “Tap to” leaving **“continue”**. (2) **Vertical balance:** Asymmetric stretch (**2:1**) plus row spacing/margins does not match the intended **optical center** of the celebration block; needs layout pass vs design mockup.

**Fix direction:** Reserve a **dedicated band** for the tap hint (extra bottom margin on `focus_body`, or move hint outside row stack); increase hint contrast/size or non-transparent footer; re-tune `_set_card_vertical_balance` / margins for true vertical balance; optionally widen title slot for **Completed** vs cat.

---

## 中文：专注完成庆祝页（「已完成 / Completed」）— 轻触继续缺失；文案重合；未垂直居中

**状态：** 待处理 — 截图：庆祝态（彩屑、**Round …**、**Nice work!**、**Today …** 等）。

**现象：**

1. **「Tap to continue / 轻触继续」没了或看不清：** 预期底部提示不明显，只剩与正文**叠在一起**的浅色碎片（如 **continue**），不像独立操作提示。
2. **功能区文字重合：** **Today …** 与底部提示在**同一竖条区域**叠画，行距失效、**互相遮挡**。
3. **没有做到垂直居中：** 整块庆祝内容（三轮文案 + 提示）整体**偏下**，上方空一大块，**视觉重心不在卡片中部**；标题 **Completed** 与右上角小猫仍**过近**（与主界面标题问题同类）。

**相关代码：** 见上表。`ClickToResumeOverlay` 在 `set_pick_mode` 下为**全卡透明**点击层，提示为小号、muted、**底部对齐**，与 `_render_celebration` 里最后一行 `month_row` 的「今日累计」极易**同区重叠**；垂直方向由 **`_set_card_vertical_balance(2:1)`**、行间距、`month_row` 底边距等共同决定，当前与「整块垂直居中」目标不一致。

**修复方向：** 为底部提示**单独留白或独立控件**，避免与 `month_row` 同层同带；提高提示可读性；重做庆祝态垂直分配并对照设计稿；标题与 mascot 预留与第一节一致处理。

---

## EN: Proposed — dedicated layout slot for top-right mascot (record only, no code yet)

**Status:** **Documentation only** — user asked **not** to implement this change yet.

**Goal:** Give the top-right cat a **real layout cell** (e.g. fixed-size `QLabel` / `QWidget` with pixmap in a **header `QHBoxLayout`**) instead of **only** drawing it in `CardFrame.paintEvent` (`tm_ui.py`). The layout engine then **knows** how much horizontal (and vertical) space the mascot reserves, which reduces **title vs cat** crowding and **optical vs geometric** mismatch (see issue §1 investigation). **Swapping the image asset** later becomes “set pixmap on the slot widget” plus optional constants, not fragile paint math.

**Sketch for a future change:** e.g. top row `[stretch][title][stretch][mascot]` so title stays centered in the band **excluding** the mascot column; tune **top/right insets** to match today’s paint (`~4 px` from card right, `~9 px` from top — as constants in `tm_resources.py`); then **remove** mascot drawing from `CardFrame.paintEvent` and stop assigning `card.top_pixmap`; raise **`title_header`** (or equivalent) with fireworks/tap z-order as today’s `title_label.raise_()`.

---

## 中文：拟议 — 小猫改为布局内专用占位（仅记录，尚未改代码）

**状态：** **只写入文档** — 用户要求**先不要改代码**。

**目的：** 将右上角小猫从**仅 `CardFrame.paintEvent` 绘制**改为在**布局里占固定一格**（例如顶栏 **`QHBoxLayout` + `QLabel` 显示位图**）。这样排版时就有**明确的 mascot 区域**，标题与装饰不会在几何上「假装互不重叠」；之后**替换图片**只需换该控件的 **pixmap**（或换资源路径），用常量微调边距即可，而不必改手写绘制坐标。

**实现草图（供后续 PR）：** 顶行如 **`[stretch][标题][stretch][mascot 槽]`**，标题在**扣除猫列宽度后的中间带**内居中；右/上与现 **`drawPixmap(width - w - 4, 9, …)`** 对齐后删除 **`paintEvent`** 中的猫绘制，并去掉 **`card.top_pixmap`** 赋值；烟火/轻触层的 **`raise_()`** 改为针对整块顶栏容器。当前源码**未做**上述改动。
