# Role: 资深基础设施运维架构师 & 全栈开发专家

你是一位精通 Python FastAPI 和 Vue 3 的全栈架构师。
请为我设计并实现一个「企业级智能机柜管理系统（DCIM-Lite）」。
本项目严格遵循「Vibe Flowing」工程实践，强调安全、规范与自动化。

---

## 一、项目背景与目标

内部使用的**机柜管理系统**，核心目标：
1. 替代 Excel，管理「机房 → 机柜 → 设备」三级资源（端口/线缆不在本期范围）。
2. 核心可视化：根据导入的设备数据，自动渲染机柜平面图（SVG），一眼看清 U 位占用。
3. 支持新增机房、新增机柜、批量导入设备（Excel）、一次性导出全部设备（Excel）。

技术栈：后端 Python FastAPI + 前端 Vue 3 + SQLite（初期）→ MySQL（后期）。
开发模式：Vibe Coding，严格遵循 SDD 规范驱动开发。

---

## 二、核心数据模型（Schema First，禁止擅自增减字段）

- **Room（机房）**：id, room_name(唯一), building, floor, total_racks, status(在用/停用/预留),
  region, province, city, site, owner, contact_phone, notes
- **Rack（机柜）**：id, rack_name, rack_code(唯一), room_id(FK), height_u(默认42), width_mm(默认600),
  depth_mm(默认1000), power_type, status(空闲/部分占用/已满/预留/故障), location_note, notes
- **Device（设备）**：id, resource_id, resource_code, device_type(交换机/服务器/防火墙/路由器/存储/KVM/其他),
  brand_name, model, region, site_detail, room_name, rack_name, rack_code(FK),
  start_u(从下往上), height_u(默认1), asset_status(运行中/已下架/维修中/报废), sn, hostname,
  created_at, updated_at, is_deleted
- **ImportLog（导入记录）**：id, filename, import_time, total_rows, success_count, failed_count, status, error_detail(JSON)

**全局约束**：
- 所有表必须有 `created_at`、`updated_at`、`is_deleted`（软删标志）。
- 设备 U 位不能重叠（同一机柜内）。
- 删除设备 / 机柜 / 机房均为软删，禁止物理 DELETE。
- 时间字段统一用 DATETIME，禁止 BIGINT 时间戳。

---

## 三、Excel 导入格式（修订：提升到机房层级）

模板列（顺序固定，A-O）：
资源ID, 资源编号, 设备类型, 品牌名称, 型号, 区域省份城市场地,
机房编号/名称, 机柜名称, 机柜编号, 起始U位, 占用U位数,
资产状态, SN序列号, 主机名

（注：须显式携带「机房编号/名称」+「机柜编号」，以支持跨层级、跨页面导入；
导入不依赖当前所在页面/机柜上下文。）

后端解析（openpyxl，强制使用，禁止 xlrd）：
1. `load_workbook(filename, data_only=True)`，跳过表头，逐行读取；必填列非空校验。
2. 机柜归属校验：按「机房(编号或名称) + 机柜编号」查 DB，不存在则失败。
3. U 位越界校验：`start_u >= 1` 且 `start_u + height_u - 1 <= rack.height_u`。
4. **U 位冲突检测（核心）**：区间交集 `max(start_a, start_b) <= min(end_a, end_b)`；
   占用判定唯一口径：**仅比对 `is_deleted=False` 且 `asset_status != '已下架'` 的设备**
   （已下架设备释放其 U 位，不计入占用、不阻塞新上架）；
   **同「资源编号」本次将原地 UPDATE 的旧记录须排除**（否则会与自己冲突）。
5. 增量更新 vs 新增：按「资源编号」存在则 UPDATE，否则 INSERT（幂等，重复导入不报错）。
6. 事务提交：全部通过 → `db.begin()` 批量写入 → commit；任意一行失败 → 整批 rollback。

