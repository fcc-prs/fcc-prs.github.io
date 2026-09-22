import anthropic
import os


def get_client():
    """Return an Anthropic client configured for the Portkey/authkey.ai proxy."""
    return anthropic.Anthropic(
        api_key="placeholder",  # Portkey ignores x-api-key; auth is via x-portkey-api-key
        base_url=os.environ["ANTHROPIC_BASE_URL"],
        default_headers={"x-portkey-api-key": os.environ["ANTHROPIC_API_KEY"]},
    )
