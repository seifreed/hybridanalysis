"""API resource groups, one class per API tag."""

from __future__ import annotations

from .abuse_reports import AbuseReportsResource
from .feed import FeedResource
from .file_collection import FileCollectionResource
from .key import KeyResource
from .overview import OverviewResource
from .quick_scan import QuickScanResource
from .report import ReportResource
from .search import SearchResource
from .submit import SubmitResource
from .system import SystemResource

__all__ = [
    "AbuseReportsResource",
    "FeedResource",
    "FileCollectionResource",
    "KeyResource",
    "OverviewResource",
    "QuickScanResource",
    "ReportResource",
    "SearchResource",
    "SubmitResource",
    "SystemResource",
]
