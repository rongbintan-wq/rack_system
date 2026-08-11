# Changelog

## [1.0.0] - 2026-08-10

### 新增（Phase 1：机房/机柜 CRUD + Excel 导入 + SVG 视图）
- 后端 FastAPI + SQLAlchemy + SQLite 全栈骨架（monorepo：backend/ + web/）。
- 数据模型：Room / Rack / Device / ImportLog / AuditLog / User，全局软删 + DATETIME 时间戳。
- 机房、机柜、设备 CRUD API，统一返回 `{ code, data, msg }`，RBAC + JWT 鉴权（DEV 可关闭）。
- Excel 批量导入：`openpyxl` 解析 + 机柜归属校验 + U 越界校验 + **U 位冲突检测（含排除自身 UPDATE）** + 增量更新（幂等）+ 事务回滚。
- 核心 SVG 机柜视图坐标公式（含 +1 off-by-one 修正）与按设备类型颜色编码，前端 RackView 渲染。
- 前端 Vue 3 + Element Plus + Pinia + Vue Router：
  - 机房列表（表格/卡片切换、筛选）、机房详情（机柜矩阵 + 设备类型分布）。
  - 机柜详情（SVG 视图 + Hover Tooltip + 点击空闲 U 上架 + 设备抽屉编辑/下架）。
  - 导入对话框（上传 → Dry-Run 预览 → 确认提交 → 结果反馈）。
- 预置数据：`init_db.py` 建表 + 3 机房 / 6 机柜 / 15 设备；Excel 模板与示例数据下载接口。
- 工程文件：AGENTS.md、README.md、CHANGELOG.md、.env.example、start.sh、scripts/setup.sh。
- 测试：pytest 覆盖 U 位冲突检测、自身 UPDATE 排除、越界、机柜不存在（4 passed）。

### 修复（相对原始提示语）
- SVG 坐标公式 off-by-one：采用 `Y = 上边距 + (height_u - start_u - height_u_dev + 1) × 22` 修正。
- U 位冲突检测顺序：先按资源编号排除本次将 UPDATE 的旧记录，再比对，避免自冲突整批回滚。

### 版本备份（Git）
- 首次版本备份标签：**`v1.0.0`**（对应 Phase 1 完整交付，2026-08-10）。
- 备份范围：源码 `backend/`、`web/src`、工程文件（`AGENTS.md` / `README.md` / `CHANGELOG.md` / `.env.example` / `start.bat` / `setup.bat` / `stop.bat` / `scripts/`）。
- 已按 `.gitignore` 排除：密钥 `.env.local`、SQLite 数据 `*.db`、构建产物 `web/dist`、依赖 `node_modules`、运行时日志 `logs/`。
- 提交前检查：后端 `pytest`（4 passed）、前端 `npm run build` 通过、无敏感文件入库。
- 恢复方式：`git checkout v1.0.0`；初始化运行 `setup.bat`（Windows）或 `bash scripts/setup.sh`（Linux/macOS）。
- 说明：AGENTS.md 提交阶段含"推送"，本机未配置 remote，故仅做**本地版本备份**；需推送时执行 `git remote add origin <url>` 后 `git push --tags`。

## [1.1.0] - 2026-08-11

### 变更（资源模型收敛为三级）
- 按需求将管理范围从「机房→机柜→设备→端口→线缆」五级收敛为**三级**（机房→机柜→设备），端口/线缆移出本期范围（保留为 Phase 2+ 路线）。
- **后端清理**：删除 `Port` / `Connection` 数据模型；删除 `routers/ports.py`（含端口与线缆接口）；`crud.py` / `schemas.py` 移除对应增删查封装；`main.py` 取消 `ports.router` 挂载。
- **前端清理**：`web/src/api/index.js` 移除 `devicePorts` / `createPort` / `deletePort` / `listConnections` / `createConnection` / `deleteConnection` 等指向已删端点的死代码。
- **文档同步**：`机柜管理系统_AI开发提示语.md` 与 `AGENTS.md` 更新背景目标（三级资源）、数据模型（删 Port/Connection）、前端组件清单（去 PortList/ConnectionForm）、开发流程（删 Step 9 端口线缆）、审计日志示例（去"删线缆"）。
- **兼容性**：其余功能（机房/机柜/设备 CRUD、Excel 导入冲突检测、SVG 视图、JWT 鉴权、软删、审计）均不受影响；`pytest` 4 项冲突算法测试保持通过。

### 版本备份（Git）
- 标签：**`v1.1.0`**（基于 `v1.0.0`，仅含端口/线缆收敛，2026-08-11）。
- 恢复方式：`git checkout v1.1.0`；初始化运行 `setup.bat`（Windows）或 `bash scripts/setup.sh`（Linux/macOS）。

## [1.2.0] - 2026-08-11

### 修复（下架占用逻辑 + 导出 422）
- **统一"占用"口径**：设备占用 U 位 ⇔ `is_deleted=False AND asset_status != '已下架'`。
  此前下架仅置 `asset_status='已下架'` 但判定仍按 `is_deleted`，导致两处 bug：
  1. 下架设备仍显示在机柜图（渲染未排除已下架）；
  2. 下架后其 U 位仍被判定"已占用"，新设备无法上架。
  该口径统一应用到 `crud.list_devices` / `_conflict` / `rack_used_u` / `rack_stats` / `room_stats` / `importer` 工作集。
- **重新上架闭环**：机房详情页新增「已下架设备」可折叠面板，每项「重新上架」按钮调用更新接口复用原 U 位；
  若目标 U 位被在用设备占用 → 返回 **「位置已占用告警」** 并禁止上架，待占用设备下架释放后方可重上架。
- **冲突提示语统一**为「位置已占用告警」（create / update / import 三处一致）。
- **导出 422 根因修复**：导出端点 `GET /api/devices/export` 此前未加载到运行进程，
  请求被 `/{device_id}` 误匹配为 `device_id="export"`（int 解析失败）→ 422；
  重启 uvicorn 后新路由表生效（/export 已声明在 /{device_id} 之前），导出返回 200 + xlsx。
- **AGENTS.md 提示语**：新增 4.4 下架语义与占用判定、4.5 路由顺序与重启铁律；三 冲突检测说明同步更新。

### 验证
- 后端 TestClient 端到端：下架→机柜图不再显示、新设备同 U 上架成功、旧设备重上架报「位置已占用告警」、占用设备下架后旧设备重上架成功、DB 还原。
- 导出端点：`GET /api/devices/export` → 200，Content-Type 正确，导出含全部非删除设备。
- 前端 `npm run build` 通过；服务进程已重启至 :8000 加载新代码。
