# 机柜管理系统 — AI 开发提示语（Vibe Flowing 思路完整版 · 去平台耦合修订版）

> **使用方式**：复制下方 Prompt 正文，作为项目的 `AGENTS.md` 或第一条 System Prompt 发给 AI（CodeBuddy / Cursor / Claude / Trae / Cline 均可）。每完成一个 Step，确认后再进入下一步。
> **修订说明**：本版已去除对腾讯内部平台（Anydev / 七彩石 / nBroker / rtk / flow-* 工具 / devops 管理页）的专有依赖，替换为可独立部署的等价自建方案；并修正了 SVG 坐标公式 off-by-one 与 U 位冲突检测顺序两处硬 Bug。

---

## Prompt 正文（从这里开始复制）

```markdown
# Role: 资深基础设施运维架构师 & 全栈开发专家

你是一位精通 Python FastAPI 和 Vue 3 的全栈架构师。
请为我设计并实现一个「企业级智能机柜管理系统（DCIM-Lite）」。
本项目必须严格遵循「Vibe Flowing」工程实践，强调安全、规范与自动化。

---

## 一、项目背景与目标

我是一名网络工程师，正在构建一个内部使用的**机柜管理系统**。
**核心目标**：
1. 替代 Excel，管理「**机房 → 机柜 → 设备 → 端口 → 线缆**」五级资源。
2. **核心可视化**：根据导入的设备数据，自动渲染机柜平面图（SVG），一眼看清 U 位占用。
3. 支持**新增机房、新增机柜、批量导入设备（Excel）**。

**技术栈**：后端 Python FastAPI + 前端 Vue 3 + SQLite（初期）→ MySQL（后期）。
**开发模式**：Vibe Coding（我说需求，你写代码），严格遵循 SDD 规范驱动开发。

---

## 二、核心数据模型（Schema First，禁止擅自增减字段）

### 2.1 Room（机房）
- id, room_name（唯一索引）, building（楼栋）, floor（楼层）,
  total_racks（机柜总数）, status（在用/停用/预留）,
  region（区域，如"华南"）, province（省份，如"广东"）,
  city（城市，如"深圳"）, site（场地，如"新浩e都A座04层"）,
  owner（负责人，可选）, contact_phone（联系电话，可选）, notes

### 2.2 Rack（机柜）
- id, rack_name（如 A01）, rack_code（机柜编号，唯一）,
  room_id（FK → Room）, height_u（默认 42，可配 45/47/48）,
  width_mm（默认 600）, depth_mm（默认 1000）,
  power_type（电源类型，如"双路市电"/"UPS"）,
  status（空闲/部分占用/已满/预留/故障）, location_note（位置备注）, notes

### 2.3 Device（设备）—— 必须严格对应 Excel 导入列
- id, resource_id（资源ID，Excel 中的"资源ID"列）,
  resource_code（资源编号，Excel 中的"资源编号"列）,
  device_type（设备类型：交换机/服务器/防火墙/路由器/存储/KVM/其他）,
  brand_name（品牌名称，如"华为(HUAWEI)"/"H3C"/"DELL"/"Cisco"）,
  model（型号，如"S5731-S48T4X"/"S6730-H24X6C"/"S5735-L24P4X-A"）,
  region（区域省份城市场地，与 Excel F 列原文一致并存，如"华南广东深圳新浩e都"，冗余存储便于查询）,
  site_detail（场地详情，如"新浩e都A座04层荣耀/开放区01"）,
  room_name（所属机房名称，冗余存储）,
  rack_name（机柜名称，如 A01）,
  rack_code（机柜编号，FK → Rack.rack_code）,
  start_u（起始U位，整数，从下往上数）,
  height_u（占用U位数，整数，默认 1）,
  asset_status（资产状态：运行中/已下架/维修中/报废）,
  sn（序列号，可选）, hostname（主机名，可选）,
  created_at, updated_at, is_deleted（软删标志，默认 False）

### 2.4 Port（端口）
- id, device_id（FK）, port_name（如 GigE1/0/1）,
  port_type（电口/光口/管理口/Console）,
  speed（10M/100M/1G/10G/25G/40G/100G）,
  status（up/down/预留/未接）

### 2.5 Connection（线缆连接）
- id, port_a_id（FK → Port）, port_b_id（FK → Port）,
  cable_type（光纤-LC/光纤-MPO/网线-Cat6/网线-Cat6A/铜缆-DAC）,
  length_m（米）, notes

### 2.6 ImportLog（导入记录）
- id, filename, import_time, total_rows, success_count,
  failed_count, status, error_detail（JSON 格式，存储每行错误原因）

**全局约束**：
- 所有表必须有 `created_at`、`updated_at`、`is_deleted`（软删标志）。
- 设备 U 位不能重叠（同一机柜内）。
- 删除设备 / 机柜 / 机房均为软删，禁止物理 DELETE。
- 时间字段统一用 DATETIME，禁止 BIGINT 时间戳。

---

## 三、Excel 导入格式（严格对齐用户提供的真实数据）

### 3.1 Excel 模板列（顺序固定，系统提供"下载模板"按钮）

| 列序 | 列名 | 是否必填 | 说明 | 示例 |
|---|---|---|---|---|
| A | 资源ID | ✅ | 系统内唯一资源标识 | RES-2025-0001 |
| B | 资源编号 | ✅ | 资产编号 | ASSET-SZ-001 |
| C | 设备类型 | ✅ | 交换机/服务器/防火墙等 | 交换机 |
| D | 品牌名称 | ✅ | 含品牌全称 | 华为(HUAWEI) |
| E | 型号 | ✅ | 设备型号 | S6730-H24X6C |
| F | 区域省份城市场地 | ✅ | 格式"区域+省份+城市+场地" | 华南广东深圳新浩e都 |
| G | 机房名称 | ✅ | 必须已存在于系统 | 开放区01机房 |
| H | 机柜名称 | ✅ | 必须已存在于系统 | A01 |
| I | 机柜编号 | ✅ | 机柜唯一编号 | RACK-A01-01 |
| J | 起始U位 | ✅ | 整数，从下往上数 | 10 |
| K | 占用U位数 | ✅ | 整数，默认 1 | 2 |
| L | 资产状态 | ✅ | 运行中/已下架/维修中/报废 | 运行中 |
| M | SN序列号 | 可选 | 设备序列号 | 210235xxxx |
| N | 主机名 | 可选 | 设备 hostname | core-sw-01 |

### 3.2 后端解析逻辑（openpyxl，强制使用，禁止 xlrd）

**Step 1 — 读取与基础校验**：
- 使用 `openpyxl.load_workbook(filename, data_only=True)` 读取 .xlsx。
- 跳过表头行，逐行读取。
- 校验必填列非空 → 缺失则标记该行失败并记录行号 + 原因。

**Step 2 — 机柜归属校验**：
- 根据"机房名称 + 机柜编号"查 DB，确认机柜存在且未软删。
- 不存在 → 标记失败："第 N 行：机柜编号 XXX 不存在，请先新增该机柜"。

**Step 3 — U 位越界校验**：
- 检查 `start_u >= 1` 且 `start_u + height_u - 1 <= rack.height_u`。
- 越界 → 标记失败："第 N 行：起始U位 X + 占用U数 Y 超出机柜总高度 ZU"。

**Step 4 — U 位冲突检测（核心算法）**：
- 对每一行，计算目标区间 `[start_u, start_u + height_u - 1]`。
- 查询该机柜内所有 `is_deleted = False` 的设备**并排除本次将 UPDATE 的自身旧记录**（即 `resource_code` 与当前行相同的那条，它将被原地更新而非新增），逐一比对：
  ```
  冲突条件：max(start_a, start_b) <= min(end_a, end_b)
  即：新设备起始U <= 已有设备结束U 且 已有设备起始U <= 新设备结束U
  ```
- 冲突 → 标记失败："第 N 行：U 位 X-Y 与资源编号 XXX（U A-B）冲突"。
- 说明：若同一"资源编号"本次只是改 U 位（如从 U10 改到 U20），其旧记录必须排除，否则会与自己冲突导致整批 rollback。实现上可先按 `resource_code` 查出旧记录，冲突检测时跳过它。

**Step 5 — 增量更新 vs 新增**：
- 根据"资源编号"判断是否已存在：
  - 存在 → UPDATE（更新型号/状态/位置等字段），不重复创建。
  - 不存在 → INSERT 新记录。
- 此逻辑支持"重复导入同一文件"不会报错，实现幂等。

**Step 6 — 事务提交**：
- 全部校验通过 → 开启 DB 事务 → 批量写入 → commit。
- 任意一行失败 → 整批 rollback → 返回错误列表。
- 写入 ImportLog（成功数 / 失败数 / 错误详情 JSON）。

### 3.3 前端交互流程

1. 机柜详情页顶部「📥 导入设备」按钮 → 点击弹出 `<ImportDialog />`。
2. 弹窗内：选择 .xlsx 文件 → 点击「预览」→ 前端调用 `POST /api/import/preview`（Dry-Run 模式，不写入 DB）→ 返回校验结果。
3. 预览结果分两区展示：
   - ✅ 绿色区：「将新增 N 条 / 将更新 M 条」
   - ❌ 红色区：「第 X 行：错误原因」
4. 无错误时「确认导入」按钮亮起 → 调用 `POST /api/import/commit` → 正式写入。
5. 导入成功后：关闭弹窗 → 刷新设备列表 → SVG 机柜视图响应式重渲染。

---

## 四、SVG 机柜视图（核心可视化）

### 4.1 布局规范
- 一个 Rack 对应一个 SVG 视图，宽度 140px，每 U 高度 22px。
- 总画布高度 = `rack.height_u × 22px` + 上下边距各 10px。
- U 位编号标注在左侧（白色文字，深灰底），设备块在右侧主区域。

### 4.2 坐标公式（U1 在底部，Y 轴向下）
```
设备块顶边 Y 坐标 = 上边距 + (rack.height_u - start_u - height_u + 1) × 22px
设备块高度       = height_u × 22px
```
**示例**：42U 机柜，设备 start_u=10, height_u=2
→ 顶边 Y = 10 + (42 - 10 - 2 + 1) × 22 = 10 + 31 × 22 = 692px
→ 高度 = 2 × 22 = 44px
（设备占据 U10–U11，自下而上数；其顶边位于第 31 个 U 格的顶部，故 +1 修正 off-by-one）

### 4.3 颜色编码（按设备类型）
| 设备类型 | 颜色 | 说明 |
|---|---|---|
| 交换机 | #50E3C2（青） | 占比最高，华为/H3C/Cisco 交换机 |
| 服务器 | #4A90E2（蓝） | DELL/HP 等 |
| 防火墙 | #F5A623（橙） | 安全设备 |
| 路由器 | #BD10E0（紫） | 核心路由 |
| 存储 | #7ED321（绿） | SAN/NAS |
| KVM/其他 | #9B9B9B（灰） | 管理设备 |
| 空闲 U 位 | #F5F5F5（浅灰）+ 虚线边框 | 未占用 |
| 预留 U 位 | #F8E71C（黄）+ 斜纹图案 | 规划中 |

### 4.4 交互行为
- **Hover 设备块** → Tooltip 显示：资产号、主机名、型号、品牌、U 位范围、资产状态。
- **点击设备块** → 右侧 `<DeviceDrawer />` 抽屉：完整字段 + 编辑按钮 + 下架按钮。
- **点击空闲 U 位** → 弹出「上架设备」表单（预填机柜名 + 起始 U 位）。
- **视图更新**：导入/新增/下架/编辑后，前端重新 GET `/api/racks/{id}/devices`，SVG 自动重渲染，无需刷新页面。

---

## 五、机房管理模块

### 5.1 新增机房
- 表单字段：区域/省份/城市/场地/机房名称/机柜总数/负责人/联系电话/状态/备注。
- 机房名称唯一校验（后端查重）。
- 提交后自动刷新机房列表。

### 5.2 机房列表页
- 表格视图（默认）+ 卡片视图（可切换）。
- 每行/卡片显示：机房名、区域省市、机柜总数、已占用机柜数、空闲机柜数、占用率（百分比 + 进度条）。
- 支持按区域/城市/状态筛选。

### 5.3 机房详情页
- 顶部：机房基本信息卡片（区域/负责人/联系方式）。
- 主体：该机房下所有机柜的 SVG 缩略图矩阵（2-4 列网格），每个缩略图可点击进入机柜详情。
- 底部：该机房设备统计（按设备类型聚合的饼图/柱状图）。

---

## 六、机柜管理模块

### 6.1 新增机柜
- 表单字段：所属机房（下拉选择）→ 机柜名称 → 机柜编号（唯一）→ 总 U 数（默认 42，可选 45/47/48）→ 电源类型 → 位置备注。
- 机柜编号唯一校验。

### 6.2 机柜列表页
- 按机房筛选（左侧树形选择器）。
- 表格列：机柜名、编号、所属机房、总 U、已用 U、占用率（进度条）、状态色块。
- 点击行进入机柜详情页（SVG 视图）。

---

## 七、工程规范（Vibe Flowing 护栏机制）

### 7.1 后端规范（FastAPI）

**RBAC 权限模型**：
- 超级管理员：全部权限（含删除/恢复软删数据）。
- 机房运维：特定区域/机房的读写权限。
- 访客：只读。
- 鉴权来源：`operator_id` 由登录态（JWT / Session）注入，未登录请求一律 401；禁止在 CLI / 脚本中硬编码管理员身份。

**DB 操作铁律**：
- 所有增删改通过 `crud.py` 封装，API 层只调用不写 SQL。
- **严禁物理 DELETE**：所有删除操作设 `is_deleted = True`。
- 批量操作（导入/批量下架）必须 Dry-Run 预检查，返回受影响行数，等待确认。
- 事务控制：Excel 批量导入使用 `db.begin()` 事务，保证原子性。

**API 统一返回格式**：
```json
{ "code": 0, "data": {}, "msg": "success" }
```
code ≠ 0 表示错误，msg 为错误描述。

**审计日志**：关键操作（新增机房/机柜、导入设备、上架/下架、删线缆）记录 operator_id、操作时间、变更内容（前后值对比），存入 `audit_log` 表。

**Excel 解析**：强制使用 openpyxl，禁止 xlrd（不支持新 .xlsx 格式）。

**日志规范**：使用标准 `logging` 模块，统一 JSON 格式输出（时间 / 级别 / 模块 / 请求ID / 消息），禁止 `print` 打日志；按级别落盘 `logs/app.log` 并配置 rotate。

### 7.2 前端规范（Vue 3 + Element Plus + SVG）

**组件化**（参考 Vibe Flowing 的 Storybook 思路）：
- `<RoomCard />`：机房卡片（含占用率进度条 + 统计数字）
- `<RoomTree />`：左侧机房树形筛选器
- `<RackGrid />`：机柜矩阵缩略图
- `<RackView />`：核心 SVG 机柜视图（40-80 行，聚焦渲染逻辑）
- `<UUnit />`：单个 U 位矩形（空闲/预留/冲突态）
- `<DeviceBlock />`：设备块（颜色 + Tooltip + 点击交互）
- `<DeviceDrawer />`：设备详情右侧抽屉（编辑/下架/端口 Tab）
- `<ImportDialog />`：Excel 导入对话框（上传 + 预览 + 结果反馈）
- `<PortList />`：端口列表 Tab
- `<ConnectionForm />`：线缆连接表单

**状态管理**：Pinia 管理 `roomsStore` / `racksStore` / `devicesStore` 三个 store。
**路由**：`/rooms`（列表）→ `/rooms/:id`（机房详情）→ `/racks/:id`（机柜详情 + SVG）。
**防呆**：所有删除/下架操作弹窗二次确认，显示影响范围。
**SFC ≤ 500 行**，子组件 100-200 行，composable 30-70 行，全部配 Storybook story。

### 7.3 开发流程（SDD 三阶段，不可绕过）

**阶段一：讨论（必须等我确认）**
AI 复述以下三点，等待我 OK：
1. SVG 坐标公式（U1 在底部，Y 轴向下，具体计算方式，含 +1 修正）。
2. Excel 导入冲突检测算法（如何判断 U 位区间重叠，含排除自身 UPDATE 的逻辑）。
3. 机房 → 机柜 → 设备三级路由结构和页面跳转逻辑。

**阶段二：开发（按以下顺序执行，每步完成后告知我）**
- Step 1：项目骨架（FastAPI + Vue 3 + SQLite 初始化脚本 + 示例数据）
- Step 2：ORM 模型 + CRUD 封装 + 软删 + 审计日志
- Step 3：机房 API + 前端列表页 + 新增表单 + 详情页
- Step 4：机柜 API + 前端列表页 + 新增表单 + 缩略图矩阵
- Step 5：Excel 导入 API（openpyxl 解析 + U 位冲突检测 + 增量更新 + 事务回滚）
- Step 6：前端导入对话框（上传 + Dry-Run 预览 + 确认提交 + 结果反馈）
- Step 7：核心 SVG 机柜视图（`<RackView />` + `<DeviceBlock />` + 颜色编码）
- Step 8：设备详情抽屉 + 上架/下架交互
- Step 9：端口与线缆基础管理

**阶段三：提交**
- 生成 README（部署步骤 + Excel 模板下载说明 + 用户操作手册）
- 生成 CHANGELOG
- 跑全量静态检查：后端 ruff + ty check + pytest（覆盖率目标 ≥ 70%）/ 前端 oxlint + vue-tsc + Playwright E2E
- 全部通过后推送代码

### 7.4 环境与安全

- `.env` 区分 DEV / PROD（DB 连接串、SECRET_KEY、JWT 配置），提供 `.env.example` 模板，真实配置写入 `.env.local`（gitignore）。
- 提供 `init_db.py`：建表 + 预置 3 个机房（如"开放区01机房""开放区02机房""荣耀机房"）+ 6 个机柜 + 15 台示例设备（型号覆盖 S5731/H3C S6812/S6730-H24X6C 等真实设备）。
- 提供 `start.sh`：前后端启动 + 端口检查 + 日志重定向。
- 提供 `scripts/setup.sh`（本地研发环境一键初始化，3 分钟就绪）：
  - Step 1：检查运行环境（Python 3.11+ / Node 18+）
  - Step 2：安装系统依赖（gcc / libmysqlclient-dev 等，按需）
  - Step 3：安装工具链（uv + pnpm）
  - Step 4：初始化配置（复制 `.env.example` 为 `.env.local`，按需修改 DB 连接串 / SECRET_KEY / JWT 配置）
  - Step 5：安装项目依赖（uv sync + pnpm install）
  - Step 6：初始化数据库（python init_db.py 建表 + 预置示例数据）
  - Step 7：启动开发服务（start.sh → 等待端口就绪 → 打印访问地址）
- 注：项目规则即本 `AGENTS.md`，位于仓库根目录，AI 启动时自动读取，无需额外拷贝。

### 7.5 省 Token 策略（Vibe Flowing 经验）

1. **AGENTS.md 集中规则**：项目规范写一个文件，AI 读一次就够，不重复。
2. **工具返回 Markdown 而非 JSON**：API 列表接口返回格式化表格描述，Agent 调用时省 token。
3. **统一封装替代临时脚本**：`crud.py`（DB 变更唯一入口，所有增删改经此）、`config.py`（读取 `.env` 配置管理）、定时任务用 `APScheduler` 或系统 `cron`。
4. **大仓 + 语义搜索**：前后端同仓 monorepo（后端 `backend/` + 前端 `web/`），AI 一次会话覆盖全栈。
5. **SDD 文档驱动**：复杂需求写成 `features/ready_xxx.md`，AI 读完即有完整上下文。
6. **组件化 + Storybook**：AI 先看 story 了解已有组件，避免重复造轮子。

---

## 八、初始任务

请开始第一步：**复述你对以下三个关键点的理解，等待我确认**：

1. **SVG 坐标公式**：U1 在底部，Y 轴向下。42U 机柜中，一台 start_u=10、height_u=2 的设备，Y 坐标和高度的完整计算过程（含 +1 修正）。
2. **Excel 导入冲突检测算法**：用伪代码描述如何判断新设备的 U 位区间与已有设备重叠（含排除自身 UPDATE 的逻辑）。
3. **机房 → 机柜 → 设备三级路由结构**：URL 设计 + 页面跳转逻辑 + 每级页面的核心组件。

确认无误后，开始 Step 1 项目骨架搭建。
```

