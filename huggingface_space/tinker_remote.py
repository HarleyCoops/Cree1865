"""Remote Tinker inference helpers for the Cree1865 Hugging Face Space."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import time
from typing import Any, Callable

DEFAULT_MODEL_PATH = (
    "tinker://c71aadd1-8e48-51b0-b890-149a2889b4fa:train:0/"
    "sampler_weights/final"
)

DEFAULT_SYSTEM_PROMPT = (
    "Answer Cree dictionary lookup and translation prompts concisely. "
    "Use Cree forms only when you are confident, preserve orthography exactly, "
    "and return only the requested answer."
)

EXAMPLE_PROMPTS = [
    "Translate the Cree word maskihkiy into English.",
    "Give the Cree dictionary headword for 'medicine'. Return only the Cree form.",
    "Translate 'I speak Cree' into Cree. Return only the answer.",
    "What does the Cree suffix -win usually mark in dictionary entries?",
]


@dataclass(frozen=True)
class TinkerGeneration:
    """Structured result from one Tinker sampler request."""

    responses: list[str]
    stop_reasons: list[str]
    prompt_tokens: int
    model_path: str
    elapsed_seconds: float

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


def _import_tinker() -> Any:
    import tinker

    return tinker


@lru_cache(maxsize=4)
def get_cached_sampling_client(model_path: str) -> Any:
    """Create and cache one remote sampler client per Tinker model path."""

    tinker = _import_tinker()
    service_client = tinker.ServiceClient()
    return service_client.create_sampling_client(model_path=model_path)


def build_chat_prompt(
    tokenizer: Any,
    system_prompt: str,
    user_prompt: str,
    enable_thinking: bool,
) -> str:
    """Format a chat prompt with the sampler tokenizer template."""

    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
        except TypeError:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
    return f"{messages[0]['content']}\n\nUser: {messages[1]['content']}\nAssistant:"


def sample_tinker_response(
    *,
    prompt: str,
    system_prompt: str,
    model_path: str = DEFAULT_MODEL_PATH,
    max_tokens: int = 96,
    temperature: float = 0.3,
    top_p: float = 0.9,
    top_k: int = -1,
    seed: int = 42,
    num_samples: int = 1,
    enable_thinking: bool = False,
    sampling_client: Any | None = None,
    tinker_module: Any | None = None,
) -> TinkerGeneration:
    """Run one remote generation request against a Tinker sampler checkpoint."""

    if tinker_module is None:
        tinker_module = _import_tinker()
    if sampling_client is None:
        sampling_client = get_cached_sampling_client(model_path)

    start = time.perf_counter()
    tokenizer = sampling_client.get_tokenizer()
    formatted_prompt = build_chat_prompt(
        tokenizer,
        system_prompt=system_prompt,
        user_prompt=prompt,
        enable_thinking=enable_thinking,
    )
    prompt_tokens = tokenizer.encode(formatted_prompt)
    model_input = tinker_module.ModelInput.from_ints(prompt_tokens)
    sampling_params = tinker_module.SamplingParams(
        max_tokens=int(max_tokens),
        temperature=float(temperature),
        top_p=float(top_p),
        top_k=int(top_k),
        seed=int(seed),
    )
    response = sampling_client.sample(
        prompt=model_input,
        num_samples=int(num_samples),
        sampling_params=sampling_params,
    ).result()
    decoded = [
        tokenizer.decode(sequence.tokens, skip_special_tokens=True).strip()
        for sequence in response.sequences
    ]
    stop_reasons = [str(sequence.stop_reason) for sequence in response.sequences]
    return TinkerGeneration(
        responses=decoded,
        stop_reasons=stop_reasons,
        prompt_tokens=len(prompt_tokens),
        model_path=model_path,
        elapsed_seconds=round(time.perf_counter() - start, 3),
    )


def format_output(responses: list[str]) -> str:
    """Render one or more model samples for the Gradio textbox."""

    cleaned = [response.strip() or "[empty response]" for response in responses]
    if len(cleaned) == 1:
        return cleaned[0]
    return "\n\n---\n\n".join(
        f"Sample {index}\n{response}" for index, response in enumerate(cleaned, start=1)
    )


def generate_for_ui(
    *,
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    seed: int,
    num_samples: int,
    enable_thinking: bool,
    model_path: str = DEFAULT_MODEL_PATH,
    sampling_client_factory: Callable[[str], Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Gradio callback wrapper with validation and readable error reporting."""

    if not prompt or not prompt.strip():
        return (
            "Enter a prompt before running inference.",
            {"ok": False, "error_type": "validation"},
        )

    try:
        sampling_client = (
            sampling_client_factory(model_path)
            if sampling_client_factory is not None
            else get_cached_sampling_client(model_path)
        )
        result = sample_tinker_response(
            prompt=prompt,
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            model_path=model_path,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=-1,
            seed=seed,
            num_samples=num_samples,
            enable_thinking=enable_thinking,
            sampling_client=sampling_client,
        )
        metadata = result.to_metadata()
        metadata.update(
            {
                "ok": True,
                "num_samples": int(num_samples),
                "temperature": float(temperature),
                "top_p": float(top_p),
                "seed": int(seed),
                "enable_thinking": bool(enable_thinking),
            }
        )
        return format_output(result.responses), metadata
    except Exception as exc:  # noqa: BLE001 - UI should surface backend failures.
        return (
            f"Inference error ({type(exc).__name__}): {exc}",
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "message": str(exc),
                "model_path": model_path,
            },
        )
