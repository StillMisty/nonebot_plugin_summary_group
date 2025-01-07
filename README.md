# nonebot_plugin_summary_group

## 📖 介绍

基于Nonebot2，使用 AI 分析群聊记录，生成讨论内容的总结。

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

在机器人文件夹的`env`文件中添加下表中配置项。

|       配置项       |      必填      |       默认       |                   说明                    |
| :----------------: | :------------: | :--------------: | :---------------------------------------: |
|     gemini_key     | 与openai二选一 |       None       |              gemini接口密钥               |
|  openai_base_url   | 与gemini二选一 |       None       |              openai接口地址               |
|   openai_api_key   | 与gemini二选一 |       None       |              openai接口密钥               |
|   summary_model    |       是       | gemini-1.5-flash |                 模型名称                  |
|       proxy        |       否       |       None       |                 代理设置                  |
| summary_max_length |       否       |       2000       |               总结最大长度                |
| summary_min_length |       否       |        50        |               总结最小长度                |
| summary_cool_down  |       否       |        0         | 总结冷却时间（0即无冷却，针对人，而非群） |
|      time_out      |       否       |       120        |             API 请求超时时间              |
|   summary_in_png   |       否       |      False       |          总结是否以图片形式发送           |

- 使用Gemini需要配置 gemini_key 与 summary_model。
- 使用OpenAI兼容的API则需要配置 openai_base_url 、 openai_api_key 与 summary_model。

若同时配置Gemini与OpenAI，则优先使用Gemini。

若以图片形式发送，使用[hyrious/github-markdown-css](https://github.com/hyrious/github-markdown-css)渲染markdown文本样式。

## 🕹️ 使用

**总结 [消息数量]** ：生成该群最近消息数量的内容总结

**总结 [@群友] [消息数量]** ：生成指定群友相关内容总结

注：默认总结消息数量范围50~2000，使用无冷却时间
