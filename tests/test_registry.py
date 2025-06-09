import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from registry import Registry, Tool


def base_func():
    return "ok"


def handler(func, **kwargs):
    return func()


def test_register_and_call():
    registry = Registry()
    tool = Tool(func=base_func, handler=handler)
    registry.register_tool(tool)
    assert "base_func" in registry.manager
    result = registry.call("base_func")
    assert result == "ok"
    assert registry["base_func"].func is base_func