# StudyPAL+ AI学习伙伴

> **基于Flask的智能学习管理系统** - 前后端分离架构

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 项目简介

StudyPAL+ 是一个基于Flask框架开发的智能学习管理系统，采用前后端分离架构。系统集成了用户认证、课程管理、学习计划、番茄钟计时、AI智能问答、成就激励等核心功能，为用户提供个性化的学习体验。

## ✨ 核心功能

### 🔐 用户认证系统
- **用户注册/登录**：基于JWT的认证机制
- **密码加密**：使用Werkzeug进行密码哈希
- **会话管理**：Token自动过期和刷新

### 📚 课程知识库
- **课程管理**：创建、编辑、删除课程，支持权重和颜色设置
- **资料上传**：支持PDF、PPT、Word、图片格式
- **知识卡片**：自动生成摘要、关键点、名词解释、例题
- **测验系统**：基于内容生成测验题目
- **RAG检索**：基于文档内容的智能问答

### 🍅 番茄钟系统
- **多模式支持**：标准模式(25/5)、深度模式(50/10)、冲刺模式(35/7)
- **自适应调整**：根据历史中断率动态调整时长
- **情绪打卡**：专注结束后记录情绪状态
- **中断管理**：超过90秒中断计为失败
- **数据持久化**：所有会话数据保存到MySQL数据库

### 📋 学习计划管理
- **计划创建**：支持课程关联、预估时长、重要性设置
- **AI优化建议**：基于多维度算法推荐学习顺序
- **进度追踪**：实时监控计划完成情况
- **本地存储**：使用localStorage保存计划数据

### 🤖 AI智能辅导
- **智能问答**：集成通义千问API进行智能对话
- **图片直返**：四类固定信息（班车、校历、地图、系统状态）直接返回图片
- **学习助教**：课程内容相关问答
- **生活助理**：校园信息查询

### 🏆 成就激励系统
- **StudyCoin经济**：完成番茄钟获得虚拟货币奖励
- **成就体系**：18项成就分类（入门、学习、资料、测验、复盘、情绪、计划、生活、经济、荣誉）
- **动态反馈**：粒子特效和音效反馈
- **数据统计**：学习时长、番茄数量、连续登录等统计

## 🏗️ 技术架构

### 后端技术栈
- **框架**：Flask 2.3.3
- **数据库**：MySQL 8.0+
- **ORM**：PyMySQL 1.1.0
- **认证**：PyJWT 2.8.0
- **CORS**：Flask-CORS 4.0.0
- **AI集成**：zhipuai 2.0.1, openai 1.58.1
- **文档处理**：PyPDF2 3.0.1, python-pptx 0.6.21, python-docx 0.8.11

### 前端技术栈
- **语言**：HTML5 + CSS3 + JavaScript
- **样式**：自定义CSS框架（64KB样式文件）
- **交互**：原生JavaScript + Fetch API
- **存储**：localStorage + 后端API

### 数据库设计
- **用户表**：用户信息、认证数据
- **课程表**：课程管理、权重设置
- **资料表**：学习资料、文件管理
- **卡片表**：知识卡片、测验数据
- **嵌入表**：向量检索数据
- **计划表**：学习计划、进度追踪
- **会话表**：番茄钟会话记录
- **成就表**：用户成就、奖励记录
- **统计表**：用户学习统计

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MySQL 8.0+
- 现代浏览器（支持ES6+）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd flaskProject
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **配置数据库**
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE studypal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 初始化数据库表
python create_tables.py
```

4. **启动后端服务**
```bash
python app.py
```

5. **访问前端**
```bash
# 直接用浏览器打开
study-pal-frontend/src/index.html
```

## 📖 API接口文档

### 认证相关
```http
POST /api/auth/register
POST /api/auth/login
```

### 系统健康检查
```http
GET /api/health
GET /api/test-images
```

### 课程管理
```http
GET    /api/courses
POST   /api/courses
GET    /api/courses/{course_id}
PUT    /api/courses/{course_id}
DELETE /api/courses/{course_id}
```

### 资料管理
```http
POST   /api/materials
GET    /api/materials/{material_id}
GET    /api/cards/{material_id}
POST   /api/ask-doc
```

### 学习计划
```http
GET    /api/plans
POST   /api/plans
GET    /api/plans/{plan_id}
PUT    /api/plans/{plan_id}
DELETE /api/plans/{plan_id}
```

### 番茄钟
```http
POST   /api/pomodoro/start
POST   /api/pomodoro/complete
POST   /api/pomodoro/interrupt
GET    /api/pomodoro/stats
GET    /api/plan/suggestions
```

### AI辅导
```http
POST   /api/ai/chat
POST   /api/chat
```

### 成就系统
```http
GET    /api/achievements
POST   /api/achievements/check/{user_id}
POST   /api/achievements/test/{user_id}
GET    /api/activities
```

## 📁 项目结构

```
flaskProject/
├── 后端核心文件
│   ├── app.py                    # Flask主应用 (865行)
│   ├── auth.py                   # 用户认证模块 (155行)
│   ├── achievement_service.py    # 成就服务 (771行)
│   ├── pomodoro_service.py       # 番茄钟服务 (427行)
│   ├── course_service.py         # 课程服务 (306行)
│   ├── material_service.py       # 资料服务 (438行)
│   ├── card_service.py           # 卡片服务 (364行)
│   ├── ai_chat_service.py        # AI聊天服务 (111行)
│   ├── smart_ai_service.py       # 智能AI服务 (216行)
│   ├── rag_service.py            # RAG检索服务 (327行)
│   ├── activity_service.py       # 活动服务 (236行)
│   ├── db_service.py             # 数据库服务 (584行)
│   ├── jwt_utils.py              # JWT工具 (110行)
│   ├── quiz_service.py           # 测验服务 (72行)
│   ├── create_tables.py          # 数据库初始化 (206行)
│   ├── init_database.py          # 数据库初始化脚本 (166行)
│   └── requirements.txt          # Python依赖
├── 前端文件 (study-pal-frontend/src/)
│   ├── index.html                # 首页 (125行)
│   ├── login.html                # 登录页 (70行)
│   ├── register.html             # 注册页 (87行)
│   ├── dashboard.html            # 仪表盘 (286行)
│   ├── courses.html              # 课程列表 (372行)
│   ├── course-detail.html        # 课程详情 (483行)
│   ├── plans.html                # 学习计划 (326行)
│   ├── plan-detail.html          # 计划详情 (308行)
│   ├── achievements.html         # 成就页面 (211行)
│   ├── ai-tutor.html             # AI辅导 (210行)
│   ├── config.js                 # 配置文件 (52行)
│   ├── script.js                 # 通用脚本 (400行)
│   ├── courses.js                # 课程逻辑 (349行)
│   ├── course-detail.js          # 课程详情逻辑 (547行)
│   ├── plans.js                  # 计划逻辑 (1068行)
│   ├── plan-detail.js            # 计划详情逻辑 (839行)
│   ├── achievements.js           # 成就逻辑 (589行)
│   ├── ai-chat.js                # AI聊天逻辑 (357行)
│   └── styles.css                # 样式文件 (3606行)
├── 数据库文件
│   ├── database_schema.sql       # 数据库结构
│   └── uploads/                  # 上传文件目录
├── 部署文件
│   ├── Dockerfile                # Docker镜像配置
│   └── docker-compose.yml        # Docker编排配置
└── 其他文件
    ├── static/                   # 静态资源
    ├── templates/                # 模板文件
    └── index.html                # 重定向页面
