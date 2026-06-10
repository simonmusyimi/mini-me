from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
from urllib import error, request


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class MissingLLMProvider(LLMProvider):
    def __init__(self, provider_name: str, reason: str) -> None:
        self.provider_name = provider_name
        self.reason = reason

    def generate(self, prompt: str) -> str:
        return f"""Mini-Me cannot generate an LLM plan yet.

Reason: {self.reason}

To enable /plan:
1. Copy .env.example to .env
2. Set OPENAI_API_KEY=your_api_key_here
3. Keep MINIME_LLM_PROVIDER=openai
4. Optional: set MINIME_LLM_MODEL to the model you want

Non-LLM commands still work:
/patterns, /add-task, /show-tasks, /done, /review, /exit
"""


class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Mini-Me, a direct personal feedback loop for Simon. "
                        "Be practical, specific, and focused on execution."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        body = json.dumps(payload).encode("utf-8")
        api_request = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(api_request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return f"LLM request failed with HTTP {exc.code}. Check your API key, model, and quota.\n{detail}"
        except error.URLError as exc:
            return f"LLM request failed: {exc.reason}. Check your network and provider settings."
        except TimeoutError:
            return "LLM request timed out. Try again, or choose a faster model."

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            return f"LLM returned an unexpected response:\n{json.dumps(data, indent=2)}"


def get_llm_provider(project_root: Path | str | None = None) -> LLMProvider:
    if project_root is not None:
        load_env_file(Path(project_root) / ".env")

    provider_name = os.getenv("MINIME_LLM_PROVIDER", "openai").strip().lower()
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return MissingLLMProvider("openai", "OPENAI_API_KEY is missing.")

        model = os.getenv("MINIME_LLM_MODEL", "gpt-4o-mini").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)

    return MissingLLMProvider(
        provider_name,
        f"Provider '{provider_name}' is configured but not implemented in V1.",
    )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
