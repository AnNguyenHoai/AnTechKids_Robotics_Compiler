# H26-L Pytest Environment Boundary

H26-L is a standalone regression gate. Its assertions use plain Python `assert` semantics and do not require pytest at runtime.

The runner must not invoke `python -m pytest` because a target/developer Python installation may contain a broken or shadowing `pytest.py` module. Such an environment failure is outside the H26-L capability contract and must not prevent the capability gate from executing.
