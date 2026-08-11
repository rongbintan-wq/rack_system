# Role: 资深基础设施运维架构师 & 全栈开发专家

你是一位精通 Python FastAPI 和 Vue 3 的全栈架构师。
请为我设计并实现一个「企业级智能机柜管理系统（DCIM-Lite）」。
本项目严格遵循「Vibe Flowing」工程实践，强调安全、规范与自动化。

---

## 一、项目背景与目标

内部使用的**机柜管理系统**，核心目标：
1. 替代 Excel，管理「机房 → 机柜 → 设备 → 端口 → 线缆」五级资源。
2. 核心可视化：根据导入的设备数据，自动渲染机柜平面图（SVG），一眼看清 U 位占用。
3. 支持新增机房、新增机柜、批量导入设备（Excel）。

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
- **Port（端口）**：id, device_id(FK), port_name, port_type(电口/光口/管理口/Console),
  speed(10M/100M/1G/10G/25G/40G/100G), status(up/down/预留/未接)
- **Connection（线缆）**：id, port_a_id(FK), port_b_id(FK), cable_type, length_m, notes
- **ImportLog（导入记录）**：id, filename, import_time, total_rows, success_count, failed_count, status, error_detail(JSON)

**全局约束**：
- 所有表必须有 `created_at`、`updated_at`、`is_deleted`（软删标志）。
- 设备 U 位不能重叠（同一机柜内）。
- 删除设备 / 机柜 / 机房均为软删，禁止物理 DELETE。
- 时间字段统一用 DATETIME，禁止 BIGINT 时间戳。

---

## 三、Excel 导入格式

模板列（顺序固定，A-N）：资源ID, 资源编号, 设备类型, 品牌名称, 型号, 区域省份城市场地,
机房名称, 机柜名称, 机柜编号, 起始U位, 占用U位数, 资产状态, SN序列号, 主机名。

后端解析（openpyxl，强制使用，禁止 xlrd）：
1. `load_workbook(filename, data_only=True)`，跳过表头，逐行读取；必填列非空校验。
2. 机柜归属校验：按「机房名称 + 机柜编号」查 DB，不存在则失败。
3. U 位越界校验：`start_u >= 1` 且 `start_u + height_u - 1 <= rack.height_u`。
4. **U 位冲突检测（核心）**：区间交集 `max(start_a, start_b) <= min(end_a, end_b)`；
   仅比对 `is_deleted=False` 的设备；**同「资源编号」本次将原地 UPDATE 的旧记录须排除**（否则会与自己冲突）。
5. 增量更新 vs 新增：按「资源编号」存在则 UPDATE，否则 INSERT（幂等，重复导入不报错）。
6. 事务提交：全部通过 → `db.begin()` 批量写入 → commit；任意一行失败 → 整批 rollback。

前端交互：`POST /api/import/preview`（Dry-Run）→ 分「将新增 N / 将更新 M」与错误区 →
无错时「确认导入」→ `POST /api/import/commit`。

---

## 四、SVG 机柜视图（核心可视化）

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

交互：Hover 设备块显示 Tooltip；点击设备块打开右侧详情抽屉（编辑/下架）；点击空闲 U 位弹出上架表单。

---

## 五、工程规范

- **RBAC**：超级管理员 / 机房运维 / 访客；鉴权由 JWT 注入 `operator_id`，未登录 401。
- **DB 铁律**：增删改经 `crud.py` 封装，API 层只调用不写 SQL；严禁物理 DELETE；批量操作须 Dry-Run 预检；Excel 导入用事务。
- **统一返回**：`{ "code": 0, "data": {}, "msg": "success" }`，code≠0 为错误。
- **审计日志**：关键操作写 `audit_log`（operator_id、时间、前后值对比）。
- **日志**：标准 logging，JSON 格式，禁止 print。
- **前端**：组件化（RackView / DeviceBlock / RoomCard / RoomTree / RackGrid / DeviceDrawer / ImportDialog 等）；
  Pinia 管理 rooms/racks/devices store；路由 `/rooms` → `/rooms/:id` → `/racks/:id`；删除/下架二次确认。
- **省 Token**：本 AGENTS.md 集中规则；前后端同仓 monorepo（`backend/` + `web/`）。

---

## 六、初始任务流程

1. 讨论阶段：复述 SVG 坐标公式、冲突检测算法、三级路由结构，等待确认。
2. 开发阶段：骨架 → ORM/CRUD → 机房 → 机柜 → 导入 API → 导入对话框 → SVG 视图 → 设备抽屉 → 端口线缆。
3. 提交阶段：README + CHANGELOG + 静态检查（后端 ruff/pytest，前端 oxlint/vue-tsc）+ 推送。

---

## 七、本地研发

- `scripts/setup.sh`：检查环境 → 安装依赖 → 初始化配置 → 初始化 DB → 启动。
- `init_db.py`：建表 + 预置 3 机房 / 6 机柜 / 15 设备。
- `start.sh`：前后端启动 + 端口检查 + 日志重定向。
- 后端依赖隔离在 venv；前端用 `npm install` + `npm run dev`（代理 `/api` 到 :8000）。
