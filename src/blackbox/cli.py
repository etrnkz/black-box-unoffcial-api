import argparse
import sys

from .login import LoginError, login
from .webchat import WebChat


def cmd_login(args):
    try:
        import getpass
        password = args.password or getpass.getpass("Password: ")
        result = login(email=args.email, password=password)
        print("Login successful!")
        print(f"Session token: {result['session_token'][:60]}...")
        print(f"User email: {result['user_email'] or 'N/A'}")
        print(f"User ID: {result['user_id'] or 'N/A'}")
        print()
        print("Cookie header (pass with --cookie):")
        print(result["cookie_header"])
        result["session"].close()
    except LoginError as e:
        print(f"Login failed: {e}", file=sys.stderr)
        sys.exit(1)


def _web(args):
    kwargs = {}
    if getattr(args, "cookie", None):
        kwargs["cookie_header"] = args.cookie
    if getattr(args, "validated", None):
        kwargs["validated"] = args.validated
    return WebChat(**kwargs)


def cmd_chat(args):
    with _web(args) as wc:
        result = wc.chat(
            args.message,
            model=getattr(args, "model", None),
            max_tokens=args.max_tokens or 1024,
        )
        print(result.content)
        if result.sources:
            print("\n--- Sources ---")
            for s in result.sources:
                print(f"  {s.get('title', 'Untitled')}: {s.get('url', '')}")


def cmd_search(args):
    with _web(args) as wc:
        result = wc.search(args.query, deep=args.deep)
        print(result.content)
        if result.sources:
            print("\n--- Sources ---")
            for s in result.sources:
                print(f"  {s.get('title', 'Untitled')}: {s.get('url', '')}")


def cmd_code(args):
    with _web(args) as wc:
        result = wc.generate_code(args.prompt, language=getattr(args, "language", None))
        print(result.content)


def cmd_image(args):
    with _web(args) as wc:
        result = wc.generate_image(args.prompt, model=getattr(args, "model", None))
        print(result.content)


def cmd_video(args):
    with _web(args) as wc:
        result = wc.generate_video(args.prompt, model=getattr(args, "model", None))
        print(result.content)


def cmd_filechat(args):
    with _web(args) as wc:
        result = wc.chat_with_file(args.file, args.prompt, model=getattr(args, "model", None))
        print(result.content)


def cmd_reason(args):
    with _web(args) as wc:
        result = wc.chat(args.question, reasoning=True, max_tokens=args.max_tokens or 1024)
        print(result.content)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="blackbox",
        description="Blackbox.ai reverse — no API key needed",
    )
    parser.add_argument("--cookie", help="Raw Cookie header from browser DevTools")
    parser.add_argument("--validated", help="Validated UUID (from browser network tab)")
    parser.add_argument("--model", help="Model override")

    sub = parser.add_subparsers(dest="command")

    # --- login ---
    login_p = sub.add_parser("login", help="Login with email/password, get cookies")
    login_p.add_argument("--email", required=True)
    login_p.add_argument("--password", help="Prompt if omitted")

    # --- chat ---
    chat_p = sub.add_parser("chat", help="Chat with AI")
    chat_p.add_argument("message")
    chat_p.add_argument("--max-tokens", type=int, default=1024)

    # --- search ---
    search_p = sub.add_parser("search", help="Web search")
    search_p.add_argument("query")
    search_p.add_argument("--deep", action="store_true", help="Deep search")

    # --- code ---
    code_p = sub.add_parser("code", help="Generate code")
    code_p.add_argument("prompt")
    code_p.add_argument("--language")

    # --- image ---
    image_p = sub.add_parser("image", help="Generate image")
    image_p.add_argument("prompt")

    # --- video ---
    video_p = sub.add_parser("video", help="Generate video")
    video_p.add_argument("prompt")

    # --- file ---
    file_p = sub.add_parser("file", help="Chat with a file")
    file_p.add_argument("file")
    file_p.add_argument("prompt")

    # --- reason ---
    reason_p = sub.add_parser("reason", help="Reasoning mode")
    reason_p.add_argument("question")
    reason_p.add_argument("--max-tokens", type=int, default=1024)

    args = parser.parse_args(argv)

    handlers = {
        "login": cmd_login,
        "chat": cmd_chat,
        "search": cmd_search,
        "code": cmd_code,
        "image": cmd_image,
        "video": cmd_video,
        "file": cmd_filechat,
        "reason": cmd_reason,
    }

    fn = handlers.get(args.command)
    if fn:
        try:
            fn(args)
        except SystemExit:
            raise
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
