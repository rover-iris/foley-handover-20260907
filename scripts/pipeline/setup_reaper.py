"""一键配置 Reaper 启用 reapy_boost（含 Python 3.13 兼容补丁）。

用法：
    python setup_reaper.py [resource_path]

背景：reapy_boost 0.10.x 的 CaseInsensitiveDict 与 Python 3.13 的 configparser
新增的 unnamed-section 检查不兼容（非字符串 key 触发 .lower() 报错）。
本脚本在调用官方 configure_reaper 前打一个运行时补丁，非字符串 key 直接放行。
配置内容（由 reapy_boost 官方逻辑完成）：
    1. Reaper 启用 Python ReaScript（指向托管 Python 3.13.12）
    2. Web Interface 端口 2309
    3. activate_reapy_server 注册进 Actions
    4. 写入 external state

执行后：重启 Reaper 即可从外部连接 reapy_boost。
"""
from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore")

from reapy_boost.config.config import CaseInsensitiveDict  # noqa: E402

_orig_contains = CaseInsensitiveDict.__contains__


def _safe_contains(self, key):
    if not isinstance(key, str):
        return False
    return _orig_contains(self, key)


CaseInsensitiveDict.__contains__ = _safe_contains

from reapy_boost.config import configure_reaper  # noqa: E402

RESOURCE_PATH = (
    sys.argv[1]
    if len(sys.argv) > 1
    else r"C:\Users\Administrator\AppData\Roaming\REAPER"
)

if __name__ == "__main__":
    configure_reaper(resource_path=RESOURCE_PATH)
    print("OK: Reaper 已配置完成（Python ReaScript + Web Interface + 启动脚本）")
    print("下一步：重启 Reaper，之后外部进程即可用 reapy_boost.connect() 连接。")
