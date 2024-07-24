import pytest
from kanade.signature_prototype.base import Parameter, Signature, BindResult, BindOptions

@pytest.fixture
def signature():
    params = [
        Parameter(name="x"),
        Parameter(name="y", annotation="int"),
        Parameter(name="z", default="None"),
    ]
    return Signature(parameters=params)

def test_parameter_str():
    param = Parameter(name="x", annotation="int", default="0")
    assert str(param) == "x: int = 0"

def test_signature_str(signature):
    assert str(signature) == "(x, y: int, z = None)"

def test_bind_partial(signature):
    bind_result = signature.bind_partial(1, z=3)
    assert isinstance(bind_result, BindResult)
    assert bind_result.bounded_args == {"x": 1, "z": 3}

def test_apply_defaults(signature):
    bind_result = signature.bind_partial(1)
    bind_result = bind_result.apply_defaults()
    assert isinstance(bind_result, BindResult)
    assert bind_result.bounded_args == {"x": 1, "z": "None"}

def test_complete(signature):
    bind_result = signature.bind_partial(1, y=2)
    with pytest.raises(BaseException):
        bind_result.complete()
    bind_result = bind_result.apply_defaults()
    bind_result = bind_result.complete()
    assert isinstance(bind_result, BindResult)
    assert bind_result.bounded_args == {"x": 1, "y": 2, "z": "None"}
    assert bind_result.completed

def test_options(signature):
    bind_result = signature.bind_partial(1, y=2)
    bind_result = bind_result.options(BindOptions(reassignable=True))
    assert isinstance(bind_result, BindResult)
    assert bind_result._options.reassignable

def test_check_valid(signature):
    assert signature.check_valid() is None
