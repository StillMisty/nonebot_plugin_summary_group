<div align="center">
  <a href="https://nonebot.dev/store/plugins">
    <img src="./docs/NoneBotPlugin.svg" width="300" alt="logo">
  </a>
</div>
<div align="center">

# nonebot_plugin_summary_group

</div>

## 📖 介绍

基于Nonebot2，使用 AI 分析群聊记录，生成讨论内容的总结，亦或是总结特定人或事。

## 💿 安装

使用nb-cli安装插件

```shell
nb plugin install nonebot_plugin_summary_group
```

使用pip安装插件

```shell
pip install nonebot_plugin_summary_group
```

## ⚙️ 配置

### AI 账户配置项

每个账户（Gemini/OpenAI）都支持以下基础配置，至少填写一个账户，填多个时，当默认API错误时可根据优先级依次降级处理：

- `nickname`: 账户的唯一别名，作为首先调用的模型（必填）
- `api_key`: 该账户的 API Key（必填）
- `model`: 该账户要使用的模型名称（必填）
- `proxy`: 为该账户单独设置代理
- `time_out`: 该账户的 API 请求超时时间(秒)，默认 60

#### OpenAI 兼容格式特定配置

- `provider`: 固定为 "openai"（必填）
- `base_url`: OpenAI API 兼容格式的访问地址（必填）

#### Gemini 特定配置

- `provider`: 固定为 "gemini"（必填）

#### AI 账户配置示例

```env
# Gemini 配置
ai_accounts__0__provider="gemini"
ai_accounts__0__nickname="gemini-1"
ai_accounts__0__api_key="your_gemini_api_key"
ai_accounts__0__model="gemini-2.5-flash"

# OpenAI 配置
ai_accounts__1__provider="openai"
ai_accounts__1__nickname="deepseek-1"
ai_accounts__1__base_url="https://api.deepseek.com"
ai_accounts__1__api_key="your_openai_api_key"
ai_accounts__1__model="deepseek-chat"

# 根据需要可添加更多账户配置
# ai_accounts__3__...
```

### 功能配置项

如无特殊需求，使用默认配置即可：

|          配置项          | 类型  | 默认值 |                           说明                           |
| :----------------------: | :---: | :----: | :------------------------------------------------------: |
| default_account_nickname |  str  |  None  | 默认使用的账户别名。如果未设置，将使用列表中的第一个账户 |
|    summary_max_length    |  int  |  1000  |                  总结内容的最大长度限制                  |
|    summary_min_length    |  int  |   50   |                  总结内容的最小长度限制                  |
|    summary_cool_down     |  int  |   0    |            单个用户调用总结功能的冷却时间(秒)            |
|      summary_in_png      | bool  |  True  |               是否将总结结果以图片形式发送               |
|  summary_max_queue_size  |  int  |   10   |              等待处理的总结任务队列最大数量              |
|  summary_queue_timeout   |  int  |  300   |            任务在队列中等待处理的超时时间(秒)            |
|  summary_queue_workers   |  int  |   2    |               同时处理总结任务的最大并发数               |

## 🕹️ 使用

**总结 [消息数量] [特定内容?]** ：生成该群最近消息数量的总结或指定内容的总结，特定内容为可选项。

**总结定时 [时间] [最少消息数量?=summary_max_length]** ：定时生成消息数量的内容总结，时间：0~23，最少消息数量：默认为总结最大长度，每群的定时总结独立计算，默认不启用。

**总结定时取消** ：取消本群的定时内容总结。

## 🙏 感谢

[github-markdown-css](https://github.com/sindresorhus/github-markdown-css) - 用于美化Markdown文档
