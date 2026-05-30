import argparse
import sys

from .client import BlackBoxClient
from .models import AgentConfig, AgentTaskConfig, ChatMessage, ReasoningConfig, Tool, ToolChoice


def cmd_auth(args):
    client = BlackBoxClient(session_token=getattr(args, "session", None))
    try:
        if args.action == "csrf":
            token = client.auth.get_csrf()
            print(f"CSRF Token: {token}")
        elif args.action == "login":
            result = client.auth.login_with_token(args.token, args.email)
            print(f"Login result: {result}")
        elif args.action == "session":
            info = client.get_session()
            print(f"User: {info.email or 'Not logged in'}")
            print(f"Expires: {info.expires}")
        elif args.action == "verify":
            result = client.verify_email(args.email, args.code)
            print(f"Verify result: {result}")
        elif args.action == "send-verification":
            result = client.send_verification(args.email)
            print(f"Verification sent: {result}")
    finally:
        client.close()


def cmd_credits(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        info = client.get_credits()
        print(f"Total: {info.total}")
        print(f"Used:  {info.used}")
        print(f"Remaining: {info.remaining}")


def cmd_chat(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        messages = [ChatMessage(role="user", content=args.message)]
        kwargs = {}
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.max_tokens is not None:
            kwargs["max_tokens"] = args.max_tokens
        if args.top_p is not None:
            kwargs["top_p"] = args.top_p

        result = client.chat_complete(messages, model=args.model, **kwargs)

        if result.usage:
            print(f"\n[{result.usage.prompt_tokens} prompt / {result.usage.completion_tokens} completion / {result.usage.total_tokens} total tokens]")
            if result.usage.cost is not None:
                print(f"[Cost: ${result.usage.cost:.6f}]")
        print(f"\n{result.content}")


def cmd_search(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        result = client.search(args.query, system_prompt=args.system_prompt)

        print(result.content)

        if result.choices:
            msg = result.choices[0].message
            if msg and msg.annotations:
                print("\n--- Sources ---")
                for ann in msg.annotations:
                    if ann.url_citation:
                        title = ann.url_citation.title or "Untitled"
                        url = ann.url_citation.url
                        print(f"  {title}: {url}")


def cmd_code(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        result = client.generate_code(args.prompt, args.language)
        print(f"\n{result.code}")


def cmd_image(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        result = client.generate_image(
            args.prompt,
            model=args.model,
            size=args.size,
        )
        for img in result.data:
            if img.url:
                print(f"URL: {img.url}")
            if img.revised_prompt:
                print(f"Revised prompt: {img.revised_prompt}")


def cmd_video(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        result = client.generate_video(args.prompt, model=args.model)
        if result.url:
            print(f"URL: {result.url}")
        else:
            print("No video URL in response")


# --- Web-based commands (app.blackbox.ai/api/chat) ---

def cmd_webchat(args):
    with BlackBoxClient(session_token=getattr(args, "session", None)) as client:
        result = client.web_chat(
            args.message,
            agent=getattr(args, "agent", "VscodeAgent"),
            model=getattr(args, "model", None),
            code=args.code,
            search=args.search,
            deep_search=args.deep_search,
            reasoning=args.reasoning,
            max_tokens=args.max_tokens or 1024,
        )
        print(result.content)
        if result.sources:
            print("\n--- Sources ---")
            for s in result.sources:
                print(f"  {s.get('title', 'Untitled')}: {s.get('url', '')}")


def cmd_websearch(args):
    with BlackBoxClient(session_token=getattr(args, "session", None)) as client:
        result = client.web_search(args.query, deep=args.deep)
        print(result.content)
        if result.sources:
            print("\n--- Sources ---")
            for s in result.sources:
                print(f"  {s.get('title', 'Untitled')}: {s.get('url', '')}")


def cmd_webcode(args):
    with BlackBoxClient(session_token=getattr(args, "session", None)) as client:
        result = client.web_generate_code(args.prompt, language=args.language)
        print(result.content)


def cmd_webimage(args):
    with BlackBoxClient(session_token=getattr(args, "session", None)) as client:
        result = client.web_generate_image(args.prompt, model=args.model)
        print(result.content)


def cmd_webvideo(args):
    with BlackBoxClient(session_token=getattr(args, "session", None)) as client:
        result = client.web_generate_video(args.prompt, model=args.model)
        print(result.content)


def cmd_models(args):
    with BlackBoxClient(api_key=getattr(args, "api_key", None)) as client:
        models = client.get_models()
        for m in models:
            parts = [f"  {m.id}"]
            if m.provider:
                parts.append(f"({m.provider})")
            if m.pricing:
                parts.append(f"${m.pricing.input_cost_per_1k:.2f}i/${m.pricing.output_cost_per_1k:.2f}o")
            print(" ".join(parts))


def cmd_agent(args):
    client = BlackBoxClient(api_key=getattr(args, "api_key", None))
    try:
        if args.action == "create":
            config = AgentConfig(
                name=args.name or "my-agent",
                description=args.description,
                model=args.model,
                system_prompt=args.system_prompt,
            )
            agent = client.create_agent(config)
            print(f"Created agent: {agent.id} ({agent.name})")
        elif args.action == "list":
            agents = client.list_agents()
            if not agents:
                print("No agents found.")
            for a in agents:
                print(f"  {a.id}  {a.name}  [{a.status or '?'}]")
        elif args.action == "get":
            agent = client.get_agent(args.id)
            print(f"ID:     {agent.id}")
            print(f"Name:   {agent.name}")
            print(f"Status: {agent.status}")
        elif args.action == "delete":
            client.delete_agent(args.id)
            print(f"Deleted agent {args.id}")
        elif args.action == "run":
            result = client.run_agent(
                args.prompt,
                model=args.model,
                system_prompt=args.system_prompt,
            )
            print(f"Execution: {result.id}")
            if result.output:
                print(f"\n{result.output}")
            if result.error:
                print(f"Error: {result.error}")
        elif args.action == "task":
            if not args.agents:
                print("Error: --agents required for multi-agent task (format: agent:model,agent:model)")
                return
            agents = []
            for a in args.agents.split(","):
                parts = a.strip().split(":", 1)
                agent_name = parts[0].strip()
                model_name = parts[1].strip() if len(parts) > 1 else ""
                agents.append(AgentTaskConfig(agent=agent_name, model=model_name))
            result = client.create_multi_agent_task(
                prompt=args.prompt,
                agents=agents,
                repo_url=args.repo_url,
                selected_branch=args.branch,
            )
            print(f"Task ID: {result.id}")
            if result.task_url:
                print(f"Task URL: {result.task_url}")
            print(f"Status: {result.status}")
        elif args.action == "task-status":
            task = client.get_multi_agent_task(args.id)
            print(f"Task: {task.id}")
            print(f"Status: {task.status}")
            if task.agent_executions:
                for ex in task.agent_executions:
                    print(f"  Agent: {ex.agent_id} -> {ex.status}")
    finally:
        client.close()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="blackbox",
        description="Unofficial blackbox.ai API client",
    )
    parser.add_argument("--api-key", help="Blackbox API key (sk-...)")
    parser.add_argument("--session", help="Session token for cookie auth")

    sub = parser.add_subparsers(dest="command")

    # --- auth ---
    auth_p = sub.add_parser("auth", help="Authentication commands")
    auth_p.add_argument("action", choices=["csrf", "login", "session", "verify", "send-verification"])
    auth_p.add_argument("--token", help="Login token")
    auth_p.add_argument("--email", help="Email address")
    auth_p.add_argument("--code", help="Verification code")

    # --- credits ---
    sub.add_parser("credits", help="Get credit balance")

    # --- models ---
    sub.add_parser("models", help="List available models")

    # --- agent ---
    agent_p = sub.add_parser("agent", help="Manage and run agents")
    agent_p.add_argument("action", choices=["create", "list", "get", "delete", "run", "task", "task-status"])
    agent_p.add_argument("--name", help="Agent name (for create)")
    agent_p.add_argument("--description", help="Agent description")
    agent_p.add_argument("--model", help="Model to use")
    agent_p.add_argument("--system-prompt", help="System prompt")
    agent_p.add_argument("--id", help="Agent/task ID (for get/delete/task-status)")
    agent_p.add_argument("--prompt", help="Prompt (for run/task)")
    agent_p.add_argument("--agents", help="Comma-separated agent:model pairs (for task)")
    agent_p.add_argument("--repo-url", help="GitHub repo URL (for task)")
    agent_p.add_argument("--branch", help="GitHub branch (for task)")

    # --- chat ---
    chat_p = sub.add_parser("chat", help="Chat completion")
    chat_p.add_argument("message", help="User message")
    chat_p.add_argument("--model", default="blackbox", help="Model to use")
    chat_p.add_argument("--temperature", type=float, help="Sampling temperature (0-2)")
    chat_p.add_argument("--max-tokens", type=int, help="Maximum response tokens")
    chat_p.add_argument("--top-p", type=float, help="Top-p sampling")

    # --- search ---
    search_p = sub.add_parser("search", help="Web search via blackbox-search model")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--system-prompt", help="System prompt for search context")

    # --- code ---
    code_p = sub.add_parser("code", help="Generate code")
    code_p.add_argument("prompt", help="Code prompt")
    code_p.add_argument("--language", help="Target language")

    # --- image ---
    image_p = sub.add_parser("image", help="Generate image")
    image_p.add_argument("prompt", help="Image prompt")
    image_p.add_argument("--model", default=None, help="Image model (e.g. flux-pro, ideogram-v3, imagen-3)")
    image_p.add_argument("--size", help="Image size (e.g. 1024x1024)")

    # --- video ---
    video_p = sub.add_parser("video", help="Generate video")
    video_p.add_argument("prompt", help="Video prompt")
    video_p.add_argument("--model", default="veo-2", help="Video model (e.g. veo-2, veo-3, ray-2)")

    # --- web chat ---
    wc_p = sub.add_parser("webchat", help="Chat via web endpoint")
    wc_p.add_argument("message", help="User message")
    wc_p.add_argument("--agent", default="VscodeAgent", help="Agent to use")
    wc_p.add_argument("--model", help="Model override")
    wc_p.add_argument("--max-tokens", type=int, default=1024, help="Max tokens")
    wc_p.add_argument("--code", action="store_true", help="Code generation mode")
    wc_p.add_argument("--search", action="store_true", help="Web search mode")
    wc_p.add_argument("--deep-search", action="store_true", help="Deep search mode")
    wc_p.add_argument("--reasoning", action="store_true", help="Reasoning mode")

    # --- web search ---
    ws_p = sub.add_parser("websearch", help="Web search via web endpoint")
    ws_p.add_argument("query", help="Search query")
    ws_p.add_argument("--deep", action="store_true", help="Deep search")

    # --- web code ---
    wk_p = sub.add_parser("webcode", help="Generate code via web endpoint")
    wk_p.add_argument("prompt", help="Code prompt")
    wk_p.add_argument("--language", help="Target language")

    # --- web image ---
    wi_p = sub.add_parser("webimage", help="Generate image via web endpoint")
    wi_p.add_argument("prompt", help="Image prompt")
    wi_p.add_argument("--model", help="Image model")

    # --- web video ---
    wv_p = sub.add_parser("webvideo", help="Generate video via web endpoint")
    wv_p.add_argument("prompt", help="Video prompt")
    wv_p.add_argument("--model", help="Video model")

    args = parser.parse_args(argv)

    handlers = {
        "auth": cmd_auth,
        "credits": cmd_credits,
        "models": cmd_models,
        "agent": cmd_agent,
        "chat": cmd_chat,
        "search": cmd_search,
        "code": cmd_code,
        "image": cmd_image,
        "video": cmd_video,
        "webchat": cmd_webchat,
        "websearch": cmd_websearch,
        "webcode": cmd_webcode,
        "webimage": cmd_webimage,
        "webvideo": cmd_webvideo,
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
