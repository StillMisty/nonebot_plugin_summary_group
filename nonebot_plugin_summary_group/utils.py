import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import dropwhile
from math import ceil
from pathlib import Path

from nonebot import get_bot, require
from nonebot.adapters.onebot.v11 import Bot, MessageSegment

from .Config import config
from .Model import detect_model
from .Store import Store

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

if config.summary_in_png:
    require("nonebot_plugin_htmlrender")
    from nonebot_plugin_htmlrender import md_to_pic  # type: ignore

    async def generate_image(summary: str):
        return await md_to_pic(
            summary,
            css_path=(
                Path(__file__).parent / "assert" / "github-markdown-dark.css"
            ).resolve(),
        )


model = detect_model()
cool_down = defaultdict(lambda: datetime.now())


def validate_message_count(num: int) -> bool:
    """验证消息数量是否在合法范围内"""
    return num >= config.summary_min_length and num <= config.summary_max_length


def validate_cool_down(user_id: int) -> bool | int:
    """验证是否冷却"""
    if config.summary_cool_down > 0:
        if (last_time := cool_down[user_id]) > datetime.now():
            return ceil((last_time - datetime.now()).total_seconds())
        cool_down[user_id] = datetime.now() + timedelta(
            seconds=config.summary_cool_down
        )
    return False


async def process_message(messages, bot: Bot, group_id: int) -> str:
    # 预先收集所有被@的QQ号，同时过滤掉非法消息
    qq_set: set[str] = set()
    for msg in messages:
        valid_segments = [
            segment for segment in msg["message"] if isinstance(segment, dict)
        ]
        qq_set.update(
            segment["data"]["qq"]
            for segment in valid_segments
            if segment["type"] == "at"
        )
        msg["message"] = valid_segments

    # 将所有被@的QQ号转换为其群昵称
    qq_name = await fetch_member_nicknames(bot, group_id, qq_set)

    result = []
    for message in messages:
        text_segments = []
        for segment in message["message"]:
            if segment["type"] == "text":
                text = segment["data"]["text"].strip()
                if text:  # 只添加非空文本
                    text_segments.append(text)
            elif (
                segment["type"] == "at" and segment["data"]["qq"] in qq_name
            ):  # 处理@消息，替换为昵称
                text_segments.append(f"@{qq_name[segment['data']['qq']]}")

        if text_segments:  # 只处理有内容的消息
            sender = message["sender"]["card"] or message["sender"]["nickname"]
            result.append({sender: "".join(text_segments)})

    if result:  # 安全检查
        result.pop()  # 去除请求总结的命令

    return result


async def fetch_member_nicknames(
    bot: Bot, group_id: int, qq_set: set[str]
) -> dict[str, str]:
    """批量获取群成员的昵称"""
    qq_name: dict[str, str] = {}
    if qq_set:
        member_infos = await asyncio.gather(
            *(
                bot.get_group_member_info(group_id=group_id, user_id=qq)
                for qq in qq_set
            ),
            return_exceptions=True,
        )
        qq_name.update(
            {
                str(info["user_id"]): info["card"] or info["nickname"]
                for info in member_infos
                if not isinstance(info, Exception)
            }
        )

    return qq_name


async def get_group_msg_history(
    bot: Bot, group_id: int, count: int
) -> list[dict[str, str]]:
    """获取群聊消息记录"""
    messages = (await bot.get_group_msg_history(group_id=group_id, count=count))[
        "messages"
    ]

    return await process_message(messages, bot, group_id)


async def messages_summary(
    messages: list[dict[str, str]], content: str | None = None
) -> str:
    """使用模型对历史消息进行总结"""
    prompt = (
        f"请详细总结对话中仅与{content}相关的内容，用中文回答。"
        if content
        else "请详细总结这个群聊的内容脉络，要有什么人说了什么，用中文回答。"
    )
    return await model.summary_history(messages, prompt)


async def send_summary(bot: Bot, group_id: int, summary: str):
    """发送总结"""
    if config.summary_in_png:
        img = await generate_image(summary)
        await bot.send_group_msg(group_id=group_id, message=MessageSegment.image(img))
    else:
        await bot.send_group_msg(group_id=group_id, message=summary.strip())


async def scheduler_send_summary(group_id: int, least_message_count: int):
    """定时发送总结，总结消息范围为所设置总结条数中最近24小时内的消息，若消息数量小于总结最小值则不总结"""
    bot = get_bot()
    messages = (
        await bot.get_group_msg_history(group_id=group_id, count=least_message_count)
    )["messages"]

    if len(messages) < config.summary_min_length:
        return

    deadline = (datetime.now() - timedelta(hours=24)).timestamp()

    # 如果最小总结条数的消息时间在24小时前，则不进行总结
    if messages[-config.summary_min_length]["time"] <= deadline:
        return

    # 如果最大总结条数的消息时间在24小时前，则截取其中24小时内的消息
    if messages[0]["time"] <= deadline:
        messages = list(dropwhile(lambda msg: msg["time"] <= deadline, messages))

    messages = await process_message(messages, bot, group_id)

    summary = await messages_summary(messages)

    await send_summary(bot, group_id, summary)


def set_scheduler():
    """设置定时任务"""
    store = Store()
    for group_id, data in store.data.items():
        scheduler.add_job(
            scheduler_send_summary,
            "cron",
            hour=data["time"],
            args=(int(group_id), data["least_message_count"]),
            id=f"summary_group_{group_id}",
            replace_existing=True,
        )
