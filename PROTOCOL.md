# 邮件系统协议说明

## 消息格式

所有消息使用JSON格式，通过TCP协议传输，每条消息以换行符结尾。

### 客户端 -> 服务器消息结构

```json
{
  "type": "命令类型",
  "seq": 1,
  "from_user": "",
  "to": "",
  "body": {
    "命令参数": "值"
  },
  "signature": "",
  "session_token": ""
}
```

### 服务器 -> 客户端响应结构

```json
{
  "type": "RESPONSE",
  "seq": 1,
  "body": {
    "status": "SUCCESS|ERROR",
    "message": "信息",
    "data": {}
  }
}
```

## 消息类型

### 认证类

| 类型 | 用途 | 请求参数 | 响应 |
|------|------|----------|------|
| REGISTER | 注册 | username, password | status, message |
| LOGIN | 登录 | username, password | status, session_token, username, email |
| LOGOUT | 登出 | (无) | status, message |
| SESSION_TOKEN | 会话令牌 | (无) | session_token |

### 邮件操作类

| 类型 | 用途 | 请求参数 | 响应 |
|------|------|----------|------|
| SEND_EMAIL | 发送邮件 | to_users[], subject, body, attachments[] | status, mail_id |
| GET_INBOX | 获取收件箱 | (无) | status, emails[] |
| GET_SENT | 获取发件箱 | (无) | status, emails[] |
| GET_DRAFTS | 获取草稿箱 | (无) | status, emails[] |
| GET_EMAIL | 获取单个邮件 | mail_id | status, email |
| DELETE_EMAIL | 删除邮件 | mail_id | status, message |
| RECALL_EMAIL | 撤回邮件 | mail_id | status, message |
| SAVE_DRAFT | 保存草稿 | to_users[], subject, body, mail_id | status, mail_id |

### 群组功能类

| 类型 | 用途 | 请求参数 | 响应 |
|------|------|----------|------|
| CREATE_GROUP | 创建群组 | name | status, group_id |
| GET_GROUPS | 获取群组列表 | (无) | status, groups[] |
| ADD_GROUP_MEMBER | 添加群组成员 | group_id, member | status, message |

### 搜索功能类

| 类型 | 用途 | 请求参数 | 响应 |
|------|------|----------|------|
| SEARCH_EMAILS | 搜索邮件 | keyword | status, emails[] |

### 服务器间通信类

| 类型 | 用途 | 请求参数 | 响应 |
|------|------|----------|------|
| RELAY_EMAIL | 中转邮件 | from_domain, to_domain, mail_data | status |

## 认证流程

1. 客户端连接服务器
2. 客户端发送LOGIN请求
3. 服务器验证用户名密码
4. 服务器返回SESSION_TOKEN
5. 后续请求携带SESSION_TOKEN进行认证

## 安全机制

### 密码存储
- 使用SHA-256 + 随机盐值进行密码哈希存储
- 密码不加密传输（实际应使用HTTPS或加密通道）

### 登录保护
- 登录失败5次后锁定账户30分钟
- 登录频率限制：每分钟最多5次

### 发送限制
- 发送频率限制：每分钟最多20次

### 钓鱼检测
- 邮件主题和正文进行钓鱼关键词检测
- 风险分数 >= 0.5 标记为钓鱼邮件

## 邮件数据结构

```json
{
  "mail_id": "邮件唯一ID",
  "from_user": "发件人邮箱",
  "to_users": ["收件人邮箱列表"],
  "cc_users": ["抄送邮箱列表"],
  "bcc_users": ["密送邮箱列表"],
  "subject": "邮件主题",
  "body": "邮件正文",
  "attachments": [
    {
      "filename": "文件名",
      "content_type": "MIME类型",
      "size": "文件大小",
      "file_id": "文件唯一ID（用于去重）",
      "data": "Base64编码的文件内容"
    }
  ],
  "timestamp": "ISO格式时间戳",
  "is_read": false,
  "is_draft": false,
  "is_recalled": false,
  "folder": "inbox|sent|drafts",
  "keywords": ["关键词列表"],
  "is_spam": false,
  "is_phishing": false
}
```

## 用户数据结构

```json
{
  "username": "用户名",
  "password_hash": "密码哈希",
  "salt": "盐值",
  "email": "完整邮箱地址",
  "created_at": "创建时间",
  "groups": ["群组ID列表"],
  "failed_login_attempts": 0,
  "lock_until": "锁定截止时间"
}
```