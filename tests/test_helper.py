import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from helper import function_to_schema


def sample_func(name: str, age: int):
    """Return a greeting"""
    return f"Hello {name}, you are {age} years old"


def test_function_to_schema():
    schema = function_to_schema(sample_func)
    assert schema["function"]["name"] == "sample_func"
    props = schema["function"]["parameters"]["properties"]
    assert props["name"]["type"] == "string"
    assert props["age"]["type"] == "integer"
    required = set(schema["function"]["parameters"]["required"])
    assert required == {"name", "age"}