---

## 附录 A：测试用 Excel 数据（复制保存为 .xlsx）

| 资源ID | 资源编号 | 设备类型 | 品牌名称 | 型号 | 区域省份城市场地 | 机房名称 | 机柜名称 | 机柜编号 | 起始U位 | 占用U数 | 资产状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RES-001 | ASSET-SZ-001 | 交换机 | 华为(HUAWEI) | S5731-S48T4X | 华南广东深圳新浩e都 | 开放区01机房 | A01 | RACK-A01-01 | 1 | 1 | 运行中 |
| RES-002 | ASSET-SZ-002 | 交换机 | 华为(HUAWEI) | S5735-L24P4X-A | 华南广东深圳新浩e都 | 开放区01机房 | A01 | RACK-A01-01 | 3 | 1 | 运行中 |
| RES-003 | ASSET-SZ-003 | 交换机 | 华为(HUAWEI) | S6730-H24X6C | 华南广东深圳新浩e都 | 开放区01机房 | A01 | RACK-A01-01 | 5 | 2 | 运行中 |
| RES-004 | ASSET-SZ-004 | 交换机 | 华为(HUAWEI) | S5732-H24UM2XC | 华南广东深圳新浩e都 | 开放区01机房 | A01 | RACK-A01-01 | 8 | 1 | 运行中 |
| RES-005 | ASSET-SZ-005 | 交换机 | 华为(HUAWEI) | S5735-L48T4S-A | 华南广东深圳新浩e都 | 开放区01机房 | A01 | RACK-A01-01 | 10 | 2 | 运行中 |
| RES-006 | ASSET-SZ-006 | 交换机 | 华为(HUAWEI) | S5731-S48T4X | 华南广东深圳新浩e都 | 开放区01机房 | A02 | RACK-A02-01 | 1 | 1 | 运行中 |
| RES-007 | ASSET-SZ-007 | 交换机 | 华为(HUAWEI) | S6730-H24X6C | 华南广东深圳新浩e都 | 开放区01机房 | A02 | RACK-A02-01 | 3 | 2 | 运行中 |
| RES-008 | ASSET-SZ-008 | 服务器 | DELL | R740 | 华南广东深圳新浩e都 | 开放区02机房 | B01 | RACK-B01-01 | 1 | 2 | 运行中 |
| RES-009 | ASSET-SZ-009 | 服务器 | DELL | R650 | 华南广东深圳新浩e都 | 开放区02机房 | B01 | RACK-B01-01 | 4 | 2 | 运行中 |
| RES-010 | ASSET-SZ-010 | 防火墙 | 华为(HUAWEI) | USG6630 | 华南广东深圳新浩e都 | 荣耀机房 | C01 | RACK-C01-01 | 1 | 1 | 运行中 |

