import pytest
from blackbox.cli import main


class TestCLIParsing:
    def test_no_args(self):
        with pytest.raises(SystemExit):
            main([])

    def test_help(self):
        with pytest.raises(SystemExit):
            main(["--help"])

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

    def test_file_help(self):
        with pytest.raises(SystemExit):
            main(["file", "--help"])

    def test_reason_help(self):
        with pytest.raises(SystemExit):
            main(["reason", "--help"])

    def test_login_help(self):
        with pytest.raises(SystemExit):
            main(["login", "--help"])

    def test_chat_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["chat", "hello"])
        assert exc.value.code in (0, 1, 2)

    def test_search_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["search", "test query"])
        assert exc.value.code in (0, 1, 2)

    def test_code_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["code", "fib", "--language", "python"])
        assert exc.value.code in (0, 1, 2)

    def test_image_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["image", "a cat"])
        assert exc.value.code in (0, 1, 2)

    def test_video_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["video", "drone"])
        assert exc.value.code in (0, 1, 2)

    def test_file_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["file", "doc.pdf", "Summarize"])
        assert exc.value.code in (0, 1, 2)

    def test_reason_with_args(self):
        with pytest.raises(SystemExit) as exc:
            main(["reason", "solve x", "--max-tokens", "500"])
        assert exc.value.code in (0, 1, 2)

    def test_cookie_flag(self):
        with pytest.raises(SystemExit) as exc:
            main(["--cookie", "session=abc", "chat", "hi"])
        assert exc.value.code in (0, 1, 2)

    def test_validated_flag(self):
        with pytest.raises(SystemExit) as exc:
            main(["--validated", "abc-123", "chat", "hi"])
        assert exc.value.code in (0, 1, 2)

    def test_model_flag(self):
        with pytest.raises(SystemExit) as exc:
            main(["--model", "claude", "chat", "hi"])
        assert exc.value.code in (0, 1, 2)
