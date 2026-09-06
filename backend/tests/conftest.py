# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Test setup: keep the scene cache out of the working tree."""
import os
import tempfile

# Set before advent.mcp_server is imported so its module-level SceneStore uses
# a throwaway directory instead of ./scene-cache.
os.environ.setdefault("ADVENT_SCENE_CACHE", tempfile.mkdtemp(prefix="advent-scenes-"))
