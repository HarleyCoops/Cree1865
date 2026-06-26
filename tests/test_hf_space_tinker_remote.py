from __future__ import annotations

import importlib


class FakeFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class FakeSequence:
    def __init__(self, tokens, stop_reason="length"):
        self.tokens = tokens
        self.stop_reason = stop_reason


class FakeResponse:
    def __init__(self, sequences):
        self.sequences = sequences


class FakeTokenizer:
    def __init__(self):
        self.messages = None
        self.enable_thinking = None
        self.encoded_text = None

    def apply_chat_template(
        self,
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    ):
        self.messages = messages
        self.enable_thinking = enable_thinking
        assert tokenize is False
        assert add_generation_prompt is True
        return f"SYSTEM:{messages[0]['content']}\nUSER:{messages[1]['content']}\nASSISTANT:"

    def encode(self, text):
        self.encoded_text = text
        return [101, 102, 103]

    def decode(self, tokens, skip_special_tokens=True):
        assert skip_special_tokens is True
        return "maskihkiy" if tokens == [201, 202] else "nisto"


class FakeSamplingClient:
    def __init__(self):
        self.tokenizer = FakeTokenizer()
        self.sample_calls = []

    def get_tokenizer(self):
        return self.tokenizer

    def sample(self, prompt, num_samples, sampling_params):
        self.sample_calls.append(
            {
                "prompt": prompt,
                "num_samples": num_samples,
                "sampling_params": sampling_params,
            }
        )
        return FakeFuture(
            FakeResponse(
                [
                    FakeSequence([201, 202], "stop"),
                    FakeSequence([301], "length"),
                ]
            )
        )


class FakeTinker:
    class ModelInput:
        @staticmethod
        def from_ints(tokens):
            return {"tokens": tokens}

    class SamplingParams:
        def __init__(self, max_tokens, temperature, top_p, top_k, seed):
            self.max_tokens = max_tokens
            self.temperature = temperature
            self.top_p = top_p
            self.top_k = top_k
            self.seed = seed


def test_sample_tinker_response_formats_chat_and_uses_sampler_params():
    remote = importlib.import_module("huggingface_space.tinker_remote")
    sampling_client = FakeSamplingClient()

    result = remote.sample_tinker_response(
        prompt="Translate the Cree word maskihkiy.",
        system_prompt="Answer from the Cree dictionary.",
        model_path="tinker://example/sampler_weights/final",
        max_tokens=32,
        temperature=0.2,
        top_p=0.8,
        top_k=-1,
        seed=7,
        num_samples=2,
        enable_thinking=False,
        sampling_client=sampling_client,
        tinker_module=FakeTinker,
    )

    assert result.responses == ["maskihkiy", "nisto"]
    assert result.stop_reasons == ["stop", "length"]
    assert result.prompt_tokens == 3
    assert result.model_path == "tinker://example/sampler_weights/final"
    assert sampling_client.tokenizer.messages == [
        {"role": "system", "content": "Answer from the Cree dictionary."},
        {"role": "user", "content": "Translate the Cree word maskihkiy."},
    ]
    assert sampling_client.tokenizer.enable_thinking is False
    sample_call = sampling_client.sample_calls[0]
    assert sample_call["prompt"] == {"tokens": [101, 102, 103]}
    assert sample_call["num_samples"] == 2
    assert sample_call["sampling_params"].max_tokens == 32
    assert sample_call["sampling_params"].temperature == 0.2
    assert sample_call["sampling_params"].top_p == 0.8
    assert sample_call["sampling_params"].top_k == -1
    assert sample_call["sampling_params"].seed == 7


def test_generate_for_ui_rejects_empty_prompts_without_backend_call():
    remote = importlib.import_module("huggingface_space.tinker_remote")

    output, metadata = remote.generate_for_ui(
        prompt="   ",
        system_prompt="Answer from the Cree dictionary.",
        max_tokens=32,
        temperature=0.2,
        top_p=0.8,
        seed=7,
        num_samples=1,
        enable_thinking=False,
        sampling_client_factory=lambda _model_path: (_ for _ in ()).throw(
            AssertionError("backend should not be called")
        ),
    )

    assert "Enter a prompt" in output
    assert metadata["ok"] is False
    assert metadata["error_type"] == "validation"


def test_generate_for_ui_reports_backend_errors():
    remote = importlib.import_module("huggingface_space.tinker_remote")

    def broken_factory(_model_path):
        raise RuntimeError("Tinker key missing")

    output, metadata = remote.generate_for_ui(
        prompt="Translate the Cree word maskihkiy.",
        system_prompt="Answer from the Cree dictionary.",
        max_tokens=32,
        temperature=0.2,
        top_p=0.8,
        seed=7,
        num_samples=1,
        enable_thinking=False,
        sampling_client_factory=broken_factory,
    )

    assert "Inference error" in output
    assert "Tinker key missing" in output
    assert metadata["ok"] is False
    assert metadata["error_type"] == "RuntimeError"
