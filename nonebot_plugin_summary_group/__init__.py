import asyncio
from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil
from .Config import config, Config
from .Model import detect_model

model = detect_model()

__plugin_meta__ = PluginMetadata(
    name="群聊总结",
    description="使用 AI 分析群聊记录，生成讨论内容的总结。",
    usage="1.总结 [消息数量] ：生成该群最近消息数量的内容总结\n2.总结 [@群友] [消息数量] ：生成指定群友相关内容总结",
    type="application",
    homepage="https://github.com/StillMisty/nonebot_plugin_summary_group",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

summary_group = on_command("总结", priority=5, block=True)

cool_down = defaultdict(lambda: datetime.now())

if config.summary_in_png:
    require("nonebot_plugin_htmlrender")
    from nonebot_plugin_htmlrender import md_to_pic # type: ignore


async def get_group_msg_history(
    bot: Bot, group_id: int, count: int
) -> list[dict[str, str]]:
    """获取群聊消息记录"""
    messages = await bot.get_group_msg_history(group_id=group_id, count=count)

    # 预先收集所有需要查询的QQ号
    qq_set: set[str] = {
        segment["data"]["qq"]
        for msg in messages["messages"]
        for segment in msg["message"]
        if segment["type"] == "at"
    }

    # 批量获取成员信息
    qq_name: dict[str, str] = {}
    if qq_set:
        member_infos = await asyncio.gather(
            *(bot.get_group_member_info(group_id=group_id, user_id=qq) for qq in qq_set)
        )
        qq_name.update(
            {
                str(info["user_id"]): info["card"] or info["nickname"]
                for info in member_infos
            }
        )

    result = []
    for message in messages["messages"]:
        text_segments = []
        for segment in message["message"]:
            if segment["type"] == "text":
                text = segment["data"]["text"].strip()
                if text:  # 只添加非空文本
                    text_segments.append(text)
            elif segment["type"] == "at":  # 处理@消息，替换为昵称
                qq = segment["data"]["qq"]
                text_segments.append(f"@{qq_name[qq]}")

        if text_segments:  # 只处理有内容的消息
            sender = message["sender"]["card"] or message["sender"]["nickname"]
            result.append({sender: "".join(text_segments)})

    if result:  # 安全检查
        result.pop()  # 去除请求总结的命令

    return result


def parse_command_args(args: Message):
    """解析命令参数，返回QQ号和消息数量"""
    qq: int | None = None
    num: int | None = None
    for seg in args:
        if seg.type == "at":
            qq = seg.data["qq"]
        elif seg.type == "text" and seg.data["text"].strip().isdigit():
            num = int(seg.data["text"])
    return qq, num


@summary_group.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    qq, num = parse_command_args(args)

    # 如果没有数字或者@，则不处理
    if num is None and qq is None:
        return

    if num < config.summary_min_length or num > config.summary_max_length:
        await summary_group.finish(
            f"总结消息数量应在 {config.summary_min_length} 到 {config.summary_max_length} 之间。",
            at_sender=True,
        )

    # 冷却时间，针对人，而非群
    if config.summary_cool_down > 0:
        if (last_time := cool_down[event.user_id]) > datetime.now():
            await summary_group.finish(
                f"请等待 {ceil((last_time - datetime.now()).total_seconds())} 秒后再请求总结。",
                at_sender=True,
            )
        cool_down[event.user_id] = datetime.now() + timedelta(
            seconds=config.summary_cool_down
        )

    group_id = event.group_id
    messages = await get_group_msg_history(bot, group_id, num)
    if not messages:
        await summary_group.finish("未能获取到聊天记录。")

    if qq is None:
        # 总结整个群聊内容
        summary = await model.summary_history(
            messages, "请详细总结这个群聊的内容脉络，要有什么人说了什么，用中文回答。"
        )
    else:
        # 只针对某个用户的聊天内容进行总结
        member_info = await bot.get_group_member_info(group_id=group_id, user_id=qq)
        name: str = member_info["card"] or member_info["nickname"]
        summary = await model.summary_history(
            messages,
            f"请总结对话中与{name}相关的内容，用中文回答。",
        )
    if config.summary_in_png:
        img = await md_to_pic(
            summary,
            css_path=__file__.replace("__init__.py", "assert/github-markdown-dark.css"),
        )
        await summary_group.finish(MessageSegment.image(img))
    else:
        await summary_group.finish(summary.strip())
