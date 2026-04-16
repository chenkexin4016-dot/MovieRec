### 前端框架：Vue 3 + Element Plus

* 目前采用的是：Vue 3 + FastAPI 架构；早年多采用前端技术是 HTML + jQuery，配合 Django 的后端模板渲染，这是比较传统的“前后端不分离”做法

#### frontend初始化项目环境(Node.js)

```bash
# 1. 创建 Vue 3 项目 (按提示操作，项目名可以叫 frontend，其他选项全选 No 即可)
npm create vue@latest
# 2. 进入项目目录
cd frontend
# 3. 安装项目依赖
npm install
# 4. 安装 Element Plus (UI 组件库) 和 图标库
npm install element-plus @element-plus/icons-vue
# 前端终端
npm run dev
# 后端终端
uvicorn main:app --reload
```

#### ORM 框架 SQLAlchemy-SQLite