前端交互（入口见「五、导入/导出入口约束」）：
`POST /api/import/preview`（Dry-Run）→ 分「将新增 N / 将更新 M」与错误区 →
无错时「确认导入」→ `POST /api/import/commit`。

---

## 四、SVG 机柜视图与交互层级（修订）

### 4.1 视图层级约束（两级即止）
- 机房管理仅两级：机房列表(RoomsView) → 机房详情(RoomDetailView)。
- 机房详情页**内联渲染该机房下所有机柜的 SVG 机柜图（机柜矩阵）**，
  不提供独立「机柜详情」页面菜单入口。
- 点击设备色块 → DeviceDrawer（抽屉）查看/编辑/下架；
  点击空白处或「返回」→ 回到机房列表。
- 原 RackDetailView 保留为可选深链（路由 `/racks/:id` 仍可达，非主入口），
  其导入入口与机房层共用同一 ImportDialog，逻辑完全一致。

### 4.2 SVG 机柜图（核心可视化，坐标公式不变）
- 一个 Rack 一个 SVG，宽度 140px，每 U 高度 22px。
- 总画布高度 = `rack.height_u × 22px` + 上下边距各 10px。
- U 位编号标注左侧；设备块在右侧主区域。

**坐标公式（U1 在底部，Y 轴向下，含 +1 修正）**：
```
设备块顶边 Y = 上边距 + (rack.height_u - start_u - height_u + 1) × 22px
设备块高度   = height_u × 22px
```
示例：42U 机柜，设备 start_u=10, height_u=2 → 顶边 Y = 10 + (42-10-2+1)×22 = 692px，高度 = 44px。

颜色编码（按设备类型）：交换机 #50E3C2，服务器 #4A90E2，防火墙 #F5A623，路由器 #BD10E0，
存储 #7ED321，KVM/其他 #9B9B9B，空闲 #F5F5F5（虚线），预留 #F8E71C（斜纹）。

### 4.3 设备标签与交互
- 设备色块内**直接渲染「品牌 + 型号」文字标签**（字号自适应，超出省略号），
  使运维人员一眼可见设备信息。
- 点击设备色块 → DeviceDrawer；点击空闲 U 位 → 上架表单；点击空白/返回 → 机房列表。

### 4.4 下架（decommission）语义与占用判定（强制统一口径）

- **下架 ≠ 软删**：下架仅将 `asset_status` 置为「已下架」，**保留 `is_deleted=False` 与 `start_u/height_u`**，
  以便后续「重新上架」复用原 U 位（无需重新指定位置）。
- **占用判定唯一口径**：设备"占用"某 U 位 ⇔ `is_deleted=False AND asset_status != '已下架'`。
  下列逻辑必须**统一使用该口径，禁止只判 `is_deleted`**：
  1. 机柜 SVG 渲染（`rack_layout` / `list_devices`）——已下架设备不渲染；
  2. U 位冲突检测（`_conflict` / `importer` 工作集）——已下架设备不计入占用；
  3. 机柜占用率 / 已用 U 数（`rack_used_u` / `rack_stats` / `room_stats`）——已下架设备不计入；
  4. 设备列表（`list_devices` / `rack_devices`）默认只返回占用中设备（已下架设备由独立查询提供）。
- **重新上架闭环**：机房详情页提供「已下架设备」可折叠面板，每项带「重新上架」按钮；
  点击后按占用口径做冲突检测：若目标 U 位被在用设备占用 → 返回 **「位置已占用告警」** 并禁止上架；
  待占用设备下架、该 U 位释放后，方可成功重新上架（复用原 `start_u/height_u`）。
- **冲突提示语统一为「位置已占用告警」**（create / update / import 三处一致）。

### 4.5 路由顺序与重启铁律（防 422 / 404）

- 静态动作路由（如 `/export`、`/preview`、`/decommissioned`）**必须声明在 `/{id}` 等路径参数路由之前**，
  否则 `/export` 会被误匹配为 `/{device_id}=export`，因 `device_id: int` 解析失败返回 **422**。
  （更稳妥：静态动作用独立前缀如 `/export/all`，彻底规避路径参数碰撞。）
