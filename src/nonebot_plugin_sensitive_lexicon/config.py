from pathlib import Path

from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    kick_count: int = 5
    mute_day: int = 1
    reject_add_request: bool = False


# 配置加载
plugin_config: Config = get_plugin_config(Config)
global_config = get_driver().config

# 目录
ROOT_PATH = Path(__name__).parent.absolute()

DATA_PATH = ROOT_PATH / "data"

PLUGIN_PATH = Path(__file__).resolve().parent