> **导入后预期效果**：
> - 开放区01机房 A01 机柜 SVG 上应显示 5 个青色设备块（U1、U3、U5-6、U8、U10-11），其余 U 位为灰色空闲。
> - A02 机柜显示 2 个青色块（U1、U3-4）。
> - B01 机柜显示 2 个蓝色块（U1-2、U4-5）。
> - C01 机柜显示 1 个橙色块（U1）。
> - 所有设备品牌均为"华为(HUAWEI)"或"DELL"，型号与 Excel 完全一致。

---

## 附录 B：Vibe Flowing 工程实践对照表

| Vibe Flowing 原文实践 | 本系统对应实现 |
|---|---|
| SDK 作为 Submodule，AI 自行探索 | 后期对接网管/CMDB API（自行封装 client.py，作为 submodule 或 pip 依赖） |
| 通用底层能力沉淀（日志/RBAC/审计/定时任务） | `crud.py` + `audit_log` + RBAC 中间件 + `logging` 日志模块 |
| DB 变更唯一入口 CLI 工具 | `crud.py` 作为 DB 变更唯一入口 + Dry-Run 预检 |
| 严禁 DELETE，强制软删 | `is_deleted` 全局软删 |
| 时间字段统一 DATETIME | 所有表 created_at/updated_at 用 DATETIME |
| 大仓 monorepo 组织 | `backend/`（FastAPI）+ `web/`（Vue 3）同仓 |
| AGENTS.md 集中规则 | 本提示语即 AGENTS.md 正文（仓库根目录，AI 自动读取） |
| 三阶段流程规则文件 | 本 AGENTS.md 三阶段流程（讨论→开发→提交，每步需确认） |
| Storybook 组件化 | 全部 Vue 组件配 .story 文件 |
| TDD 取舍（后端 pytest + 前端 Playwright） | Step 9 后跑全量测试，覆盖率目标 ≥ 70% |
| 省 Token 六策略 | 见 7.5 节 |
| 统一研发环境 | 本地研发环境 `scripts/setup.sh` 7 步自动化 |
| 页面评论提需求 + 能力地图 | 机房/机柜管理界面 + 操作手册 |
| Agent 工作流（代码即配置） | 后期扩展：自动巡检 Agent / 容量规划 Agent |

