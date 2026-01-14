import pytest
from scivianna_example import demo

@pytest.mark.default
def test_demo():
    _, slaves = demo.make_demo(return_slaves = True)

    for slave in slaves:
        slave.terminate()


if __name__ == "__main__":
    test_demo()