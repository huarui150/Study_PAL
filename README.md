好的 👍 我帮你改写一下你的 `README.md`，按照比赛要求来：

1. **明确选择的赛题**
2. **项目创意说明**（核心创新点 + 为什么做这个）
3. **实现功能**（精简但全面，突出亮点功能）
4. **运行/部署指南**（本地运行 + 线上部署链接）
5. **可执行成果说明**（明确Release、部署地址）
6. 保持Markdown简洁美观

我帮你选了一个最符合的赛题方向：
👉 **“AI赋能学习与教育”**（StudyPAL+ 完全是 AI 学习伙伴，匹配度最高）。

这是修改后的版本：

---

# StudyPAL+ AI学习伙伴

> **参赛赛题：AI赋能学习与教育**
> **访问地址**：[http://study.linyang.ink/](http://study.linyang.ink/)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 项目简介

**StudyPAL+** 是一个基于 **Flask + 前后端分离架构** 的智能学习伙伴系统。
它集成了 **课程知识库、学习计划、番茄钟、AI智能辅导、成就激励** 等功能，利用 **AI大模型** 为学生提供个性化的学习体验与高效的学习管理。

---

## 💡 项目创意

在信息爆炸与学习任务繁重的环境下，很多同学面临：

* 学习规划不合理，效率低下
* 缺乏反馈与激励，容易放弃
* 资料分散，难以组织

**StudyPAL+** 的创意在于：

1. **AI赋能学习全流程**：从资料整理、知识点提炼到智能答疑，提升学习效率。
2. **智能计划与番茄钟结合**：通过算法推荐学习顺序，并自适应调整专注时长。
3. **游戏化激励机制**：学习获得虚拟货币与成就解锁，提升学习动力。

---

## ✨ 核心功能

* **课程知识库**：上传PDF/PPT/Word等资料，自动生成知识卡片与测验题
* **学习计划管理**：AI优化学习顺序，实时追踪进度
* **番茄钟系统**：多模式计时，自适应调整，支持情绪打卡
* **AI智能辅导**：课程问答、学习助教、校园助手
* **成就激励体系**：18类成就、虚拟货币奖励、粒子动画反馈

---

## 🚀 运行与部署

### 在线体验

已部署版本：[http://study.linyang.ink/](http://study.linyang.ink/)

### 本地运行

#### 环境要求

* Python 3.8+
* MySQL 8.0+
* 现代浏览器（支持ES6+）

#### 安装步骤

```bash
# 克隆项目
git clone <repository-url>
cd flaskProject

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
mysql -u root -p
CREATE DATABASE studypal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
python create_tables.py

# 启动服务
python app.py
```

前端：直接用浏览器打开 `study-pal-frontend/src/index.html`

### Docker部署

```bash
docker-compose up -d
```

---

## 📦 可执行成果

* **部署网站**：[http://study.linyang.ink/](http://study.linyang.ink/)
* **可执行文件**：将在仓库 **Release 区** 发布（安装包/部署文件）

---

## 📄 许可证

本项目采用 **MIT License**

---

✨ **StudyPAL+** —— 让AI成为学习的最佳伙伴


