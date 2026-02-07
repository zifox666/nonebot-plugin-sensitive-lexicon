import json
import time

from nonebot import logger, require, on_command, on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, GroupMessageEvent

from .ocr import ocr_text
from .detect import detect_sensitive_words

require("nonebot_plugin_localstore")

from .config import Config, plugin_config

__plugin_meta__ = PluginMetadata(
    name="敏感词审核",
    description="",
    usage="",
    type="application",
    homepage="https://github.com/zifox666/nonebot-plugin-sensitive-lexicon",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={"author": "zifox666"},
)

import nonebot_plugin_localstore as store

enable = on_command("esl", aliases={"开启敏感词审核"}, priority=5)
detect = on_message(priority=999)


class EnableGroupState:
    def __init__(self):
        pass

    @classmethod
    async def get(cls, group_id: int) -> bool:
        file = store.get_data_file(
            plugin_name="nonebot_plugin_sensitive_lexicon",
            filename=f"sensitive_lexicon_{group_id}.json",
        )

        if not file.exists():
            default_data = {
                "enabled": True,
                "admin": None,
                "timestamp": int(time.time()),
            }
            file.write_text(json.dumps(default_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            return True

        data = file.read_text(encoding="utf-8")
        data = json.loads(data)
        return data.get("enabled", False)

    @classmethod
    async def set(cls, group_id: int, enabled: bool, admin: str | int) -> bool:
        file = store.get_data_file(
            plugin_name="nonebot_plugin_sensitive_lexicon",
            filename=f"sensitive_lexicon_{group_id}.json",
        )

        if not file.exists():
            data = {}
        else:
            data = json.loads(file.read_text(encoding="utf-8"))

        data["enabled"] = enabled
        data["admin"] = admin
        data["timestamp"] = int(time.time())
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        return True


class BlackMemberList:
    @classmethod
    async def get(cls, user_id: str | int, group_id: str | int) -> int:
        file = store.get_data_file(
            plugin_name="nonebot_plugin_sensitive_lexicon",
            filename=f"blacklist_{group_id}_{user_id}.json",
        )
        if not file.exists():
            default_data = {
                "blacklisted": [],
                "timestamp": int(time.time()),
            }
            file.write_text(json.dumps(default_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            return 0
        else:
            data = json.loads(file.read_text(encoding="utf-8"))
            return len(data.get("blacklisted", []))

    @classmethod
    async def add(cls, user_id: str | int, group_id: str | int, msg: str) -> bool:
        file = store.get_data_file(
            plugin_name="nonebot_plugin_sensitive_lexicon",
            filename=f"blacklist_{group_id}_{user_id}.json",
        )
        if not file.exists():
            data = {
                "blacklisted": [
                    {
                        "group_id": group_id,
                        "msg": msg[:50],
                        "timestamp": int(time.time()),
                    }
                ],
                "timestamp": int(time.time()),
            }
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            return True
        else:
            data = json.loads(file.read_text(encoding="utf-8"))
            blacklisted = data.get("blacklisted", [])
            blacklisted.append({
                "group_id": group_id,
                "msg": msg[:50],
                "timestamp": int(time.time()),
            })
            data["blacklisted"] = blacklisted
            data["timestamp"] = int(time.time())
            file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            return True


@enable.handle()
async def _(bot: Bot, event: Event):
    if event.sender.role == "member":
        return
    user_id = event.get_user_id()
    group_id = event.group_id

    if await EnableGroupState.get(group_id):
        await EnableGroupState.set(group_id, False, user_id)
        await enable.finish("已关闭敏感词审核")
    else:
        await EnableGroupState.set(group_id, True, user_id)
        await enable.finish("已开启敏感词审核")


async def _extract_text_from_forward(bot: Bot, forward_id: str) -> str:
    """递归提取合并转发消息的文本内容"""
    try:
        result = await bot.call_api("get_forward_msg", data={"id": forward_id})
        messages = result.get("message", [])

        text = ""
        for msg_item in messages:
            if isinstance(msg_item, dict):
                # 处理 node 消息段
                if msg_item.get("type") == "node":
                    content = msg_item.get("data", {}).get("content", "")
                    if isinstance(content, str):
                        text += content
                    else:
                        # content 可能是消息数组
                        for seg in content:
                            if isinstance(seg, dict) and seg.get("type") == "text":
                                text += seg.get("data", {}).get("text", "")
        return text
    except Exception as e:
        logger.error(f"获取合并转发消息失败: {e}")
        return ""


@detect.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not await EnableGroupState.get(event.group_id):
        return
    msg = event.get_message()

    detecting_str = ""
    for seg in msg:
        _type = seg.type
        match _type:
            case "text":
                detecting_str += seg.data.get("text", "")
            case "image":
                ocr_result = await ocr_text(img=seg.data.get("url", ""))
                if ocr_result:
                    detecting_str += ocr_result
            case "forward" | "node":
                # 处理合并转发消息
                forward_id = seg.data.get("id", "")
                if forward_id:
                    forward_text = await _extract_text_from_forward(bot, forward_id)
                    detecting_str += forward_text
            case _:
                pass

    res = await detect_sensitive_words(detecting_str)
    if res:
        try:
            await bot.call_api("delete_msg", data={
                "message_id": event.message_id,
            })
        except Exception as e:
            logger.error(f"删除消息失败: {e}")

        blacklist = BlackMemberList()
        count = await blacklist.get(event.get_user_id(), event.group_id)

        await blacklist.add(event.get_user_id(), event.group_id, msg=str(detecting_str))

        current_count = count + 1

        if current_count <= plugin_config.kick_count:
            base_days = plugin_config.mute_day
            max_days = 30

            ban_days = int(min(max_days, base_days * (2 ** (current_count - 1))))

            duration = int(60 * 60 * 24 * ban_days)

            try:
                await bot.call_api(
                    "set_group_ban",
                    data={
                        "group_id": event.group_id,
                        "user_id": event.get_user_id(),
                        "duration": duration,
                    },
                )
            except Exception as e:
                logger.error(f"禁言用户失败: {e}")
            flag = f"禁言 {ban_days} 天"
        else:
            try:
                await bot.call_api(
                    "set_group_kick",
                    data={
                        "group_id": event.group_id,
                        "user_id": event.get_user_id(),
                        "reject_add_request": plugin_config.reject_add_request,
                    },
                )
            except Exception as e:
                logger.error(f"移出群聊失败: {e}")
            flag = "移出群聊"


        await detect.finish(
            MessageSegment.at(event.get_user_id()) +
            MessageSegment.text("话题违规" + f"\n处罚方式: {flag}")
        )

