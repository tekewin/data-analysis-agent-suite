"""Orchestration module for the Data Analysis Agent Suite.

This module provides pipeline orchestration capabilities for coordinating
the execution of multiple agents in sequence.

Key Components:
- PipelineStage: Enum of pipeline stages
- PipelineConfig: User configuration options
- PipelineState: Runtime state tracking
- PipelineManifest: Execution results documentation

Example:
    >>> from src.orchestration import (
    ...     PipelineStage,
    ...     PipelineConfig,
    ...     PipelineState,
    ...     validate_input_file,
    ... )
    >>> config = PipelineConfig(writing_style="executive")
    >>> validation = validate_input_file("data.csv")
    >>> if validation["valid"]:
    ...     state = PipelineState(source_file="data.csv")
"""

from .pipeline import (
    PipelineStage,
    PipelineConfig,
    PipelineState,
)

from .discovery import (
    SUPPORTED_EXTENSIONS,
    validate_input_file,
    get_source_name,
    find_outputs_for_source,
    find_latest_outputs_for_source,
    discover_resumable_state,
    get_output_path,
    ensure_output_dir,
)

from .manifest import (
    PipelineManifest,
    create_pipeline_manifest,
    save_pipeline_manifest,
    load_pipeline_manifest,
    find_manifests_for_source,
    get_latest_manifest,
)

__all__ = [
    # Pipeline core
    "PipelineStage",
    "PipelineConfig",
    "PipelineState",
    # Discovery
    "SUPPORTED_EXTENSIONS",
    "validate_input_file",
    "get_source_name",
    "find_outputs_for_source",
    "find_latest_outputs_for_source",
    "discover_resumable_state",
    "get_output_path",
    "ensure_output_dir",
    # Manifest
    "PipelineManifest",
    "create_pipeline_manifest",
    "save_pipeline_manifest",
    "load_pipeline_manifest",
    "find_manifests_for_source",
    "get_latest_manifest",
]
