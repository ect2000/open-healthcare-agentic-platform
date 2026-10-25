"""Ollama model adapter implementation."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator, Sequence

from healthcare_agents.models.base import (
    BaseModelAdapter,
    ModelInferenceError,
    ModelNotFoundError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from healthcare_agents.models.schemas import (
    CompletionUsage,
    Message,
    ModelResponse,
    ModelStreamChunk,
)


class OllamaAdapter(BaseModelAdapter):
    """Adapter for local inference with Ollama using native HTTP endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "gemma4:e2b",
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def _make_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def check_service_health(self) -> bool:
        """Check if the Ollama service responds to requests."""
        url = self._make_url("/api/tags")
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return bool(resp.status == 200)
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Fetch list of model names currently installed on Ollama."""
        url = self._make_url("/api/tags")
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                names: list[str] = []
                for m in models:
                    name = m.get("name")
                    if name:
                        names.append(name)
                        # also append variant without :latest tag if present
                        if name.endswith(":latest"):
                            names.append(name[:-7])
                return names
        except urllib.error.URLError as err:
            raise ModelUnavailableError(
                f"Cannot connect to Ollama service at {self.base_url}: {err.reason}"
            ) from err
        except Exception as err:
            raise ModelUnavailableError(
                f"Error retrieving models from Ollama at {self.base_url}: {err}"
            ) from err

    def is_available(self) -> bool:
        """Check if Ollama is running and the target model is installed."""
        try:
            available_models = self.list_models()
            return (
                self.model_name in available_models
                or f"{self.model_name}:latest" in available_models
            )
        except ModelUnavailableError:
            return False

    def _build_payload(
        self,
        prompt: str,
        system_instruction: str | None = None,
        messages: Sequence[Message] | None = None,
        temperature: float | None = None,
        stream: bool = False,
    ) -> dict[str, object]:
        chat_messages: list[dict[str, str]] = []
        if system_instruction:
            chat_messages.append({"role": "system", "content": system_instruction})

        if messages:
            for m in messages:
                chat_messages.append({"role": m.role, "content": m.content})
        else:
            chat_messages.append({"role": "user", "content": prompt})

        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": chat_messages,
            "stream": stream,
        }

        options: dict[str, object] = {}
        if temperature is not None:
            options["temperature"] = temperature

        if options:
            payload["options"] = options

        return payload

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        messages: Sequence[Message] | None = None,
        temperature: float | None = None,
    ) -> ModelResponse:
        """Synchronously execute a chat completion request with Ollama."""
        url = self._make_url("/api/chat")
        payload = self._build_payload(
            prompt=prompt,
            system_instruction=system_instruction,
            messages=messages,
            temperature=temperature,
            stream=False,
        )

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        import time

        from healthcare_agents.observability import get_metrics, trace_span

        m = get_metrics()
        m.inference_requests_total.add(1, {"model": self.model_name})
        t0 = time.perf_counter()

        with trace_span(
            "model.inference",
            attributes={
                "model.name": self.model_name,
                "model.provider": "ollama",
                "model.timeout_seconds": self.timeout_seconds,
            },
        ) as span:
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    resp_text = resp.read().decode("utf-8")
                    raw = json.loads(resp_text)
                duration_s = time.perf_counter() - t0
                m.inference_duration_seconds.record(
                    duration_s, {"model": self.model_name, "status": "success"}
                )
            except urllib.error.HTTPError as err:
                duration_s = time.perf_counter() - t0
                m.inference_duration_seconds.record(
                    duration_s, {"model": self.model_name, "status": "error"}
                )
                m.inference_errors_total.add(
                    1, {"model": self.model_name, "error_type": "HTTPError"}
                )
                err_body = err.read().decode("utf-8", errors="replace")
                if err.code == 404:
                    raise ModelNotFoundError(
                        f"Model '{self.model_name}' not found on Ollama at {self.base_url}. "
                        f"Run `ollama pull {self.model_name}` first."
                    ) from err
                raise ModelInferenceError(
                    f"Ollama returned HTTP error {err.code}: {err_body}"
                ) from err
            except urllib.error.URLError as err:
                duration_s = time.perf_counter() - t0
                m.inference_duration_seconds.record(
                    duration_s, {"model": self.model_name, "status": "error"}
                )
                m.inference_errors_total.add(
                    1, {"model": self.model_name, "error_type": "URLError"}
                )
                if isinstance(err.reason, socket.timeout | TimeoutError):
                    raise ModelTimeoutError(
                        f"Request to Ollama timed out after {self.timeout_seconds} seconds."
                    ) from err
                raise ModelUnavailableError(
                    f"Cannot connect to Ollama service at {self.base_url}: {err.reason}"
                ) from err
            except TimeoutError as err:
                duration_s = time.perf_counter() - t0
                m.inference_duration_seconds.record(
                    duration_s, {"model": self.model_name, "status": "error"}
                )
                m.inference_errors_total.add(
                    1, {"model": self.model_name, "error_type": "TimeoutError"}
                )
                raise ModelTimeoutError(
                    f"Request to Ollama timed out after {self.timeout_seconds} seconds."
                ) from err
            except json.JSONDecodeError as err:
                duration_s = time.perf_counter() - t0
                m.inference_duration_seconds.record(
                    duration_s, {"model": self.model_name, "status": "error"}
                )
                m.inference_errors_total.add(
                    1, {"model": self.model_name, "error_type": "JSONDecodeError"}
                )
                raise ModelInferenceError(f"Malformed JSON response from Ollama: {err}") from err

            message_data = raw.get("message", {})
            content = message_data.get("content", "")

            total_dur_ns = raw.get("total_duration")
            eval_dur_ns = raw.get("eval_duration")
            prompt_tokens = raw.get("prompt_eval_count")
            completion_tokens = raw.get("eval_count")

            # Record actual token metrics reported by the response without fabricating
            if prompt_tokens is not None:
                try:
                    m.inference_prompt_tokens_total.add(prompt_tokens, {"model": self.model_name})
                    span.set_attribute("gen_ai.usage.input_tokens", prompt_tokens)
                except Exception:
                    pass
            if completion_tokens is not None:
                try:
                    m.inference_completion_tokens_total.add(
                        completion_tokens, {"model": self.model_name}
                    )
                    span.set_attribute("gen_ai.usage.output_tokens", completion_tokens)
                except Exception:
                    pass

            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=(
                    (prompt_tokens or 0) + (completion_tokens or 0)
                    if prompt_tokens is not None or completion_tokens is not None
                    else None
                ),
                total_duration_ms=total_dur_ns / 1_000_000.0 if total_dur_ns is not None else None,
                eval_duration_ms=eval_dur_ns / 1_000_000.0 if eval_dur_ns is not None else None,
            )

            return ModelResponse(
                content=content,
                model=raw.get("model", self.model_name),
                usage=usage,
                raw=raw,
            )

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        messages: Sequence[Message] | None = None,
        temperature: float | None = None,
    ) -> Iterator[ModelStreamChunk]:
        """Stream chat completion chunks from Ollama."""
        url = self._make_url("/api/chat")
        payload = self._build_payload(
            prompt=prompt,
            system_instruction=system_instruction,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout_seconds)
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            if err.code == 404:
                raise ModelNotFoundError(
                    f"Model '{self.model_name}' not found on Ollama at {self.base_url}. "
                    f"Run `ollama pull {self.model_name}` first."
                ) from err
            raise ModelInferenceError(f"Ollama returned HTTP error {err.code}: {err_body}") from err
        except urllib.error.URLError as err:
            if isinstance(err.reason, socket.timeout | TimeoutError):
                raise ModelTimeoutError(
                    f"Request to Ollama timed out after {self.timeout_seconds} seconds."
                ) from err
            raise ModelUnavailableError(
                f"Cannot connect to Ollama service at {self.base_url}: {err.reason}"
            ) from err
        except TimeoutError as err:
            raise ModelTimeoutError(
                f"Request to Ollama timed out after {self.timeout_seconds} seconds."
            ) from err

        with resp:
            for line in resp:
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    chunk_json = json.loads(line_str)
                except json.JSONDecodeError as err:
                    raise ModelInferenceError(
                        f"Malformed streaming chunk from Ollama: {err}"
                    ) from err

                msg = chunk_json.get("message", {})
                content_delta = msg.get("content", "")
                done = bool(chunk_json.get("done", False))

                usage: CompletionUsage | None = None
                if done:
                    total_dur_ns = chunk_json.get("total_duration")
                    eval_dur_ns = chunk_json.get("eval_duration")
                    usage = CompletionUsage(
                        prompt_tokens=chunk_json.get("prompt_eval_count"),
                        completion_tokens=chunk_json.get("eval_count"),
                        total_tokens=(
                            (chunk_json.get("prompt_eval_count") or 0)
                            + (chunk_json.get("eval_count") or 0)
                            if chunk_json.get("prompt_eval_count") is not None
                            or chunk_json.get("eval_count") is not None
                            else None
                        ),
                        total_duration_ms=(
                            total_dur_ns / 1_000_000.0 if total_dur_ns is not None else None
                        ),
                        eval_duration_ms=(
                            eval_dur_ns / 1_000_000.0 if eval_dur_ns is not None else None
                        ),
                    )

                yield ModelStreamChunk(
                    content=content_delta,
                    model=chunk_json.get("model", self.model_name),
                    done=done,
                    usage=usage,
                )
