from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class EntityIdentity:
    aliases: set[str] = field(default_factory=set)
    profiles: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolutionResult:
    entity_id: UUID | None
    review_required: bool
    reason: str


class EntityResolutionService:
    def resolve(self, *, candidate: EntityIdentity, existing: list[tuple[UUID, EntityIdentity]]) -> ResolutionResult:
        deterministic_matches: set[UUID] = set()
        for entity_id, identity in existing:
            for provider, external_id in candidate.profiles.items():
                if external_id and identity.profiles.get(provider) == external_id:
                    deterministic_matches.add(entity_id)
        if len(deterministic_matches) == 1:
            return ResolutionResult(next(iter(deterministic_matches)), False, "exact_external_profile")
        if len(deterministic_matches) > 1:
            return ResolutionResult(None, True, "conflicting_external_profile")

        normalized_aliases = {alias.strip().casefold() for alias in candidate.aliases if alias.strip()}
        alias_matches = {
            entity_id
            for entity_id, identity in existing
            if normalized_aliases.intersection({alias.strip().casefold() for alias in identity.aliases if alias.strip()})
        }
        if len(alias_matches) == 1:
            return ResolutionResult(None, True, "alias_only_match_requires_review")
        if len(alias_matches) > 1:
            return ResolutionResult(None, True, "ambiguous_alias_match")
        return ResolutionResult(None, False, "new_entity")
