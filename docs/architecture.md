# 架构设计

## 选择

InternFlow 使用 Django 模块化单体。页面由服务端模板渲染，HTMX 只负责
看板状态切换和筛选等局部更新。

## 请求路径

```text
浏览器
  -> Django URL 路由
  -> 登录与所有权检查
  -> Form / Service 业务规则
  -> PDF / DOCX 本地文本提取与可解释分析
  -> Django ORM
  -> SQLite（本地）或 PostgreSQL（容器/生产）
  -> HTML 页面或 HTMX 局部模板
```

## 边界

- `config/`：全局配置、根路由和部署入口。
- `jobs/`：岗位、状态历史及其业务逻辑。
- `jobs/services/`：简历提取分析与面试清单生成，不依赖 HTTP。
- `templates/`：页面和可复用局部模板。
- `static/`：项目样式和少量渐进增强脚本。
- `tests/`：模型、权限、视图和关键流程测试。

## 安全原则

- 所有岗位查询都以 `request.user` 为第一过滤条件。
- 修改类请求只接受 POST。
- 使用 Django CSRF、密码散列、会话与表单校验。
- 简历只接受 PDF / DOCX，限制 5 MB，并使用不透明存储名。
- 简历、分析结果和面试清单都通过当前用户所属关系查询。
- 生产配置从环境变量读取，不提交密钥。
- 部署前执行 `manage.py check --deploy`。

## 为什么不用前后端分离

首个版本的主要风险是产品是否有用，而不是 API 吞吐量。服务端渲染可以
减少重复的数据校验、鉴权和状态管理，让一名维护者更快交付可靠版本。
未来若出现浏览器插件或移动端需求，再从稳定的业务层抽取 API。

## 简历分析边界

`ResumeProfile` 保存原文件、提取文本和 JSON 分析结果。
`resume_analysis.py` 负责纯文本信号分析，`interview_prep.py` 负责把分析
结果与岗位信息组合为 `InterviewPrepItem`。视图只编排上传、权限和事务，
因此规则能够被独立测试，也便于未来增加明确授权的可替换分析器。
