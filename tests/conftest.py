"""Shared fixtures: a real local API server and a transport wired to it."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from hybridanalysis.client import HybridAnalysisClient
from hybridanalysis.config import Config
from hybridanalysis.transport import Transport

from .api_server import VALID_KEY, LocalAPIServer


@pytest.fixture
def server() -> Iterator[LocalAPIServer]:
    with LocalAPIServer() as running:
        yield running


@pytest.fixture
def config(server: LocalAPIServer) -> Config:
    return Config(api_key=VALID_KEY, base_url=server.base_url)


@pytest.fixture
def transport(config: Config) -> Iterator[Transport]:
    with Transport(config) as tr:
        yield tr


@pytest.fixture
def client(config: Config) -> Iterator[HybridAnalysisClient]:
    with HybridAnalysisClient(config) as instance:
        yield instance