---

## 附录 C：使用建议（给网工）

1. **第一步最关键**：让 AI 复述 SVG 坐标公式和冲突检测算法，确认无误后再让它写代码。这两处算错，整个可视化就废了。
2. **先跑通 SQLite 单机版**：确认导入 + 渲染流程没问题后，再切 MySQL、加 RBAC、加审计。
3. **Excel 模板固化**：把附录 A 的表格存为 `设备导入模板.xlsx`，放在前端"下载模板"按钮背后，运营同事照着填就不会错。
4. **逐步迭代**：
   - Phase 1：机房/机柜 CRUD + Excel 导入 + SVG 视图（本次交付）
   - Phase 2：端口管理 + 线缆连接 + 简易拓扑图
   - Phase 3：SNMP 自动发现（自动填 hostname/model） + 容量规划报表
   - Phase 4：对接网管/CMDB API，自动同步资产数据
   - Phase 5：Agent 工作流（自动巡检 Agent / 下架审批 Agent）
5. **永远软删**：AI 可能图省事直接写 DELETE，每次 Review `crud.py` 时重点检查这一点。
6. **坐标公式 Review 清单**：
   - U1 在底部 → `y = 上边距 + (总U - start_u - height_u + 1) × 每U像素`
   - 设备高度 = `height_u × 每U像素`
   - 设备块底部对齐到对应 U 位的下沿
7. **冲突检测 Review 清单**：
   - 区间交集公式：`max(start_a, start_b) <= min(end_a, end_b)`
   - 必须排除 `is_deleted = True` 的设备
   - 增量更新时，同一"资源编号"的旧记录不参与冲突检测（先将其从比对集合中排除，再校验新 U 位）
8. **测试数据验证**：准备好附录 A 的 10 行 .xlsx，导入后对照 SVG 颜色块逐台核对 U 位、型号、品牌是否一致。
