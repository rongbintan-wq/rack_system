# 企业级智能机柜管理系统（DCIM-Lite）

替代 Excel 的「机房 → 机柜 → 设备 → 端口 → 线缆」五级资源管理，核心能力是 **Excel 批量导入 + SVG 机柜平面图自动渲染（一眼看清 U 位占用）**。

技术栈：**FastAPI + SQLAlchemy + SQLite（初期）** / **Vue 3 + Vite + Element Plus + Pinia**。

---

## 一、快速开始

> **Windows 用户注意**：本项目自带 **Windows 原生 `.bat` 脚本**（无需 Git Bash / WSL），
> 已写死本机托管运行时路径（Python `3.13.12` / Node `22.22.2`），直接在 **CMD** 中双击或运行即可。
> `scripts/*.sh` 是给 Linux/macOS 用的，且需自行把运行时放到 PATH。

### 方式 A（Windows，推荐）：CMD 中执行
```bat
setup.bat     # 检查环境 → 安装依赖 → 初始化 DB → 预置示例数据 → 构建前端
start.bat     # 启动后端（:8000 同端口托管前端 dist），已在运行则提示跳过
stop.bat      # 停止后端、释放 8000 端口
```
若提示"端口已被占用"，说明服务已启动，直接访问 http://127.0.0.1:8000 即可；
需重启时先 `stop.bat` 再 `start.bat`。

### 方式 B（Linux / macOS）：bash 中执行
```bash
bash scripts/setup.sh      # 检查环境 → 安装依赖 → 初始化 DB → 预置示例数据
bash start.sh             # 启动前后端（后端:8000 / 前端:5173）
```
> 注意：`scripts/setup.sh` 默认用 `python3`/`node`/`npm` 裸命令，且未锁 `bcrypt` 版本，
> 在受管 Windows 环境下请改用上面的 `.bat`，或自行把运行时加入 PATH 并加 `bcrypt==4.0.1`。

### 方式 C：手动
```bash
# 后端
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env.local                          # 按需修改
python init_db.py                                   # 建表 + 预置 3 机房 / 6 机柜 / 15 设备
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（另开终端，仅开发热更新时需要）
cd web
npm install
npm run dev                                         # http://127.0.0.1:5173
```
前端开发服务器已配置 `/api` 代理到 `:8000`，无需跨域。

### 访问
- **前端界面（生产/默认）**：http://127.0.0.1:8000 （由 FastAPI 同端口托管 `web/dist`，已内置 SPA 深链接回退）
- **前端界面（开发热更新）**：http://127.0.0.1:5173 （需另开 `npm run dev`）
- **后端 API**：http://127.0.0.1:8000 ，根路径前缀为 `/api` ，健康检查 `GET /api/health`
- **资源接口示例**：`GET /api/rooms`、`GET /api/racks`、`GET /api/devices`（注意：**不是** `/api/v1/...`）

---

## 二、Excel 导入

1. 在机柜详情页点击「📥 导入设备」，或前端任意「下载模板」入口。
2. 下载 `设备导入模板.xlsx`，按固定列（A-N）填写：
   资源ID / 资源编号 / 设备类型 / 品牌名称 / 型号 / 区域省份城市场地 / 机房名称 /
   机柜名称 / 机柜编号 / 起始U位 / 占用U位数 / 资产状态 / SN序列号 / 主机名
3. 选择文件 → 「预览校验」→ 系统 Dry-Run 校验（机柜存在性、U 越界、U 位冲突），
   绿色区显示「将新增 N / 将更新 M」，红色区列出错误行。
4. 无错误时「确认导入」→ 事务写入；任意一行失败则**整批回滚**。
5. 重复导入同一文件幂等（按资源编号 UPDATE，不重复创建）。

下载地址：`GET /api/files/template`（模板）、`GET /api/files/sample`（示例 10 行）。

---

## 三、核心算法（已用 pytest 覆盖）

1. **SVG 坐标公式**（U1 在底部，Y 轴向下，含 +1 off-by-one 修正）：
   - `设备块顶边 Y = 10 + (height_u - start_u - height_u_dev + 1) × 22`
   - `设备块高度 = 设备占用U数 × 22`
   - 示例：42U 机柜中 start_u=10、height_u=2 → Y=692、高度=44（已验证一致）。
2. **U 位冲突检测**：区间交集 `max(start_a, start_b) <= min(end_a, end_b)`；
   仅比对 `is_deleted=False` 设备；**同资源编号本次将原地 UPDATE 的旧记录须排除**（否则自冲突导致整批回滚）。

---

## 四、项目结构

