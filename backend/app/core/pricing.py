# USD per token (input, output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15 / 1_000_000, 0.60 / 1_000_000),
    "gpt-4o": (2.50 / 1_000_000, 10.00 / 1_000_000),
    "gpt-4.1-mini": (0.40 / 1_000_000, 1.60 / 1_000_000),
    "gpt-4.1": (2.00 / 1_000_000, 8.00 / 1_000_000),
    "gpt-5": (5.00 / 1_000_000, 15.00 / 1_000_000),
    "claude-opus-4-20250514": (15.00 / 1_000_000, 75.00 / 1_000_000),
    "claude-haiku-4-5-20251001": (1.00 / 1_000_000, 5.00 / 1_000_000),
    "claude-sonnet-4-5-20250929": (3.00 / 1_000_000, 15.00 / 1_000_000),
    "claude-sonnet-4-6": (3.00 / 1_000_000, 15.00 / 1_000_000),
    "gemini-2.5-flash": (0.15 / 1_000_000, 0.60 / 1_000_000),
    "gemini-2.5-flash-lite": (0.10 / 1_000_000, 0.40 / 1_000_000),
    "gemini-2.0-flash": (0.10 / 1_000_000, 0.40 / 1_000_000),
    "grok-4.3": (3.00 / 1_000_000, 15.00 / 1_000_000),
    "grok-4": (3.00 / 1_000_000, 15.00 / 1_000_000),
    "grok-3-mini": (0.30 / 1_000_000, 0.50 / 1_000_000),
    "qwen3.6-27b-fable5": (0.0, 0.0),
}

DEFAULT_PRICING = (1.00 / 1_000_000, 3.00 / 1_000_000)

# Flat per-image output pricing (xAI Imagine docs, USD per image)
IMAGE_MODEL_PRICING: dict[str, float] = {
    "grok-imagine-image-quality": 0.05,
    "grok-imagine-image-pro": 0.05,
}


def calculate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return (input_tokens * input_rate) + (output_tokens * output_rate)


def calculate_image_cost_usd(model: str, *, image_count: int = 1) -> float:
    unit = IMAGE_MODEL_PRICING.get(model, 0.05)
    return unit * max(1, image_count)