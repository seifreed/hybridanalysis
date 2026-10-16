"""Experimental API Labs endpoints."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


def _provided(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


class LabsResource(BaseResource):
    def recent_matches(
        self, *, items_count: int | None = None, search_after: str | None = None
    ) -> Any:
        return self._get(
            "/api/labs/hunting/matches/recent",
            params=_provided(items_count=items_count, search_after=search_after),
        )

    def overview(self, sha256: str) -> Any:
        return self._get(f"/api/labs/sample/{self._seg(sha256)}/overview")

    def search_query(
        self,
        query: str,
        *,
        page: int | None = None,
        size: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Any:
        return self._post_json(
            "/api/labs/search/query/run",
            json=_provided(query=query, page=page, size=size, date_from=date_from, date_to=date_to),
        )

    def search_results(self, query_id: str) -> Any:
        return self._get(f"/api/labs/search/query/{self._seg(query_id)}/results")

    def yara_rules(
        self,
        *,
        search: str | None = None,
        threat_category: list[str] | None = None,
        status: str | None = None,
    ) -> Any:
        return self._get(
            "/api/labs/hunting/yara-rules",
            params=_provided(search=search, threat_category=threat_category, status=status),
        )

    def create_yara_rule(
        self,
        identifier: str,
        threat_categories: list[str],
        rule: str,
        *,
        active: bool | None = None,
        daily_notifications_limit: int | None = None,
    ) -> Any:
        return self._post_json(
            "/api/labs/hunting/yara-rules",
            json=_provided(
                identifier=identifier,
                threat_categories=threat_categories,
                rule=rule,
                active=active,
                daily_notifications_limit=daily_notifications_limit,
            ),
        )

    def get_yara_rule(self, rule_id: str) -> Any:
        return self._get(f"/api/labs/hunting/yara-rules/{self._seg(rule_id)}")

    def update_yara_rule(
        self,
        rule_id: str,
        *,
        identifier: str | None = None,
        threat_categories: list[str] | None = None,
        active: bool | None = None,
        daily_notifications_limit: int | None = None,
        rule: str | None = None,
        reset_counter: bool | None = None,
    ) -> Any:
        return self._post_json(
            f"/api/labs/hunting/yara-rules/{self._seg(rule_id)}",
            json=_provided(
                identifier=identifier,
                threat_categories=threat_categories,
                active=active,
                daily_notifications_limit=daily_notifications_limit,
                rule=rule,
                reset_counter=reset_counter,
            ),
        )

    def delete_yara_rule(self, rule_id: str) -> Any:
        return self._delete(f"/api/labs/hunting/yara-rules/{self._seg(rule_id)}")
