# 🎬 智影推荐系统

基于 Vue 3 + FastAPI 构建的智能电影推荐引擎。支持多路召回策略（Item-CF 协同过滤、TF-IDF 文本相似度），内置独立的反爬虫数据管道与静态资源管理。

## ✨ 核心特性

- **多算法 A/B 路由**：前端一键切换“协同过滤”、“剧情相似”、“全站热门”等推荐算法。
- **硬核 NLP 引擎**：基于 `jieba` 分词与 `scikit-learn` TF-IDF 算法，实现电影长剧情简介的向量化与余弦相似度推荐。
- **全自动数据管道**：内置 Python 爬虫脚本，支持防盗链破解、海报本地化与数据库 Upsert（覆盖更新）幂等导入。
- **极客暗黑 UI**：基于 Element Plus 打造的沉浸式响应式瀑布流，支持一键切换日间/夜间模式。

## 🛠️ 技术栈

- **前端**: Vue 3 (Composition API), Element Plus, Vite
- **后端**: FastAPI, Python 3.10+, SQLAlchemy, JWT Auth
- **算法**: Scikit-learn, Jieba, 协同过滤 (Item-Based CF)
- **数据库**: SQLite

## 🚀 快速启动

### 1. 后端环境准备
```bash
cd backend
pip install -r requirements.txt