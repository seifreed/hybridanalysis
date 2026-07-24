"""Async resource classes.

Each class reuses the endpoint methods from the shared sync resource class and,
via the MRO, resolves the ``_get``/``_post``/... helpers to the coroutine versions
in :class:`AsyncBaseResource`. So the endpoint definitions live in exactly one
place (``hybridanalysis.resources``) and every method here is awaitable.
"""

from __future__ import annotations

from hybridanalysis.resources.abuse_reports import AbuseReportsResource
from hybridanalysis.resources.feed import FeedResource
from hybridanalysis.resources.file_collection import FileCollectionResource
from hybridanalysis.resources.key import KeyResource
from hybridanalysis.resources.overview import OverviewResource
from hybridanalysis.resources.quick_scan import QuickScanResource
from hybridanalysis.resources.report import ReportResource
from hybridanalysis.resources.search import SearchResource
from hybridanalysis.resources.submit import SubmitResource
from hybridanalysis.resources.system import SystemResource

from .base import AsyncBaseResource


class AsyncFeedResource(FeedResource, AsyncBaseResource):
    pass


class AsyncKeyResource(KeyResource, AsyncBaseResource):
    pass


class AsyncOverviewResource(OverviewResource, AsyncBaseResource):
    pass


class AsyncQuickScanResource(QuickScanResource, AsyncBaseResource):
    pass


class AsyncSubmitResource(SubmitResource, AsyncBaseResource):
    pass


class AsyncReportResource(ReportResource, AsyncBaseResource):
    pass


class AsyncSearchResource(SearchResource, AsyncBaseResource):
    pass


class AsyncFileCollectionResource(FileCollectionResource, AsyncBaseResource):
    pass


class AsyncAbuseReportsResource(AbuseReportsResource, AsyncBaseResource):
    pass


class AsyncSystemResource(SystemResource, AsyncBaseResource):
    pass


__all__ = [
    "AsyncAbuseReportsResource",
    "AsyncFeedResource",
    "AsyncFileCollectionResource",
    "AsyncKeyResource",
    "AsyncOverviewResource",
    "AsyncQuickScanResource",
    "AsyncReportResource",
    "AsyncSearchResource",
    "AsyncSubmitResource",
    "AsyncSystemResource",
]
