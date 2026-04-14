"""Base classes for framework discovery."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class RouteInfo(BaseModel):
    """Information about a discovered route or endpoint."""

    path: str = Field(description="URL path (e.g., '/login', '/api/v1/users')")
    method: str = Field(default="GET", description="HTTP method")
    route_type: Literal["page", "api", "layout", "middleware", "dynamic"] = Field(
        default="page", description="Type of route"
    )
    has_auth: bool = Field(default=False, description="Whether this route requires authentication")
    has_form: bool = Field(default=False, description="Whether this route contains a form")
    source_file: str = Field(default="", description="Path to the source file defining this route")
    dynamic_params: list[str] = Field(default_factory=list, description="Dynamic route parameters")


class FrameworkInfo(BaseModel):
    """Information about a detected framework."""

    name: str = Field(description="Framework name (e.g., 'nextjs', 'fastapi')")
    version: str | None = Field(default=None, description="Framework version if detected")
    category: Literal["frontend", "backend", "fullstack"] = Field(description="Framework category")
    routes: list[RouteInfo] = Field(default_factory=list, description="Discovered routes")
    config_files: list[str] = Field(default_factory=list, description="Framework config files found")
    root_dir: str = Field(default=".", description="Root directory for this framework relative to project root")


class FrameworkDiscoverer(abc.ABC):
    """Abstract base class for framework-specific route discovery."""

    @abc.abstractmethod
    def detect(self, project_dir: Path) -> FrameworkInfo | None:
        """Detect if this framework is used in the project.

        Args:
            project_dir: Root directory of the project.

        Returns:
            FrameworkInfo if detected, None otherwise.
        """

    @abc.abstractmethod
    def discover_routes(self, project_dir: Path) -> list[RouteInfo]:
        """Discover all routes/endpoints for this framework.

        Args:
            project_dir: Root directory of the project.

        Returns:
            List of discovered routes.
        """
