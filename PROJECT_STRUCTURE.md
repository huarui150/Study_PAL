# StudyPAL+ 项目结构说明

## 📁 项目目录结构

```
flaskProject/
├── 📄 后端核心文件
│   ├── app.py                    # Flask主应用 (865行) - API路由和请求处理
│   ├── auth.py                   # 用户认证模块 (155行) - 注册登录逻辑
│   ├── achievement_service.py    # 成就服务 (771行) - 成就判定和奖励系统
│   ├── pomodoro_service.py       # 番茄钟服务 (427行) - 番茄钟计时和会话管理
│   ├── course_service.py         # 课程服务 (306行) - 课程CRUD操作
│   ├── material_service.py       # 资料服务 (438行) - 资料上传和处理
│   ├── card_service.py           # 卡片服务 (364行) - 知识卡片生成
│   ├── ai_chat_service.py        # AI聊天服务 (111行) - 基础AI对话
│   ├── smart_ai_service.py       # 智能AI服务 (216行) - 智能路由和图片直返
│   ├── rag_service.py            # RAG检索服务 (327行) - 文档检索增强
│   ├── activity_service.py       # 活动服务 (236行) - 用户活动记录
│   ├── db_service.py             # 数据库服务 (584行) - 数据库操作封装
│   ├── jwt_utils.py              # JWT工具 (110行) - Token生成和验证
│   ├── quiz_service.py           # 测验服务 (72行) - 测验题目管理
│   ├── create_tables.py          # 数据库初始化 (206行) - 表结构创建
│   ├── init_database.py          # 数据库初始化脚本 (166行) - 初始数据插入
│   └── requirements.txt          # Python依赖包列表
│
├── 📁 前端文件 (study-pal-frontend/src/)
│   ├── 📄 HTML页面
│   │   ├── index.html                # 首页 (125行) - 项目入口和重定向
│   │   ├── login.html                # 登录页 (70行) - 用户登录界面
│   │   ├── register.html             # 注册页 (87行) - 用户注册界面
│   │   ├── dashboard.html            # 仪表盘 (286行) - 学习统计和活动
│   │   ├── courses.html              # 课程列表 (372行) - 课程管理界面
│   │   ├── course-detail.html        # 课程详情 (483行) - 课程详细信息和资料
│   │   ├── plans.html                # 学习计划 (326行) - 计划创建和管理
│   │   ├── plan-detail.html          # 计划详情 (308行) - 计划执行和番茄钟
│   │   ├── achievements.html         # 成就页面 (211行) - 成就展示和统计
│   │   └── ai-tutor.html             # AI辅导 (210行) - 智能问答界面
│   │
│   ├── 📄 JavaScript文件
│   │   ├── config.js                 # 配置文件 (52行) - API地址和全局配置
│   │   ├── script.js                 # 通用脚本 (400行) - 公共函数和工具
│   │   ├── courses.js                # 课程逻辑 (349行) - 课程页面交互
│   │   ├── course-detail.js          # 课程详情逻辑 (547行) - 课程详情交互
│   │   ├── plans.js                  # 计划逻辑 (1068行) - 计划管理交互
│   │   ├── plan-detail.js            # 计划详情逻辑 (839行) - 番茄钟和计划执行
│   │   ├── achievements.js           # 成就逻辑 (589行) - 成就系统交互
│   │   └── ai-chat.js                # AI聊天逻辑 (357行) - AI对话交互
│   │
│   └── 📄 样式文件
│       └── styles.css                # 样式文件 (3606行) - 全局样式和组件样式
│
├── 📁 数据库文件
│   ├── database_schema.sql           # 数据库结构定义
│   └── uploads/                      # 上传文件存储目录
│
├── 📁 部署文件
│   ├── Dockerfile                    # Docker镜像配置
│   └── docker-compose.yml            # Docker编排配置
│
├── 📁 静态资源
│   ├── static/                       # 静态文件目录
│   └── templates/                    # 模板文件目录
│
└── 📄 其他文件
    ├── index.html                    # 重定向页面 (16行)
    └── README.md                     # 项目说明文档
```

## 🔧 核心模块说明

### 后端模块 (Backend Modules)

#### 1. **app.py** - 主应用入口
- **功能**：Flask应用主文件，定义所有API路由
- **主要路由**：
  - `/api/auth/*` - 用户认证
  - `/api/courses/*` - 课程管理
  - `/api/plans/*` - 学习计划
  - `/api/pomodoro/*` - 番茄钟
  - `/api/ai/*` - AI服务
  - `/api/achievements/*` - 成就系统

#### 2. **auth.py** - 用户认证
- **功能**：用户注册、登录、密码加密
- **技术**：Werkzeug密码哈希、JWT Token生成

#### 3. **achievement_service.py** - 成就系统
- **功能**：成就判定、StudyCoin奖励、事件处理
- **核心算法**：基于事件流的成就检测

#### 4. **pomodoro_service.py** - 番茄钟服务
- **功能**：番茄钟会话管理、自适应时长调整
- **核心算法**：基于中断率的时长自适应

#### 5. **db_service.py** - 数据库服务
- **功能**：数据库连接、CRUD操作封装
- **技术**：PyMySQL、连接池管理

#### 6. **smart_ai_service.py** - 智能AI服务
- **功能**：智能路由、图片直返、多模式问答
- **核心特性**：关键词匹配、图片快速响应

### 前端模块 (Frontend Modules)

#### 1. **dashboard.html/js** - 仪表盘
- **功能**：学习统计、近期活动、数据可视化
- **数据源**：番茄钟统计、成就数据、活动记录

