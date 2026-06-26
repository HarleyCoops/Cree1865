"""Gradio app for the Cree1865 remote Tinker sampler."""

from __future__ import annotations

import os
import json

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

import gradio as gr

try:
    from .tinker_remote import (
        DEFAULT_MODEL_PATH,
        DEFAULT_SYSTEM_PROMPT,
        EXAMPLE_PROMPTS,
        generate_for_ui,
    )
except ImportError:
    from tinker_remote import (  # type: ignore
        DEFAULT_MODEL_PATH,
        DEFAULT_SYSTEM_PROMPT,
        EXAMPLE_PROMPTS,
        generate_for_ui,
    )


def infer(
    prompt: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    seed: int,
    num_samples: int,
    enable_thinking: bool,
):
    return generate_for_ui(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=int(max_tokens),
        temperature=float(temperature),
        top_p=float(top_p),
        seed=int(seed),
        num_samples=int(num_samples),
        enable_thinking=bool(enable_thinking),
    )


def endpoint_status() -> dict[str, object]:
    return {
        "endpoint": DEFAULT_MODEL_PATH,
        "tinker_key_configured": bool(os.getenv("TINKER_API_KEY")),
    }


with gr.Blocks(title="Cree1865 Tinker Endpoint") as demo:
    gr.Markdown("# Cree1865 Tinker Endpoint")
    with gr.Accordion("Run context", open=False):
        gr.Markdown(
            "This Space calls the final 800-step Tinker sampler remotely. "
            "It is an experimental endpoint for inspection, not a validated fluent Cree model."
        )
        gr.Textbox(
            value=json.dumps(endpoint_status(), indent=2),
            label="Endpoint status",
            lines=4,
            interactive=False,
        )

    with gr.Row():
        with gr.Column(scale=3):
            prompt = gr.Textbox(
                lines=6,
                label="Prompt",
                placeholder="Ask for a Cree dictionary lookup or translation.",
            )
            system_prompt = gr.Textbox(
                value=DEFAULT_SYSTEM_PROMPT,
                lines=3,
                label="System prompt",
            )
            run = gr.Button("Run", variant="primary")
        with gr.Column(scale=2):
            max_tokens = gr.Slider(16, 256, value=96, step=8, label="Max tokens")
            temperature = gr.Slider(0.0, 1.2, value=0.3, step=0.05, label="Temperature")
            top_p = gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-p")
            seed = gr.Number(value=42, precision=0, label="Seed")
            num_samples = gr.Slider(1, 4, value=1, step=1, label="Samples")
            enable_thinking = gr.Checkbox(value=False, label="Enable thinking")

    output = gr.Textbox(lines=10, label="Model output")
    metadata = gr.JSON(label="Run metadata")

    gr.Examples(
        examples=[[example] for example in EXAMPLE_PROMPTS],
        inputs=[prompt],
    )

    run.click(
        fn=infer,
        inputs=[
            prompt,
            system_prompt,
            max_tokens,
            temperature,
            top_p,
            seed,
            num_samples,
            enable_thinking,
        ],
        outputs=[output, metadata],
        api_name="infer",
    )
    prompt.submit(
        fn=infer,
        inputs=[
            prompt,
            system_prompt,
            max_tokens,
            temperature,
            top_p,
            seed,
            num_samples,
            enable_thinking,
        ],
        outputs=[output, metadata],
        api_name=False,
    )


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=2).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
    )
