from app.services.llm_usage import extract_token_usage


class FakeMessage:
    def __init__(self, usage_metadata=None, response_metadata=None) -> None:
        self.usage_metadata = usage_metadata
        self.response_metadata = response_metadata


def test_extract_token_usage_prefers_usage_metadata() -> None:
    message = FakeMessage(
        usage_metadata={
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        }
    )

    assert extract_token_usage(message) == {
        "input_tokens": 10,
        "output_tokens": 4,
        "total_tokens": 14,
    }


def test_extract_token_usage_falls_back_to_response_metadata() -> None:
    message = FakeMessage(
        usage_metadata=None,
        response_metadata={
            "token_usage": {
                "prompt_token_count": 8,
                "candidates_token_count": 3,
                "total_token_count": 11,
            }
        },
    )

    assert extract_token_usage(message) == {
        "input_tokens": 8,
        "output_tokens": 3,
        "total_tokens": 11,
    }
