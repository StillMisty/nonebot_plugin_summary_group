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
|     gemini_key     | 与OpenAI二选一 |       None       |              gemini接口密钥               |
|  openai_base_url   | 与Gemini二选一 |       None       |              openai接口地址               |
|   openai_api_key   | 与Gemini二选一 |       None       |              openai接口密钥               |
|   summary_model    |       是       | gemini-2.0-flash |                 模型名称                  |
|       proxy        |       否       |       None       |                 代理设置                  |
| summary_max_length |       否       |       1000       |               总结最大长度                |
| summary_min_length |       否       |        50        |               总结最小长度                |
| summary_cool_down  |       否       |        0         | 总结冷却时间（0即无冷却，针对人，而非群） |
|      time_out      |       否       |       120        |             API 请求超时时间              |
|   summary_in_png   |       否       |      False       |          总结是否以图片形式发送           |

- 使用Gemini需要配置 gemini_key 与 summary_model。
- 使用OpenAI兼容的API则需要配置 openai_base_url 、 openai_api_key 与 summary_model。

若同时配置Gemini与OpenAI，则优先使用Gemini。

使用`nonebot_plugin_htmlrender`渲染图片，为节省不必要的消耗，此包不会作为该项目依赖，需要自行安装并设置`summary_in_png=True`以使用图片发送。

``` shell
nb plugin install nonebot_plugin_htmlrender
```

## 🕹️ 使用

**总结 [消息数量] [特定内容?]** ：生成该群最近消息数量的总结或指定内容的总结，特定内容为可选项。

**总结定时 [时间] [最少消息数量?=summary_max_length]** ：定时生成消息数量的内容总结，时间：0~23，最少消息数量：默认为总结最大长度，每群的定时总结独立计算，默认不启用。

**总结定时取消** ：取消本群的定时内容总结。
