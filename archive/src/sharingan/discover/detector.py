"""Auto-detect frameworks from project files."""

from __future__ import annotations

from pathlib import Path

from sharingan.discover.base import FrameworkInfo
from sharingan.discover.django import DjangoDiscoverer
from sharingan.discover.express import ExpressDiscoverer
from sharingan.discover.fastapi import FastAPIDiscoverer
from sharingan.discover.nextjs import NextJSDiscoverer
from sharingan.discover.react import ReactDiscoverer

ALL_DISCOVERERS = [
    NextJSDiscoverer(),
    ReactDiscoverer(),
    FastAPIDiscoverer(),
    ExpressDiscoverer(),
    DjangoDiscoverer(),
]


def detect_frameworks(project_dir: Path) -> list[FrameworkInfo]:
    """Detect all frameworks used in a project.

    Scans the project directory for framework-specific files and patterns.
    Returns information about each detected framework including its routes.

    Args:
        project_dir: Root directory of the project to scan.

    Returns:
        List of detected frameworks with their route information.
    """
    detected: list[FrameworkInfo] = []

    for discoverer in ALL_DISCOVERERS:
        result = discoverer.detect(project_dir)
        if result is not None:
            detected.append(result)

    return detected
