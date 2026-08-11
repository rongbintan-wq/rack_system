# Changelog

## [1.0.0] - 2026-08-10

### 新增（Phase 1：机房/机柜 CRUD + Excel 导入 + SVG 视图）
- 后端 FastAPI + SQLAlchemy + SQLite 全栈骨架（monorepo：backend/ + web/）。
- 数据模型：Room / Rack / Device / Port / Connection / ImportLog / AuditLog / User，全局软删 + DATETIME 时间戳。
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
