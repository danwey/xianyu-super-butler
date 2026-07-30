# 🐟 闲鱼超级管家

<div align="center">

**闲鱼多账号管理、自动回复、自动发货与订单管理平台**

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-supported-2496ED.svg?logo=docker)](https://www.docker.com/)

基于 [zhinianboke/xianyu-auto-reply](https://github.com/zhinianboke/xianyu-auto-reply) 二次开发，提供 Web 管理后台、只读 CLI、MCP Server 和 Agent Skill。

</div>

---

## 目录

- [功能概览](#功能概览)
- [界面预览](#界面预览)
- [运行要求](#运行要求)
- [Docker 快速启动](#docker-快速启动推荐)
- [本地安装](#本地安装)
- [首次使用](#首次使用)
- [配置说明](#配置说明)
- [常用运维命令](#常用运维命令)
- [CLI 使用](#cli-使用)
- [MCP 使用](#mcp-使用)
- [安全部署建议](#安全部署建议)
- [常见问题](#常见问题)
- [开发与测试](#开发与测试)

---

## 功能概览

### 闲鱼业务

- 多闲鱼账号管理，支持启用、停用及登录状态维护
- 关键词自动回复、商品专属回复和默认回复
- AI 智能议价及自定义折扣规则
- 订单同步、筛选、详情查看和状态管理
- 卡券管理、自动发货、延时发货和手动补发
- 商品、发货规则、回复规则和订单统计管理
- Excel 批量导入、导出

### Agent 能力

仓库包含一套只读 Agent 适配层：

- `xianyu_agent/client.py`：复用 Web 服务登录会话的异步 HTTP Client
- `xianyu_agent/cli.py`：输出 JSON 的命令行工具
- `xianyu_agent/mcp_server.py`：只读 MCP Server
- `skills/xianyu-super-butler/SKILL.md`：Agent Skill

Agent 层通过 HTTP 调用已经运行的 FastAPI 服务，不会额外创建闲鱼 WebSocket 或 CookieManager 实例。

---

## 界面预览

### 工作台

![Dashboard 界面](static/uploads/images/1.png)

### 订单管理

![订单管理](static/uploads/images/2.png)

### 手动补发

![发货方式选择](static/uploads/images/3.png)
![发货中](static/uploads/images/4.png)

---

## 运行要求

### Docker 部署

- Docker Engine 24+，或兼容版本
- Docker Compose v2
- 建议至少 2 GB 可用内存
- 能访问闲鱼及项目所需的外部接口

Docker 镜像会自动：

- 使用 Python 3.11
- 构建 `frontend/` 前端
- 安装 Chromium 和 Playwright 运行依赖
- 启动 `Start.py`

### 本地运行

- Python 3.11+
- Node.js 20+
- PNPM
- Chrome/Chromium
- Linux、macOS 或 Windows

---

## Docker 快速启动（推荐）

### 1. 克隆仓库

```bash
git clone https://github.com/danwey/xianyu-super-butler.git
cd xianyu-super-butler
```

### 2. 创建持久化目录

```bash
mkdir -p data logs backups
```

### 3. 创建环境变量文件

在项目根目录创建 `.env`：

```dotenv
WEB_PORT=8080
TZ=Asia/Shanghai

ADMIN_USERNAME=admin
ADMIN_PASSWORD=请替换为强密码
JWT_SECRET_KEY=请替换为至少32位随机字符串
SESSION_TIMEOUT=3600

USER_REGISTRATION_ENABLED=true
AUTO_REPLY_ENABLED=true
AUTO_DELIVERY_ENABLED=true
AI_REPLY_ENABLED=false

DB_PATH=/app/data/xianyu_data.db
LOG_LEVEL=INFO
DEBUG=false
```

生成随机密钥示例：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> 不要把包含密码、Cookie 或 API Key 的 `.env` 提交到 Git。

### 4. 构建并启动

```bash
docker compose up -d --build
```

### 5. 检查状态

```bash
docker compose ps
docker compose logs -f xianyu-app
curl http://127.0.0.1:8080/health
```

浏览器访问：

```text
http://服务器地址:8080
```

生产环境不建议直接向公网开放 8080，参见[安全部署建议](#安全部署建议)。

### 6. 停止或更新

```bash
# 停止服务
docker compose down

# 拉取代码并重新构建
git pull
docker compose up -d --build
```

数据默认保存在以下目录：

```text
data/       SQLite 数据库
logs/       运行日志
backups/    备份文件
```

删除容器不会删除这些目录。升级前仍建议单独备份。

---

## 本地安装

### 1. 克隆项目并创建虚拟环境

```bash
git clone https://github.com/danwey/xianyu-super-butler.git
cd xianyu-super-butler

python3.11 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装后端依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

安装 Playwright 浏览器：

```bash
playwright install chromium
```

Linux 还可执行：

```bash
playwright install-deps chromium
```

DrissionPage 需要系统中存在 Chrome 或 Chromium。

### 3. 构建前端

```bash
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm build
cd ..
```

前端构建产物会输出到后端使用的 `static/` 目录。

### 4. 启动服务

```bash
python Start.py
```

服务默认监听 8080 端口：

```text
http://127.0.0.1:8080
```

`Start.py` 会初始化数据库、检查 Playwright 浏览器、创建 CookieManager，并在后台启动 FastAPI 服务。

---

## 首次使用

1. 打开 Web 管理后台。
2. 按页面提示注册或使用已配置的管理员账号登录。
3. 立即修改默认或临时密码。
4. 添加闲鱼账号，可按页面提供的方式登录或录入 Cookie。
5. 检查账号是否已启用、登录状态是否正常。
6. 配置关键词回复、默认回复或 AI 议价。
7. 使用自动发货前，先创建卡券并配置发货规则。
8. 用测试商品和测试订单验证回复、发货及订单状态同步。

> 闲鱼 Cookie、账号密码和 AI API Key 都属于敏感凭据，不要发送到日志、Issue、PR 或聊天记录中。

---

## 配置说明

Docker Compose 已支持以下常用环境变量：

| 变量 | 默认值 | 说明 |
|---|---:|---|
| `WEB_PORT` | `8080` | 主机映射端口 |
| `TZ` | `Asia/Shanghai` | 容器时区 |
| `DB_PATH` | `/app/data/xianyu_data.db` | SQLite 数据库路径 |
| `LOG_LEVEL` | `INFO` | 日志等级 |
| `DEBUG` | `false` | 调试模式 |
| `ADMIN_USERNAME` | `admin` | 管理员用户名回退值 |
| `ADMIN_PASSWORD` | `admin123` | 管理员密码回退值，必须覆盖 |
| `JWT_SECRET_KEY` | `default-secret-key` | 签名密钥回退值，必须覆盖 |
| `SESSION_TIMEOUT` | `3600` | 会话超时秒数 |
| `USER_REGISTRATION_ENABLED` | `true` | 是否允许注册 |
| `AUTO_REPLY_ENABLED` | `true` | 是否启用自动回复 |
| `AUTO_DELIVERY_ENABLED` | `true` | 是否启用自动发货 |
| `AUTO_DELIVERY_TIMEOUT` | `30` | 自动发货超时秒数 |
| `AI_REPLY_ENABLED` | `false` | 是否启用 AI 回复 |
| `DEFAULT_AI_MODEL` | `qwen-plus` | 默认 AI 模型 |
| `DEFAULT_AI_BASE_URL` | 阿里云兼容地址 | OpenAI 兼容接口地址 |
| `WEBSOCKET_URL` | 闲鱼 WebSocket 地址 | 消息连接地址 |
| `HEARTBEAT_INTERVAL` | `15` | 心跳间隔秒数 |

完整变量以 `docker-compose.yml` 和项目配置文件为准。

### 旧版单账号 Cookie

仍可通过环境变量加载一个名为 `default` 的账号：

```bash
export COOKIES_STR='你的 Cookie'
python Start.py
```

新部署建议通过 Web 管理后台维护账号，不建议长期把 Cookie 写入 shell 历史或 Compose 文件。

---

## 常用运维命令

```bash
# 查看容器状态
docker compose ps

# 查看实时日志
docker compose logs -f --tail=200 xianyu-app

# 重启服务
docker compose restart xianyu-app

# 进入容器
docker compose exec xianyu-app bash

# 健康检查
curl http://127.0.0.1:8080/health

# 备份数据库
cp data/xianyu_data.db "backups/xianyu_data-$(date +%Y%m%d-%H%M%S).db"
```

SQLite 备份前建议暂停写入，或使用 SQLite 自带备份命令：

```bash
sqlite3 data/xianyu_data.db ".backup 'backups/xianyu_data.db'"
```

---

## CLI 使用

CLI 是只读工具，适合脚本、Agent 和服务器检查。

### 安装 Agent 依赖

```bash
pip install -r requirements.txt
pip install -r agent-requirements.txt
```

### 配置连接信息

```bash
export XIANYU_BASE_URL=http://127.0.0.1:8080
export XIANYU_USERNAME=admin
export XIANYU_PASSWORD='你的管理后台密码'
```

不要把密码放在命令行参数中，避免出现在 shell 历史和进程列表里。

### 命令示例

```bash
# 服务状态
python -m xianyu_agent health

# 验证登录
python -m xianyu_agent verify

# 账号列表
python -m xianyu_agent accounts

# 订单列表
python -m xianyu_agent orders-list --status pending --page-size 20

# 指定账号查询订单
python -m xianyu_agent orders-list --account-id ACCOUNT_ID

# 订单详情
python -m xianyu_agent orders-show ORDER_ID

# 商品、卡券和规则
python -m xianyu_agent items
python -m xianyu_agent cards
python -m xianyu_agent delivery-rules
python -m xianyu_agent reply-rules ACCOUNT_ID

# 订单统计
python -m xianyu_agent analytics-orders \
  --start-date 2026-07-01 \
  --end-date 2026-07-30
```

所有命令输出统一 JSON：

```json
{
  "success": true,
  "data": {}
}
```

CLI 会移除订单收件信息、买家标识、账号 Cookie、卡券内容和 API 配置等敏感字段。

---

## MCP 使用

MCP Server 当前只提供读取能力，不包含发货、删除、导入、Cookie 修改、AI Key 修改或规则写入。

### stdio 模式

```bash
export XIANYU_BASE_URL=http://127.0.0.1:8080
export XIANYU_USERNAME=admin
export XIANYU_PASSWORD='你的管理后台密码'

python -m xianyu_agent.mcp_server
```

通用 MCP 客户端配置：

```json
{
  "command": "python",
  "args": ["-m", "xianyu_agent.mcp_server"],
  "env": {
    "XIANYU_BASE_URL": "http://127.0.0.1:8080",
    "XIANYU_USERNAME": "admin",
    "XIANYU_PASSWORD": "替换为实际密码"
  }
}
```

使用虚拟环境时，建议把 `command` 改为虚拟环境 Python 的绝对路径。

### Streamable HTTP 模式

```bash
XIANYU_MCP_TRANSPORT=streamable-http \
XIANYU_BASE_URL=http://127.0.0.1:8080 \
XIANYU_USERNAME=admin \
XIANYU_PASSWORD='你的管理后台密码' \
python -m xianyu_agent.mcp_server
```

实际监听地址和端口以启动日志为准。远程使用时必须增加 TLS、访问控制和网络隔离，不应把未鉴权的 MCP 端口直接暴露到公网。

### MCP 工具

| 工具 | 用途 |
|---|---|
| `xianyu_health` | 检查服务、数据库及 CookieManager 状态 |
| `xianyu_list_accounts` | 查看账号列表，不返回 Cookie |
| `xianyu_list_orders` | 查询订单列表 |
| `xianyu_get_order` | 查询订单详情 |
| `xianyu_list_items` | 查看已同步商品 |
| `xianyu_list_cards` | 查看卡券元数据，不返回发货内容 |
| `xianyu_list_delivery_rules` | 查看自动发货规则 |
| `xianyu_list_reply_rules` | 查看账号回复规则 |
| `xianyu_order_analytics` | 查询指定日期范围的订单统计 |

更完整的 Agent 说明见 [AGENT_USAGE.md](AGENT_USAGE.md)。

---

## 安全部署建议

推荐架构：

```text
浏览器 / MCP Client
        │ HTTPS
        ▼
Cloudflare Access、Nginx 或其他身份网关
        │
        ▼
127.0.0.1:8080  闲鱼超级管家
127.0.0.1:8000  MCP（按实际配置）
```

建议：

- Web 和 MCP 默认只绑定本机或私有网络
- 公网访问必须使用 HTTPS
- 使用 Cloudflare Tunnel、VPN、SSH Tunnel 或受控反向代理
- 为管理后台设置强密码并定期轮换
- 替换 `JWT_SECRET_KEY` 的默认值
- 关闭不需要的用户注册
- 限制服务器安全组和防火墙端口
- 定期备份 `data/`、`backups/` 和必要配置
- 不在代码、Compose、日志或 Git 中保存真实 Cookie 和密钥
- 开启写入型 Agent 工具前，应增加权限范围、审计日志、幂等键、预览和一次性确认令牌

---

## 常见问题

### 页面无法打开

```bash
docker compose ps
docker compose logs --tail=200 xianyu-app
curl -v http://127.0.0.1:8080/health
```

同时检查服务器防火墙、安全组和 `WEB_PORT`。

### Docker 构建前端失败

项目使用 `frontend/`、Node.js 20 和 PNPM。先清理缓存后重建：

```bash
docker compose build --no-cache xianyu-app
docker compose up -d
```

### Playwright 或 Chromium 启动失败

本地 Linux：

```bash
playwright install chromium
playwright install-deps chromium
```

Docker 镜像会安装 Chromium 及依赖。仍失败时检查容器内存、共享内存和日志。

### 闲鱼账号频繁失效

- 确认 Cookie 是否过期
- 检查账号是否触发验证或风控
- 不要在多个环境同时运行同一账号
- 查看 WebSocket、心跳和令牌刷新日志

### SQLite 数据库被锁定

- 避免同时启动多个 `Start.py` 实例
- 不要让多个容器写入同一个数据库文件
- 备份前减少写入操作
- 检查 `data/` 的文件权限和磁盘空间

### CLI 或 MCP 登录失败

```bash
curl http://127.0.0.1:8080/health
python -m xianyu_agent verify
```

确认 `XIANYU_BASE_URL`、用户名和密码与 Web 管理后台一致。HTTPS 使用自签名证书时，应正确导入 CA；`--insecure` 只适合临时诊断。

---

## 开发与测试

### 前端开发模式

终端 1：

```bash
python Start.py
```

终端 2：

```bash
cd frontend
corepack enable
pnpm install
pnpm dev
```

Vite 开发地址以终端输出为准。

### Agent 单元测试

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

### 贡献流程

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: describe your change"
git push origin feature/your-feature
```

随后创建 Pull Request，并确保敏感配置和测试数据未进入提交。

---

## 技术栈

- 后端：FastAPI、Python 3.11、SQLite、Playwright、WebSocket、Asyncio
- 前端：React 19、TypeScript、Vite、Tailwind CSS、Recharts
- Agent：httpx、MCP Python SDK、stdio / Streamable HTTP
- 部署：Docker Compose，可选 Nginx 或 Cloudflare Tunnel

---

## 开源协议与免责声明

本项目采用 [MIT License](LICENSE)。

> 本项目仅供学习和研究使用。使用者应遵守所在地法律法规、平台规则和账号安全要求；因部署、配置或使用本项目产生的后果由使用者自行承担。

---

<div align="center">

基于 [xianyu-auto-reply](https://github.com/zhinianboke/xianyu-auto-reply) 开发

</div>
