# InternFlow

[![CI](https://github.com/IAMWHOAAA/internflow/actions/workflows/ci.yml/badge.svg)](https://github.com/IAMWHOAAA/internflow/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-176b4d)](https://www.python.org/)
[![Django 5.2 LTS](https://img.shields.io/badge/Django-5.2%20LTS-176b4d)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-dff257)](LICENSE)

面向学生的隐私友好型求职工作台。从六阶段投递看板，到本地简历分析，
再到基于简历与岗位 JD 的面试复习清单，把求职变成一条可执行的流程。

![InternFlow 投递工作台](assets/dashboard-preview.svg)

## 功能

- 注册、登录与严格的用户数据隔离
- 岗位创建、查看、编辑和删除
- 待投递、已投递、笔试、面试、Offer、已结束六阶段看板
- 关键词搜索、进度筛选和 HTMX 局部刷新
- 优先级、工作方式、地点、薪资、截止日期、JD 与个人笔记
- 状态变更历史、投递统计和 7 天内截止提醒
- PDF / DOCX 简历本地提取与可解释的优缺点分析
- 结构、量化成果、技术关键词和个人贡献评分
- 根据简历短板、岗位 JD 与项目经历生成可勾选的面试清单
- 注册时实时密码强度与一致性反馈，服务端同步执行强度校验
- SQLite 零配置开发，Docker Compose + PostgreSQL 一键运行
- 41 项自动化测试、93% 分支覆盖率、Ruff 与 GitHub Actions CI

## 为什么做它

招聘网站负责展示岗位，但学生仍要在表格、聊天收藏和日历之间手工整理
投递记录。InternFlow 提供一个可本地运行、可自行部署、围绕学生求职流程
设计的开源替代方案。

## 快速开始

需要 [uv](https://docs.astral.sh/uv/) 和 Python 3.13：

```bash
git clone https://github.com/IAMWHOAAA/internflow.git
cd internflow
cp .env.example .env
uv sync --locked --dev
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

打开 <http://127.0.0.1:8000>。`seed_demo` 会输出本地演示账号；不要在生产
环境使用演示密码。

也可以使用 Docker 与 PostgreSQL：

```bash
docker compose up --build
docker compose exec web python manage.py seed_demo
```

## 技术设计

InternFlow 采用 Django 模块化单体和服务端渲染。HTMX 只做渐进增强，因此
禁用 JavaScript 后，创建、编辑、删除、状态更新和清单操作仍能完成。

```text
浏览器 → Django 路由 → 登录与所有权检查 → Form / Service → ORM
                                              ↓              ↓
                                      PDF / DOCX 解析   SQLite / PostgreSQL
```

所有详情和修改查询都会同时匹配记录 ID 与当前用户；状态更新使用数据库
事务和不可变历史记录。生产镜像以非 root 用户运行，并由 WhiteNoise 提供
带内容指纹的静态文件。

简历分析不调用第三方服务：`pypdf` 与 `python-docx` 在本机提取文本，
确定性规则分析结构与证据信号。上传仅接受 PDF / DOCX 且限制为 5 MB，
文件名会替换为不可预测的存储名称。

## 质量检查

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest --cov
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
```

## 文档

- [产品范围](docs/product.md)
- [架构设计](docs/architecture.md)
- [开发路线](docs/roadmap.md)
- [面试学习笔记](docs/interview-notes.md)
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)

## 参与贡献

欢迎提交 Issue 和 Pull Request。开始前请阅读[贡献指南](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