```
rack_system/
├── AGENTS.md                 # 项目规则（开发提示语正文，AI 自动读取）
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── main.py           # 应用入口 / 路由注册 / SPA 托管 / 异常归一化
│   │   ├── config.py         # 环境配置（.env.local）
│   │   ├── database.py       # 引擎 / 会话 / Base
│   │   ├── models.py         # ORM 模型（软删 + 审计）
│   │   ├── schemas.py        # Pydantic 模型
│   │   ├── security.py       # JWT + RBAC
│   │   ├── crud.py           # 增删改唯一入口（软删 + 审计）
│   │   ├── importer.py       # Excel 解析 + 冲突检测 + 事务
│   │   ├── excel_template.py # 模板 / 示例生成
│   │   ├── utils/svg.py      # SVG 坐标 + 颜色
│   │   └── routers/          # rooms/racks/devices/ports/import/auth
│   ├── init_db.py            # 建表 + 预置示例数据
│   ├── tests/                # pytest（冲突算法）
│   └── data/                 # SQLite + 模板/示例 xlsx
├── web/                      # Vue 3 + Vite
│   └── src/
│       ├── api/  stores/  router/  utils/svg.js
│       ├── components/       # RackView / DeviceDrawer / ImportDialog / RackGrid / RoomCard / RoomTree / DeviceTypeChart
│       └── views/           # RoomsView / RoomDetailView / RackDetailView
├── setup.bat / start.bat / stop.bat   # Windows 原生启动脚本（CMD 直接运行）
├── scripts/setup.sh / start.sh        # Linux/macOS 用（需运行时在 PATH）
└── AGENTS.md / README.md / CHANGELOG.md
```

---

## 五、工程规范

- 所有删除为**软删**（`is_deleted=True`），禁止物理 DELETE。
- 统一返回 `{ code, data, msg }`，`code≠0` 为错误。
- 关键操作写 `audit_log`（操作人 / 时间 / 前后值对比）。
- 批量导入必须 Dry-Run 预检，事务原子写入。
- 删除 / 下架前端二次确认。

---

## 六、后续路线（Phase 2+）

端口管理 + 线缆连接拓扑 → SNMP 自动发现 → 容量规划报表 → 对接 CMDB/网管 API → 巡检/下架审批 Agent。

---

## 七、常见问题（排错）

### 1. 浏览器打开只显示标题、页面全白（白屏）
**现象**：`http://127.0.0.1:8000/rooms` 标题栏有文字，但 `<div id="app">` 内容为空。
**原因**：`web/src/App.vue` 的 `<script setup>` 中使用了 `ref()` 但未从 `'vue'` 导入，运行时抛 `ReferenceError: ref is not defined`，Vue 应用无法挂载。
**修复**：`import { onMounted } from 'vue'` → `import { ref, onMounted } from 'vue'`，然后重新构建 `npm run build`。
**用户侧**：改完构建后必须 **Ctrl+F5 强刷**（JS 文件名带 hash，旧文件被缓存会导致仍白屏）。

### 2. 前端改完代码后页面没变化
构建产物带 content-hash，浏览器可能缓存旧 JS。请 **Ctrl+F5 强制刷新**；若仍无效，清浏览器缓存后重试。

### 3. `npm run build` 清理 dist 时报 safe-delete / trash 错误
部分环境（受管沙箱）的 `rmSync` 被包装为「安全删除」拦截，导致 Vite 清空 `dist` 失败：
`[safe-delete] 操作失败 ... trash operation`。
**处理**：手动删除 `web/dist` 目录后再重新构建：
```bat
# Windows
powershell -Command "Remove-Item -LiteralPath 'C:\Users\Administrator\rack_system\web\dist' -Recurse -Force"
# 或 Linux/macOS
rm -rf web/dist
npm run build
```

### 4. 接口 404（`/api/v1/...` 不存在）
本系统 API 根路径是 **`/api`**（不是 `/api/v1`）。正确示例：`GET /api/rooms`、`GET /api/racks`、`GET /api/devices`。
前端 `web/src/api/index.js` 已统一设 `baseURL: '/api'`，勿自行加 `v1`。

### 5. CMD 里执行 `bash scripts/setup.sh` 报 "bash 不是内部或外部命令"
Windows 命令提示符（CMD）没有 `bash`。请用根目录的 **Windows 原生脚本**：`setup.bat` / `start.bat` / `stop.bat`（已写死本机托管运行时路径，无需 Git Bash/WSL）。`scripts/*.sh` 仅供 Linux/macOS 使用。

### 6. 访问提示端口被占用
说明后端已在运行，直接开 `http://127.0.0.1:8000` 即可；如需重启先 `stop.bat` 释放 8000 端口再 `start.bat`。

