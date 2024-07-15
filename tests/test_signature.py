from hypothesis import given, strategies as st
from kanade.signature.base import Parameter, Signature

# 生成 name 的策略

first_characters = st.characters(whitelist_categories=("Lu", "Ll", "Lt", "Lm", "Lo", "Nl"), whitelist_characters="_")
non_first_characters = st.characters(whitelist_categories=("Lu", "Ll", "Lt", "Lm", "Lo", "Nl", "Nd"), whitelist_characters="_")
identifier = st.text(min_size=1, max_size=10, alphabet=non_first_characters).map(
    lambda s: s if s[0].isalpha() or s[0] == "_" else "_" + s
)

# 生成 annotation 和 default 的策略
value_strategy = st.none() | st.just("example")

# 生成 type 的策略
type_strategy = st.sampled_from(["position-only", "keyword-only", "position-variables", "keyword-variables", "positional-or-keyword"])


@given(name=identifier, annotation=value_strategy, default=value_strategy, type_=type_strategy)
def test_parameter_str(name, annotation, default, type_):
    parameter = Parameter(name=name, annotation=annotation, default=default, type=type_)

    if parameter.type == "position-variables":
        assert parameter.__str__().startswith("*")
    elif parameter.type == "keyword-variables":
        assert parameter.__str__().startswith("**")
    else:
        assert not parameter.__str__().startswith(("*", "**"))

    if parameter.annotation is None:
        assert parameter.__str__().count(":") == 0
    else:
        assert parameter.__str__().count(":") == 1

    if parameter.default is None:
        assert parameter.__str__().count("=") == 0
    else:
        assert parameter.__str__().count("=") == 1
    
    assert parameter.__str__().count(",") == 0


@given(func=st.functions())
def test_signature(func):
    print(Signature.from_callable(func))