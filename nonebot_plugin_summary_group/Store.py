import json
from typing import TypedDict

from nonebot import require

require("nonebot_plugin_localstore")
from nonebot_plugin_localstore import get_plugin_data_file  # noqa: E402


class Data(TypedDict):
    time: int
    least_message_count: int


class Store:
    _instance = None  # 单例模式
    data: dict[str, Data]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False  # 添加一个标志来跟踪初始化状态
        return cls._instance

    def __init__(self):
        if self.__initialized:  # 避免多次初始化
            return
        self.__initialized = True

        self.store = get_plugin_data_file("summary_group.json")
        if not self.store.exists() or self.store.stat().st_size == 0:
            self.data = {}
            return

        with open(self.store, "r") as f:
            self.data: dict[str, Data] = json.load(f)

    def save(self):
        with open(self.store, "w") as f:
            json.dump(self.data, f)

    def get(self, group_id: int) -> Data | None:
        return self.data.get(str(group_id))

    def set(self, group_id: int, data: Data):
        self.data[str(group_id)] = data
        self.save()

    def remove(self, group_id: int):
        self.data.pop(str(group_id), None)
        self.save()
