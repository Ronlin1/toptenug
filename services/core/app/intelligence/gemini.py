from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

from app.intelligence.base import CandidateProposal, CandidateProposalBatch, DiscoveryQuery

T = TypeVar("T", bound=BaseModel)


class GeminiProvider:
    """Google/Gemini research support. This provider never emits official scores or ranks."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-3.8-flash",
        client: Any | None = None,
    ) -> None:
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        self.client = client
        self.model = model

    def discover(self, query: DiscoveryQuery) -> list[CandidateProposal]:
        prompt = (
            "Discover candidate entities relevant to TopTenUG. Return only candidates that have "
            "public source URLs supporting their identity and Uganda relationship. Search result order "
            "must not be interpreted as rank. Research request: " + query.text
        )
        interaction = self.client.interactions.create(
            model=self.model,
            input=prompt,
            tools=[{"type": "google_search"}, {"type": "url_context"}],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": CandidateProposalBatch.model_json_schema(),
            },
        )
        batch = CandidateProposalBatch.model_validate_json(interaction.output_text)
        return batch.candidates

    def extract_evidence(self, url: str, schema: type[T]) -> list[T]:
        adapter = TypeAdapter(list[schema])
        interaction = self.client.interactions.create(
            model=self.model,
            input=f"Extract only claims supported by this public URL: {url}",
            tools=[{"type": "url_context"}],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": adapter.json_schema(),
            },
        )
        return adapter.validate_json(interaction.output_text)
