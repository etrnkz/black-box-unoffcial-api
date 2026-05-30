import pytest
from blackbox.cli import main


def _run(args: list[str]):
    try:
        main(args)
    except SystemExit:
        pass


class TestCLIParsing:
    def test_no_args(self):
        with pytest.raises(SystemExit):
            main([])

    def test_help(self):
        with pytest.raises(SystemExit):
            main(["--help"])

    def test_auth_csrf(self):
        with pytest.raises(SystemExit) as exc:
            main(["auth", "csrf"])
        # exits with 0 because it connects and fails
        assert exc.value.code in (0, 1)

    def test_chat_help(self):
        with pytest.raises(SystemExit):
            main(["chat", "--help"])

    def test_search_help(self):
        with pytest.raises(SystemExit):
            main(["search", "--help"])

    def test_video_help(self):
        with pytest.raises(SystemExit):
            main(["video", "--help"])

    def test_image_help(self):
        with pytest.raises(SystemExit):
            main(["image", "--help"])

    def test_code_help(self):
        with pytest.raises(SystemExit):
            main(["code", "--help"])

    def test_models_help(self):
        with pytest.raises(SystemExit):
            main(["models", "--help"])

    def test_credits_help(self):
        with pytest.raises(SystemExit):
            main(["credits", "--help"])

    def test_agent_help(self):
        with pytest.raises(SystemExit):
            main(["agent", "--help"])

    def test_chat_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "chat", "hello", "--model", "gpt-4"])
        assert exc.value.code in (0, 1)

    def test_search_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "search", "test query"])
        assert exc.value.code in (0, 1)

    def test_image_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "image", "a cat", "--model", "flux-pro"])
        assert exc.value.code in (0, 1)

    def test_video_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "video", "drone", "--model", "veo-2"])
        assert exc.value.code in (0, 1)

    def test_code_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "code", "fib", "--language", "python"])
        assert exc.value.code in (0, 1)

    def test_agent_list(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "agent", "list"])
        assert exc.value.code in (0, 1)

    def test_agent_create(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "agent", "create", "--name", "test-agent"])
        assert exc.value.code in (0, 1)

    def test_agent_run(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "agent", "run", "--prompt", "say hi"])
        assert exc.value.code in (0, 1)

    def test_agent_task(self):
        with pytest.raises(SystemExit) as exc:
            main([
                "--api-key", "sk-test",
                "agent", "task",
                "--prompt", "Add README",
                "--agents", "claude:model1,blackbox:model2",
            ])
        assert exc.value.code in (0, 1)

    def test_chat_with_temperature(self):
        with pytest.raises(SystemExit) as exc:
            main(["--api-key", "sk-test", "chat", "hello", "--temperature", "0.5", "--max-tokens", "100"])
        assert exc.value.code in (0, 1)