```

## 🎮 功能演示

### 1. 用户注册登录
- 访问 `login.html` 进行用户注册或登录
- 系统使用JWT进行身份验证
- 登录后自动跳转到仪表盘

### 2. 课程管理
- 在课程页面创建和管理课程
- 支持设置课程权重、颜色、考试比例
- 上传学习资料（PDF、PPT、Word、图片）

### 3. 学习计划
- 创建学习计划，设置关联课程、预估时长、重要性
- 系统提供AI优化建议
- 支持计划编辑和删除

### 4. 番茄钟学习
- 选择计划开始专注学习
- 支持多种番茄钟模式
- 完成后进行情绪打卡，获得StudyCoin奖励
- 数据自动保存到数据库

### 5. AI智能辅导
- 在学习模式下提问课程相关问题
- 在生活模式下查询校园信息
- 支持图片直返功能

### 6. 成就系统
- 完成各种学习活动自动解锁成就
- 查看成就进度和StudyCoin余额
- 享受粒子特效和音效反馈

## 🔧 核心算法

### 自适应番茄钟算法
```python
# 基于历史中断率动态调整时长
def calculate_adaptive_duration(user_id):
    recent_sessions = get_recent_sessions(user_id, 3)
    interruption_rate = calculate_interruption_rate(recent_sessions)
    
    if interruption_rate > 0.5:
        return 22  # 缩短时长
    elif interruption_rate < 0.2:
        return 28  # 延长时长
    else:
        return 25  # 标准时长
```

### 智能计划优化算法
```python
# 多维度评分算法
def calculate_plan_score(plan, history, emotions):
    urgency = max(0, 1 - days_to_deadline(plan.deadline) / 7)
    priority = 0.5 * plan.importance + 0.5 * urgency
    retention = calculate_retention_need(plan.topic, history)
    fatigue = calculate_fatigue(emotions, history)
    
    return 0.4 * priority + 0.3 * retention + 0.3 * (1 - fatigue)
```

## 🚀 部署说明

### Docker部署
```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 访问应用
http://localhost:80
```

### 传统部署
```bash
# 安装依赖
pip install -r requirements.txt

# 配置数据库
python create_tables.py

# 启动服务
python app.py
```

## 📊 数据统计

### 当前项目规模
- **后端代码**：约8000行Python代码
- **前端代码**：约6000行JavaScript代码
- **样式文件**：64KB CSS样式
- **数据库表**：10+个核心数据表
- **API接口**：30+个RESTful接口

### 功能模块
- **认证模块**：用户注册、登录、JWT管理
- **课程模块**：课程CRUD、资料上传、知识卡片
- **计划模块**：学习计划、AI优化、进度追踪
- **番茄模块**：多模式计时、情绪打卡、数据统计
- **AI模块**：智能问答、图片直返、RAG检索
- **成就模块**：成就系统、StudyCoin、动态反馈

## 🤝 开发说明

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py

# 前端开发
# 直接编辑 study-pal-frontend/src/ 下的文件
```

### 代码规范
- 后端使用Python PEP8规范
- 前端使用ES6+语法
- 数据库使用MySQL 8.0+
- API遵循RESTful设计原则

## 📄 许可证

本项目采用 MIT 许可证

## 🙏 致谢

- 感谢Flask框架提供的Web开发能力
- 感谢MySQL数据库的稳定支持
- 感谢通义千问提供的AI能力

---

**StudyPAL+** - 让学习更高效，让AI成为你的学习伙伴 🚀
