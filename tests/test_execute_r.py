from services.r_runner import ExecuteR, RRunnerProtocol


def test_r_runner_protocol_instance():
    executor = ExecuteR()
    assert isinstance(executor, RRunnerProtocol)


def test_process_args_substitution():
    executor = ExecuteR()
    template = ("rscript", "--file", 0, "--title", 1)
    result = executor.process_args(template, "data.csv", "my_title")
    assert result == ["rscript", "--file", "data.csv", "--title", "my_title"]


def test_process_args_truncated():
    executor = ExecuteR()
    template = ("rscript", "--file", 0, "--title", 1, "--extra", 2)
    result = executor.process_args(template, "data.csv")
    assert result == ["rscript", "--file", "data.csv"]
