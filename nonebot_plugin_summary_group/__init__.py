from arclet.alconna import AllParam
from nonebot import get_driver, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .Config import Config, config
from .Store import Data, Store
from .utils.utils import (
    get_group_msg_history,
    messages_summary,
    send_summary,
    set_scheduler,
    validate_cool_down,
    validate_group_event,
    validate_message_count,
)

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (  # noqa: E402
    Alconna,
    Args,
    CommandMeta,
    Match,
    on_alconna,
)
from nonebot_plugin_alconna.uniseg.segment import At  # noqa: E402

__plugin_meta__ = PluginMetadata(
    name="群聊总结",
    description="使用 AI 分析群聊记录，生成讨论内容的总结。",
    usage="1.总结 [消息数量] [内容] ：生成该群最近消息数量的内容总结或指定内容总结\n2.总结定时 [时间] [最少消息数量] ：定时生成消息数量的内容总结\n3.总结定时取消 ：取消本群的定时内容总结",
    type="application",
    homepage="https://github.com/StillMisty/nonebot_plugin_summary_group",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

summary_group = on_alconna(
    Alconna(
        "总结",
        Args["message_count", int],
        Args["content", AllParam, None],
        meta=CommandMeta(
            compact=True,
            description="生成该群最近消息数量的内容总结或指定内容总结",
            usage="总结 [消息数量] [内容]\n内容为可选，支持@用户",
        ),
    ),
    priority=5,
    block=True,
)
summary_set = on_alconna(
    Alconna(
        "总结定时",
        Args[
            "time",
            "re:(0?[0-9]|1[0-9]|2[0-3])",
        ],
        Args["least_message_count", int, config.summary_max_length],
        meta=CommandMeta(
            compact=True,
            description="定时生成消息数量的内容总结",
            usage="总结定时 [时间] [最少消息数量]\n时间：0~23\n最少消息数量：默认为总结最大长度",
        ),
    ),
    rule=validate_group_event,
    priority=5,
    block=True,
    permission=SUPERUSER,
)

summary_remove = on_alconna(
    Alconna(
        "总结定时取消",
        meta=CommandMeta(
            description="取消本群的定时内容总结",
            usage="总结定时取消",
        ),
    ),
    rule=validate_group_event,
    priority=5,
    block=True,
    permission=SUPERUSER,
)

driver = get_driver()


@driver.on_startup
async def subscribe_jobs():
    set_scheduler()


@summary_group.handle()
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    message_count: Match[int],
    content: Match[str],
):
    message_count_get = message_count.result
    if content_get := content.result:
        # 将内容转换为消息段列表
        text_parts = []
        segments = (
            content_get if isinstance(content_get, (list, tuple)) else [content_get]
        )

        # 获取群成员信息将@转换为昵称
        for seg in segments:
            if isinstance(seg, At):
                try:
                    info = await bot.get_group_member_info(
                        group_id=event.group_id, user_id=int(seg.target)
                    )
                    text_parts.append(
                        f"@{info.get('card') or info.get('nickname', seg.target)}"
                    )
                except Exception:
                    # 如果获取群成员信息失败，直接使用QQ号
                    text_parts.append(f"@{seg.target}")
            elif isinstance(seg, str):
                # 只有当字符串不为空且不只包含空白字符时才添加
                stripped = seg.strip()
                if stripped:
                    text_parts.append(stripped)
            elif hasattr(seg, "target"):  # 处理其他可能的@类型消息段
                text_parts.append(f"@{seg.target}")
            elif hasattr(seg, "text"):  # 处理其他可能的文本类型消息段
                stripped = str(seg.text).strip()
                if stripped:
                    text_parts.append(stripped)
            else:
                # 其他类型的消息段，尝试转换为字符串
                try:
                    text = str(seg).strip()
                    if text:
                        text_parts.append(text)
                except Exception:
                    continue
        content_get = "".join(text_parts).strip()

    # 消息数量检查
    if not validate_message_count(message_count_get):
        await summary_group.finish(
            f"总结消息数量应在 {config.summary_min_length} 到 {config.summary_max_length} 之间。",
            at_sender=True,
        )

    # 冷却时间，针对人，而非群
    if cool_time := validate_cool_down(event.user_id):
        await summary_group.finish(f"请等待 {cool_time} 秒后再次使用。", at_sender=True)

    group_id = event.group_id
    messages = await get_group_msg_history(bot, group_id, message_count_get)
    if not messages:
        await summary_group.finish("未能获取到聊天记录。", at_sender=True)

    summary = await messages_summary(messages, content_get)
    await send_summary(bot, group_id, summary)


@summary_set.handle()
async def _(
    event: GroupMessageEvent,
    time: Match[str],
    least_message_count: Match[int],
):
    group_id = event.group_id
    store = Store()
    data = Data(time=int(time.result), least_message_count=least_message_count.result)
    store.set(group_id, data)
    await summary_set.finish(
        f"已设置定时总结，将在{time.result}时当群消息相较昨天同时多于{least_message_count.result}条消息时生成内容总结。",
        at_sender=True,
    )


@summary_remove.handle()
async def _(event: GroupMessageEvent):
    group_id = event.group_id
    store = Store()
    store.remove(group_id)
    await summary_remove.finish("已取消本群定时总结。", at_sender=True)
