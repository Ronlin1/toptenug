from __future__ import annotations

import importlib
import json
from typing import Any, TypeVar

from pydantic import BaseModel

from app.domain.enums import ReviewStatus
from app.domain.schemas import CandidateProposal, DiscoveryQuery

T = TypeVar("T", bound=BaseModel)


class GroundingRequiredError(ValueError):
    pass


class GeminiIntelligenceProvider:
    def __init__(
        self,
        *,
        api_key: str | None,
        client: Any | None = None,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self._model = model
        self._types: Any = None
        self._client: Any
        if client is not None:
            self._client = client
            return
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when no client is injected")
        genai = importlib.import_module("google.genai")
        self._types = importlib.import_module("google.genai.types")
        self._client = genai.Client(api_key=api_key)

    def _validate(
        self, payload: list[dict[str, Any]] | list[CandidateProposal]
    ) -> list[CandidateProposal]:
        out: list[CandidateProposal] = []
        for item in payload:
            proposal = (
                item
                if isinstance(item, CandidateProposal)
                else CandidateProposal.model_validate(item)
            )
            if not proposal.source_urls:
                raise GroundingRequiredError(
                    f"Candidate '{proposal.display_name}' has no grounded source URL"
                )
            ambiguous = any(
                token in claim.lower()
                for claim in proposal.uganda_relation_claims
                for token in ("possibly", "maybe", "unclear", "unverified")
            )
            if proposal.confidence < 0.85 or ambiguous:
                proposal = proposal.model_copy(
                    update={"review_status": ReviewStatus.REVIEW_REQUIRED}
                )
            out.append(proposal)
        return out

    def discover(self, query: DiscoveryQuery) -> list[CandidateProposal]:
        if hasattr(self._client, "discover"):
            return self._validate(self._client.discover(query.text))

        response = self._client.models.generate_content(
            model=self._model,
            contents=(
                "Discover grounded candidates. Do not rank, score, or declare winners. "
                f"Query: {query.text}"
            ),
            config=self._types.GenerateContentConfig(
                tools=[self._types.Tool(google_search=self._types.GoogleSearch())],
                response_mime_type="application/json",
                response_schema=list[CandidateProposal],
            ),
        )
        return self._validate(json.loads(response.text or "[]"))

    def extract_evidence(self, url: str, schema: type[T]) -> list[T]:
        if hasattr(self._client, "extract"):
            return [
                item if isinstance(item, schema) else schema.model_validate(item)
                for item in self._client.extract(url, schema.__name__)
            ]

        response = self._client.models.generate_content(
            model=self._model,
            contents=(
                "Extract only claims supported by this URL; do not infer rankings. "
                f"Return objects matching this JSON schema: {schema.model_json_schema()}. "
                f"URL: {url}"
            ),
            config=self._types.GenerateContentConfig(
                tools=[self._types.Tool(url_context=self._types.UrlContext())],
                response_mime_type="application/json",
                response_schema=list[dict[str, Any]],
            ),
        )
        return [schema.model_validate(item) for item in json.loads(response.text or "[]")]
