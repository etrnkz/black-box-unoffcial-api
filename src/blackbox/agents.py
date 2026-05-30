from typing import Any, Optional

import httpx

from .models import (
    AgentConfig,
    AgentExecution,
    AgentInfo,
    AgentTaskConfig,
    MultiAgentTask,
)


class Agents:
    BASE_URL = "https://api.blackbox.ai"
    CLOUD_URL = "https://cloud.blackbox.ai"

    def __init__(self, client: httpx.Client, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _headers(self, json: bool = True) -> dict[str, str]:
        h: dict[str, str] = {}
        if json:
            h["content-type"] = "application/json"
        if self._api_key:
            h["authorization"] = f"Bearer {self._api_key}"
        return h

    def _parse_agent(self, data: dict[str, Any]) -> AgentInfo:
        return AgentInfo(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            model=data.get("model"),
            status=data.get("status"),
            raw=data,
        )

    # --- Single Agent API (api.blackbox.ai/v1/agents/*) ---

    def create(self, config: AgentConfig) -> AgentInfo:
        body: dict[str, Any] = {"name": config.name}
        if config.description:
            body["description"] = config.description
        if config.model:
            body["model"] = config.model
        if config.system_prompt:
            body["system_prompt"] = config.system_prompt
        if config.tools:
            body["tools"] = config.tools

        resp = self._client.post(
            f"{self.BASE_URL}/v1/agents",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        return self._parse_agent(resp.json())

    def list(self) -> list[AgentInfo]:
        resp = self._client.get(
            f"{self.BASE_URL}/v1/agents",
            headers=self._headers() if self._api_key else {},
        )
        resp.raise_for_status()
        data = resp.json()
        agents = data if isinstance(data, list) else data.get("data", [])
        return [self._parse_agent(a) for a in agents]

    def get(self, agent_id: str) -> AgentInfo:
        resp = self._client.get(
            f"{self.BASE_URL}/v1/agents/{agent_id}",
            headers=self._headers() if self._api_key else {},
        )
        resp.raise_for_status()
        return self._parse_agent(resp.json())

    def delete(self, agent_id: str) -> dict[str, Any]:
        resp = self._client.delete(
            f"{self.BASE_URL}/v1/agents/{agent_id}",
            headers=self._headers() if self._api_key else {},
        )
        resp.raise_for_status()
        return resp.json() if resp.text else {}

    def execute(self, agent_id: str, prompt: str) -> AgentExecution:
        body = {"input": prompt}
        resp = self._client.post(
            f"{self.BASE_URL}/v1/agents/{agent_id}/execute",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return AgentExecution(
            id=data.get("id", ""),
            agent_id=agent_id,
            status=data.get("status", "completed"),
            input=prompt,
            output=data.get("output"),
            error=data.get("error"),
        )

    def run(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> AgentExecution:
        body: dict[str, Any] = {"input": prompt}
        if model:
            body["model"] = model
        if system_prompt:
            body["system_prompt"] = system_prompt

        resp = self._client.post(
            f"{self.BASE_URL}/v1/agents/run",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return AgentExecution(
            id=data.get("id", ""),
            agent_id=data.get("agent_id", ""),
            status=data.get("status", "completed"),
            input=prompt,
            output=data.get("output"),
            error=data.get("error"),
        )

    # --- Multi-Agent Task API (cloud.blackbox.ai/api/tasks) ---

    def create_task(
        self,
        prompt: str,
        agents: list[AgentTaskConfig],
        repo_url: Optional[str] = None,
        selected_branch: Optional[str] = None,
    ) -> MultiAgentTask:
        body: dict[str, Any] = {
            "prompt": prompt,
            "selectedAgents": [
                {"agent": a.agent, "model": a.model} for a in agents
            ],
        }
        if repo_url:
            body["repoUrl"] = repo_url
        if selected_branch:
            body["selectedBranch"] = selected_branch

        resp = self._client.post(
            f"{self.CLOUD_URL}/api/tasks",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        task = data.get("task", data)

        executions = None
        raw_execs = task.get("agentExecutions")
        if raw_execs:
            executions = [
                AgentExecution(
                    id=e.get("executionId", ""),
                    agent_id=e.get("agent", ""),
                    status=e.get("status", "pending"),
                    input=prompt,
                    output=(
                        e.get("result", {}).get("summary")
                        if isinstance(e.get("result"), dict)
                        else None
                    ),
                    error=e.get("error"),
                    commits=e.get("commits"),
                    files_changed=e.get("filesChanged"),
                )
                for e in raw_execs
            ]

        return MultiAgentTask(
            id=task.get("id", ""),
            prompt=prompt,
            repo_url=repo_url,
            selected_branch=selected_branch,
            status=task.get("status", "pending"),
            agent_executions=executions,
            selected_agents=[
                AgentTaskConfig(agent=a["agent"], model=a["model"])
                for a in task.get("selectedAgents", [])
            ],
            task_url=data.get("taskUrl"),
            raw=data,
        )

    def get_task(self, task_id: str) -> MultiAgentTask:
        resp = self._client.get(
            f"{self.CLOUD_URL}/api/tasks/{task_id}",
            headers=self._headers() if self._api_key else {},
        )
        resp.raise_for_status()
        data = resp.json()
        task = data.get("task", data)

        executions = None
        raw_execs = task.get("agentExecutions")
        if raw_execs:
            executions = [
                AgentExecution(
                    id=e.get("executionId", ""),
                    agent_id=e.get("agent", ""),
                    status=e.get("status", "pending"),
                    input=task.get("prompt", ""),
                    output=(
                        e.get("result", {}).get("summary")
                        if isinstance(e.get("result"), dict)
                        else None
                    ),
                    error=e.get("error"),
                    commits=e.get("commits"),
                    files_changed=e.get("filesChanged"),
                )
                for e in raw_execs
            ]

        return MultiAgentTask(
            id=task.get("id", ""),
            prompt=task.get("prompt", ""),
            repo_url=task.get("repoUrl"),
            selected_branch=task.get("selectedBranch"),
            status=task.get("status", "pending"),
            agent_executions=executions,
            selected_agents=[
                AgentTaskConfig(agent=a["agent"], model=a["model"])
                for a in task.get("selectedAgents", [])
            ],
            task_url=data.get("taskUrl"),
            raw=data,
        )