#### 2. **courses.html/js** - 课程管理
- **功能**：课程列表、创建编辑、资料上传
- **交互**：拖拽上传、实时预览、批量操作

#### 3. **plans.html/js** - 学习计划
- **功能**：计划创建、AI优化建议、进度追踪
- **存储**：localStorage + 后端同步

#### 4. **plan-detail.html/js** - 计划详情
- **功能**：番茄钟计时、情绪打卡、进度更新
- **特性**：实时计时、中断处理、数据持久化

#### 5. **achievements.html/js** - 成就系统
- **功能**：成就展示、StudyCoin余额、动态反馈
- **特效**：粒子动画、音效反馈、进度条

#### 6. **ai-tutor.html/js** - AI辅导
- **功能**：智能问答、图片直返、多模式切换
- **特性**：实时对话、上下文记忆、智能路由

## 🗄️ 数据库设计

### 核心数据表

#### 1. **users** - 用户表
```sql
- id: 用户ID
- username: 用户名
- password_hash: 密码哈希
- email: 邮箱
- created_at: 创建时间
```

#### 2. **courses** - 课程表
```sql
- id: 课程ID
- user_id: 用户ID
- name: 课程名称
- weight: 权重
- color: 颜色
- exam_ratio: 考试比例
- created_at: 创建时间
```

#### 3. **materials** - 资料表
```sql
- id: 资料ID
- course_id: 课程ID
- title: 标题
- type: 类型 (pdf/ppt/doc/image)
- url: 文件路径
- file_hash: 文件哈希
- uploaded_at: 上传时间
```

#### 4. **pomodoro_sessions** - 番茄钟会话表
```sql
- id: 会话ID
- user_id: 用户ID
- plan_id: 计划ID
- start_at: 开始时间
- end_at: 结束时间
- duration: 计划时长
- actual_minutes: 实际时长
- status: 状态 (active/completed/interrupted)
- emotion: 情绪
- note: 备注
```

#### 5. **user_achievements** - 用户成就表
```sql
- id: 记录ID
- user_id: 用户ID
- achievement_id: 成就ID
- unlocked_at: 解锁时间
```

#### 6. **user_stats** - 用户统计表
```sql
- user_id: 用户ID
- studycoin_balance: StudyCoin余额
- login_streak: 连续登录天数
- total_focus_time: 总专注时长
- total_pomodoros: 总番茄数
```

## 🔄 数据流说明

### 1. 用户认证流程
```
用户注册/登录 → auth.py → JWT生成 → 前端存储 → API调用验证
```

### 2. 番茄钟流程
```
开始番茄 → pomodoro_service.py → 数据库记录 → 计时结束 → 情绪打卡 → 成就检查 → StudyCoin奖励
```

### 3. AI问答流程
```
用户提问 → smart_ai_service.py → 关键词匹配 → 图片直返 或 LLM问答 → 返回结果
```

### 4. 成就解锁流程
```
用户行为 → 事件触发 → achievement_service.py → 条件检查 → 成就解锁 → 奖励发放 → 前端反馈
```

## 🛠️ 开发规范

### 代码组织
- **模块化设计**：每个功能模块独立文件
- **服务层分离**：业务逻辑与数据访问分离
- **前后端分离**：API接口与前端界面分离

### 命名规范
- **Python文件**：snake_case (如: `achievement_service.py`)
- **JavaScript文件**：kebab-case (如: `ai-chat.js`)
- **HTML文件**：kebab-case (如: `course-detail.html`)
- **数据库表**：snake_case (如: `pomodoro_sessions`)

### API设计
- **RESTful风格**：GET/POST/PUT/DELETE
- **统一响应格式**：JSON格式，包含状态码和消息
- **错误处理**：统一的错误响应格式

### 数据库设计
- **主键**：自增ID
- **外键**：关联完整性约束
- **索引**：查询性能优化
- **时间戳**：创建和更新时间记录

## 📊 项目统计

### 代码规模
- **后端代码**：约8000行Python代码
- **前端代码**：约6000行JavaScript代码
- **样式文件**：64KB CSS样式
- **HTML页面**：10个主要页面

### 功能模块
- **认证模块**：用户注册、登录、JWT管理
- **课程模块**：课程CRUD、资料上传、知识卡片
- **计划模块**：学习计划、AI优化、进度追踪
- **番茄模块**：多模式计时、情绪打卡、数据统计
- **AI模块**：智能问答、图片直返、RAG检索
- **成就模块**：成就系统、StudyCoin、动态反馈

### API接口
- **认证接口**：2个 (注册、登录)
- **课程接口**：5个 (CRUD操作)
- **计划接口**：5个 (CRUD操作)
- **番茄接口**：4个 (开始、完成、中断、统计)
- **AI接口**：2个 (聊天、智能问答)
- **成就接口**：3个 (查询、检查、测试)
- **其他接口**：10+个 (活动、统计、文件等)

## 🚀 部署架构

### 开发环境
```
前端 (浏览器) ←→ 后端 (Flask) ←→ 数据库 (MySQL)
```

### 生产环境 (Docker)
```
Nginx (静态文件) ←→ Flask API ←→ MySQL
```

### 服务依赖
- **Flask应用**：依赖MySQL数据库
- **前端页面**：依赖Flask API服务
- **AI服务**：依赖通义千问API (可选)

---

**StudyPAL+** - 项目结构清晰，模块化设计，便于维护和扩展 🚀
