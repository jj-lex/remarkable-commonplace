"""AI providers for the two jobs that use a model: topics (text) and handwriting (image).

Every provider implements the same two methods, so prompts and clean-up rules stay in ai.py and
switching models never changes behaviour around them.

    complete(system, prompt, max_tokens) -> str
    read_image(png_path, prompt)        -> str

Configure in ~/Library/Application Support/Commonplace/config.json, separately per job:

    "ai": {
      "topics":      {"provider": "apple"},
      "handwriting": {"provider": "anthropic"}
    }

Providers: apple (default, on device), anthropic, openai, xai, openrouter, ollama,
openai-compatible (give "base_url"), none. Options: "model", "base_url", "api_key_env",
"api_key_keychain". API keys never go in the config file.
"""
import base64
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from . import apple

# Presets for OpenAI-format APIs. Model names change often, so none is assumed: set "model".
OPENAI_PRESETS = {
    "openai": {"base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_API_KEY"},
    "xai": {"base_url": "https://api.x.ai/v1", "api_key_env": "XAI_API_KEY"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY"},
    "ollama": {"base_url": "http://localhost:11434/v1", "api_key_env": ""},
    "openai-compatible": {"base_url": "", "api_key_env": "OPENAI_API_KEY"},
}

ANTHROPIC_DEFAULT_MODEL = "claude-opus-5-5"


class ProviderError(Exception):
    pass


def api_key(opts: dict, provider: str, default_env: str = "") -> str:
    """Environment variable first, then macOS Keychain (service 'commonplace-<provider>' by default).
    Background jobs don't see your shell's environment, so Keychain is the reliable place."""
    env = opts.get("api_key_env", default_env)
    if env and os.environ.get(env):
        return os.environ[env]
    service = opts.get("api_key_keychain", f"commonplace-{provider}")
    r = subprocess.run(["security", "find-generic-password", "-s", service, "-w"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


class NoProvider:
    name = "none"

    def complete(self, system, prompt, max_tokens=256):
        return ""

    def read_image(self, png, prompt):
        return ""


class AppleProvider:
    """On-device: Apple's language model for text, Apple Vision for handwriting. Free and private."""
    name = "apple"

    def complete(self, system, prompt, max_tokens=256):
        return apple.generate(system, prompt)

    def read_image(self, png, prompt):
        return apple.read_handwriting(png)


class AnthropicProvider:
    """Claude via the official Anthropic SDK (pip install anthropic)."""
    name = "anthropic"

    def __init__(self, opts: dict):
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError("the anthropic package isn't installed: .venv/bin/pip install anthropic") from e
        self.anthropic = anthropic
        key = api_key(opts, "anthropic", "ANTHROPIC_API_KEY")
        # With no key found, the SDK falls back to its own resolution (env vars, `ant auth login` profile).
        self.client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
        self.model = opts.get("model", ANTHROPIC_DEFAULT_MODEL)
        self.effort = opts.get("effort", "low")  # small, well-defined jobs: low effort is plenty

    def _send(self, system: str, content: list, max_tokens: int) -> str:
        a = self.anthropic
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
                output_config={"effort": self.effort},
                # On a policy decline, let the API re-run the request on a suitable model.
                betas=["server-side-fallback-2026-07-01"],
                extra_body={"fallbacks": "default"},
            )
        except a.AuthenticationError as e:
            raise ProviderError("Anthropic API key missing or invalid") from e
        except a.NotFoundError as e:
            raise ProviderError(f"unknown Anthropic model {self.model!r}") from e
        except a.RateLimitError as e:
            raise ProviderError("Anthropic rate limit; will retry next sync") from e
        except a.APIStatusError as e:
            raise ProviderError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except a.APIConnectionError as e:
            raise ProviderError("can't reach the Anthropic API") from e
        except TypeError as e:  # the SDK found no credentials at all
            raise ProviderError("no Anthropic API key found. Add one with: "
                                "security add-generic-password -a \"$USER\" -s commonplace-anthropic -w") from e
        if response.stop_reason == "refusal":
            return ""
        return "".join(b.text for b in response.content if b.type == "text").strip()

    def complete(self, system, prompt, max_tokens=256):
        return self._send(system, [{"type": "text", "text": prompt}], max_tokens)

    def read_image(self, png, prompt):
        data = base64.standard_b64encode(Path(png).read_bytes()).decode("utf-8")
        return self._send("", [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
            {"type": "text", "text": prompt},
        ], 1024)


class OpenAICompatibleProvider:
    """Any API that speaks the OpenAI chat-completions format: OpenAI, xAI (Grok), OpenRouter,
    Groq, Together, Ollama, LM Studio, vLLM... Plain HTTP, no extra packages."""

    def __init__(self, provider: str, opts: dict):
        preset = OPENAI_PRESETS[provider]
        self.name = provider
        self.base_url = (opts.get("base_url") or preset["base_url"]).rstrip("/")
        self.model = opts.get("model", "")
        if not self.base_url:
            raise ProviderError(f"{provider}: set \"base_url\"")
        if not self.model:
            raise ProviderError(f"{provider}: set \"model\" (e.g. the model name from your provider's docs)")
        self.key = api_key(opts, provider, preset["api_key_env"]) if preset["api_key_env"] or opts.get("api_key_env") or opts.get("api_key_keychain") else ""

    def _send(self, messages: list, max_tokens: int) -> str:
        body = json.dumps({"model": self.model, "messages": messages, "max_tokens": max_tokens}).encode()
        req = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, method="POST",
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": f"Bearer {self.key}"} if self.key else {})})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:200]
            raise ProviderError(f"{self.name} API error {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise ProviderError(f"can't reach {self.base_url}: {e.reason}") from e
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"{self.name}: unexpected response") from e

    def complete(self, system, prompt, max_tokens=256):
        return self._send([{"role": "system", "content": system}, {"role": "user", "content": prompt}], max_tokens)

    def read_image(self, png, prompt):
        data = base64.standard_b64encode(Path(png).read_bytes()).decode("utf-8")
        return self._send([{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
        ]}], 1024)


def make(opts: dict | None):
    opts = opts or {"provider": "apple"}
    provider = opts.get("provider", "apple")
    if provider == "apple":
        return AppleProvider()
    if provider == "none":
        return NoProvider()
    if provider == "anthropic":
        return AnthropicProvider(opts)
    if provider in OPENAI_PRESETS:
        return OpenAICompatibleProvider(provider, opts)
    raise ProviderError(f"unknown provider {provider!r}")