- **改后端代码后必须重启服务进程（uvicorn）**：运行中的旧进程仍持有旧路由表，
  新端点（如刚加的 `/export`）不会被加载，请求将落到旧路由 → 422 / 404。
  重启见「八、本地研发 / start」；前端改动需 `npm run build` 后刷新浏览器。

---

## 五、导入/导出入口约束（修订）

- 导入入口提升到「机房管理」层级：
  RoomsView（机房列表）与 RoomDetailView（机房详情）均提供「导入设备」按钮，
  弹出同一个 ImportDialog。
- 导入以 Excel 数据为准：每行通过「机房编号/名称 + 机柜编号」自动归属目标机柜，
  不依赖当前页面/机柜上下文。
- 原 RackDetailView 内导入入口保留，与机房层入口共用同一后端
  `/api/import/preview` 与 `/api/import/commit`，逻辑完全一致。

### 设备导出约束（新增）
- 提供「导出全部设备」功能：一次性导出所有机房的全部设备信息为 Excel。
- 入口：RoomsView（机房列表）顶部「导出全部设备」按钮。
- 后端：新增 `GET /api/devices/export`，
  查询全部 `is_deleted=False` 设备，按「机房 → 机柜 → 设备」排序，
  用 openpyxl 生成 xlsx，经 `StreamingResponse` 返回
  （Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`）。
- 导出列：与导入模板对齐（资源ID、资源编号、设备类型、品牌名称、型号、机房名称/编号、
  机柜编号、起始U位、占用U位数、资产状态、SN、主机名），便于回导校验。
- 本期设备量 < 10万，直接同步生成；遵循统一返回 `{code,data,msg}`。

---

## 六、工程规范

- **RBAC**：超级管理员 / 机房运维 / 访客；鉴权由 JWT 注入 `operator_id`，未登录 401。
- **DB 铁律**：增删改经 `crud.py` 封装，API 层只调用不写 SQL；严禁物理 DELETE；批量操作须 Dry-Run 预检；Excel 导入/导出用事务或流式生成。
- **统一返回**：`{ "code": 0, "data": {}, "msg": "success" }`，code≠0 为错误。
- **审计日志**：关键操作写 `audit_log`（operator_id、时间、前后值对比）。
- **日志**：标准 logging，JSON 格式，禁止 print。
- **前端**：组件化（RoomsView / RoomDetailView / RackGrid / DeviceBlock / DeviceDrawer / ImportDialog / ExportButton 等）；
  Pinia 管理 rooms/racks/devices store；主路由 `/rooms` → `/rooms/:id`（内联机柜矩阵），`/racks/:id` 仅作可选深链；删除/下架二次确认。
- **省 Token**：本 AGENTS.md 集中规则；前后端同仓 monorepo（`backend/` + `web/`）。

---

## 七、初始任务流程

1. 讨论阶段：复述 SVG 坐标公式、冲突检测算法、两级视图结构，等待确认。
2. 开发阶段：骨架 → ORM/CRUD → 机房 → 机柜 → 导入 API → 导入对话框 → SVG 视图 → 设备抽屉 → 导出 API。
3. 提交阶段：README + CHANGELOG + 静态检查（后端 ruff/pytest，前端 oxlint/vue-tsc）+ **版本号一致性校验（`python scripts/check_version.py`）** + 推送。

---

## 八、本地研发

- `scripts/setup.sh`：检查环境 → 安装依赖 → 初始化配置 → 初始化 DB → 启动。
- `init_db.py`：建表 + 预置 3 机房 / 6 机柜 / 15 设备。
- `start.sh`：前后端启动 + 端口检查 + 日志重定向。
- 后端依赖隔离在 venv；前端用 `npm install` + `npm run dev`（代理 `/api` 到 :8000）。

---

## 九、Git 版本管理与发布规范

- **手动确认铁律**：所有 git 写操作（commit / tag / push / merge / reset / branch -d / 远端删除 / 创建 PR / 合并 PR 等）**必须等待用户明确确认后方可执行**。
  - 执行前：先列出将要运行的完整 git 命令及影响范围（目标分支、远端、tag），向用户说明并请求确认。
  - 用户未明确回复"确认/执行/可以"等肯定指令前，禁止自动运行任何 git 写操作。
  - 仅 `git status` / `git log` / `git diff` 等只读命令可不经确认直接执行。

### 分支模型
- **`main` 是 GitHub 上唯一的远程根分支**（无 `master` 分支），所有发布以 `main` 为准，GitHub 默认页即展示 `main`。
- 开发从 `main` 切出短生命周期分支（命名如 `feat/xxx`、`fix/xxx`），完成经 PR 合回 `main`，合后删除源分支。
- 本地若存在历史残留的 `master` 分支仅作参考，不再推送或并入 `main`。

### PR 标准流程（合入 main）
1. 提 PR 前自检（只读，不改动）：
   `git fetch origin`
   `git log --oneline origin/main..<branch>` —— 确认将带入 `main` 的提交清单；
   `git diff --stat origin/main...<branch>` —— 确认改动文件范围。
2. GitHub 新建 PR：`base = main`，`compare = <branch>`，标题与描述须含变更要点（如「统一下架占用口径、新增重上架面板、冲突提示统一、AGENTS 4.4/4.5」）。
3. 无冲突则合并，合并方式**优先 Squash and merge**（多提交压成单个干净提交）；或 Create a merge commit（保留分支链）。
4. 合并后于 PR 页 **Delete branch** 删除远端源分支；本地清理 `git branch -d <branch>`（若远端已删可 `git fetch --prune`）。
5. 若 PR 提示冲突：本地 `git checkout main && git pull origin main && git merge <branch>` 解决后 `git push origin main`，或在网页 Resolve conflicts。

### 版本备份与发布
- 本地开发：`git init`（已初始化则跳过）→ 本地 commit（消息含 CHANGELOG 说明，遵循「手动确认铁律」）。
- 发布标签：`git tag -a vX.Y.Z -m "..."` → `git push origin vX.Y.Z`（仅推 `main` 及其 tag）。
- 推送 / 打 tag 前同样须逐条确认：目标分支、tag 名称、远端地址。

### 版本号一致性铁律
- **权威来源**：项目版本号以 `CHANGELOG.md` 最新条目（如 `[1.2.0]`）为唯一权威值。
- **版本载体文件（必须保持一致，禁止漂移）**：
  1. `backend/app/main.py` → `FastAPI(version="X.Y.Z")`（用于 OpenAPI 文档展示）
  2. `web/package.json` → `"version": "X.Y.Z"`
  3. 四份项目手册（`运维操作手册.md` / `开发手册.md` / `测试手册.md` / `能力地图.md`）及 `README.md` 中的版本标注
- **提交前强制检查**：每次代码提交 / 建 PR 前，须运行版本一致性校验：
  ```bash
  python scripts/check_version.py
  ```
  脚本以 `CHANGELOG.md` 为准，比对 `main.py` / `package.json` 的版本号；不一致则报错退出（exit 1），须先统一再提交。
- **同步规则**：若本次提交修改了任一版本载体文件（如发版升级版本号），必须同步更新其余所有载体，确保彼此一致且不落后于 `CHANGELOG.md` 最新值；若未触碰版本字段则保持现状，不强行升级。
- **版本升级时机**：仅在完成一次功能 / 缺陷发布、并补写 `CHANGELOG.md` 对应条目后，才整体将载体升至新版本号；日常功能提交不得零散改动版本号。
- 周一自动核对任务负责手册与配置同步，但**代码提交仍需本地运行 `check_version.py` 校验**，不可依赖定时任务替代提交前检查。
