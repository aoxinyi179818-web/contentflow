"""Minimal DeepSeek API connectivity check for project Step 20."""

import os

from dotenv import load_dotenv
from openai import OpenAI


class DeepSeekConfigurationError(RuntimeError):
    """Raised when the local DeepSeek configuration is incomplete."""


def request_hello() -> str:
    """Send one fixed, non-sensitive prompt and return the response text."""
    load_dotenv(override=False)
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

    if not api_key:
        raise DeepSeekConfigurationError("DEEPSEEK_API_KEY is missing from the local environment.")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "请只回复：ContentFlow API connection is ready.",
            }
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("DeepSeek returned an empty response.")
    return content


def main() -> None:
    print(request_hello())


if __name__ == "__main__":
    main()
