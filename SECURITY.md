# Security policy

## Supported versions

安全修复当前只针对最新发布版本。

## Reporting

请不要通过公开 Issue 披露漏洞。使用 GitHub 的 Private vulnerability
reporting 功能提交报告，并包含影响、复现步骤和建议修复方式。

请勿在报告中包含真实用户数据、密码、Cookie、令牌或其他凭据。

## Resume data

简历属于敏感个人数据。InternFlow 默认只在本机或自托管实例中解析，
不会把文件或提取文本发送到外部 API。部署者需要为 `media/` 配置持久化
存储、备份和访问控制，并确保 Web 服务器不会公开列出上传目录。
