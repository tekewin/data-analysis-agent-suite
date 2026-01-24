"""Pipeline configuration and state management for the orchestrator.

This module defines the core dataclasses for managing pipeline execution:
- PipelineStage: Enum of pipeline stages
- PipelineConfig: User configuration options
- PipelineState: Runtime state tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PipelineStage(Enum):
    """Stages in the data analysis pipeline.

    The pipeline executes in this order:
    1. CLEANING - Clean and prepare raw data
    2. ANALYSIS - Perform statistical analysis
    3. VISUALIZATION - Generate charts and dashboard
    4. REPORT - Write full analysis report
    5. SUMMARY - Create executive summary
    """
    CLEANING = "cleaning"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORT = "report"
    SUMMARY = "summary"

    @classmethod
    def from_string(cls, value: str) -> "PipelineStage":
        """Convert string to PipelineStage.

        Args:
            value: Stage name (case-insensitive)

        Returns:
            Corresponding PipelineStage

        Raises:
            ValueError: If value doesn't match any stage
        """
        value_lower = value.lower().strip()
        # Handle common aliases
        aliases = {
            "cleaned": cls.CLEANING,
            "clean": cls.CLEANING,
            "analyzed": cls.ANALYSIS,
            "analyze": cls.ANALYSIS,
            "visualized": cls.VISUALIZATION,
            "viz": cls.VISUALIZATION,
            "reported": cls.REPORT,
            "summarized": cls.SUMMARY,
        }
        if value_lower in aliases:
            return aliases[value_lower]

        for stage in cls:
            if stage.value == value_lower:
                return stage
        raise ValueError(f"Unknown pipeline stage: {value}")

    @classmethod
    def get_order(cls) -> List["PipelineStage"]:
        """Get stages in execution order.

        Returns:
            List of stages in order
        """
        return [
            cls.CLEANING,
            cls.ANALYSIS,
            cls.VISUALIZATION,
            cls.REPORT,
            cls.SUMMARY,
        ]

    def get_index(self) -> int:
        """Get the index of this stage in the execution order.

        Returns:
            Zero-based index
        """
        return self.get_order().index(self)

    def is_critical(self) -> bool:
        """Check if this stage is critical (pipeline stops on failure).

        Returns:
            True if critical, False if can be skipped
        """
        return self in (PipelineStage.CLEANING, PipelineStage.ANALYSIS)


@dataclass
class PipelineConfig:
    """Configuration options for pipeline execution.

    Attributes:
        skip_stages: List of stages to skip
        writing_style: Report writing style (technical, business, executive)
        analysis_depth: Analysis depth (quick_scan, standard, deep_dive)
        resume_from: Stage to resume from (uses existing outputs)
        output_dir: Directory for output files
    """
    skip_stages: List[PipelineStage] = field(default_factory=list)
    writing_style: str = "business"
    analysis_depth: str = "standard"
    resume_from: Optional[PipelineStage] = None
    output_dir: str = "./output"

    def __post_init__(self) -> None:
        """Validate configuration values."""
        valid_styles = ("technical", "business", "executive")
        if self.writing_style not in valid_styles:
            raise ValueError(
                f"Invalid writing_style: {self.writing_style}. "
                f"Must be one of: {valid_styles}"
            )

        valid_depths = ("quick_scan", "standard", "deep_dive")
        if self.analysis_depth not in valid_depths:
            raise ValueError(
                f"Invalid analysis_depth: {self.analysis_depth}. "
                f"Must be one of: {valid_depths}"
            )

    def should_skip(self, stage: PipelineStage) -> bool:
        """Check if a stage should be skipped.

        Args:
            stage: The stage to check

        Returns:
            True if stage should be skipped
        """
        return stage in self.skip_stages

    def get_stages_to_execute(self) -> List[PipelineStage]:
        """Get the list of stages that will actually execute.

        Takes into account skip_stages and resume_from.

        Returns:
            List of stages to execute in order
        """
        all_stages = PipelineStage.get_order()

        # If resuming, start from that stage
        if self.resume_from is not None:
            start_index = self.resume_from.get_index()
            all_stages = all_stages[start_index:]

        # Remove skipped stages
        return [s for s in all_stages if s not in self.skip_stages]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "skip_stages": [s.value for s in self.skip_stages],
            "writing_style": self.writing_style,
            "analysis_depth": self.analysis_depth,
            "resume_from": self.resume_from.value if self.resume_from else None,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Create from dictionary.

        Args:
            data: Dictionary with config values

        Returns:
            PipelineConfig instance
        """
        skip_stages = [
            PipelineStage.from_string(s)
            for s in data.get("skip_stages", [])
        ]
        resume_from = None
        if data.get("resume_from"):
            resume_from = PipelineStage.from_string(data["resume_from"])

        return cls(
            skip_stages=skip_stages,
            writing_style=data.get("writing_style", "business"),
            analysis_depth=data.get("analysis_depth", "standard"),
            resume_from=resume_from,
            output_dir=data.get("output_dir", "./output"),
        )


@dataclass
class PipelineState:
    """Runtime state of pipeline execution.

    Tracks the current state of the pipeline including completed stages
    and output file paths from each stage.

    Attributes:
        source_file: Path to the original input file
        timestamp: Execution timestamp (YYYYMMDD_HHMMSS format)
        cleaned_csv_path: Path to cleaned CSV from cleaning stage
        analysis_json_path: Path to analysis JSON from analysis stage
        analysis_md_path: Path to analysis markdown summary
        visualization_dir: Directory containing visualization outputs
        report_path: Path to generated report
        summary_path: Path to executive summary
        completed_stages: List of completed stage names
        failed_stage: Name of stage that failed (if any)
        error_message: Error message from failed stage (if any)
    """
    source_file: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    cleaned_csv_path: Optional[str] = None
    analysis_json_path: Optional[str] = None
    analysis_md_path: Optional[str] = None
    visualization_dir: Optional[str] = None
    report_path: Optional[str] = None
    summary_path: Optional[str] = None
    completed_stages: List[str] = field(default_factory=list)
    failed_stage: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def source_name(self) -> str:
        """Get the base name of the source file without extension.

        Returns:
            Base name (e.g., 'sales_data' from 'sales_data.csv')
        """
        import os
        basename = os.path.basename(self.source_file)
        name, _ = os.path.splitext(basename)
        return name

    @property
    def is_failed(self) -> bool:
        """Check if the pipeline has failed.

        Returns:
            True if a stage has failed
        """
        return self.failed_stage is not None

    @property
    def is_complete(self) -> bool:
        """Check if all requested stages are complete.

        Returns:
            True if no failures and at least one stage completed
        """
        return not self.is_failed and len(self.completed_stages) > 0

    def mark_stage_complete(self, stage: PipelineStage) -> None:
        """Mark a stage as completed.

        Args:
            stage: The completed stage
        """
        if stage.value not in self.completed_stages:
            self.completed_stages.append(stage.value)

    def mark_stage_failed(self, stage: PipelineStage, error: str) -> None:
        """Mark a stage as failed.

        Args:
            stage: The failed stage
            error: Error message
        """
        self.failed_stage = stage.value
        self.error_message = error

    def get_stage_output(self, stage: PipelineStage) -> Optional[str]:
        """Get the output path for a specific stage.

        Args:
            stage: The stage to get output for

        Returns:
            Path to output file/directory, or None if not set
        """
        stage_outputs = {
            PipelineStage.CLEANING: self.cleaned_csv_path,
            PipelineStage.ANALYSIS: self.analysis_json_path,
            PipelineStage.VISUALIZATION: self.visualization_dir,
            PipelineStage.REPORT: self.report_path,
            PipelineStage.SUMMARY: self.summary_path,
        }
        return stage_outputs.get(stage)

    def set_stage_output(self, stage: PipelineStage, path: str) -> None:
        """Set the output path for a specific stage.

        Args:
            stage: The stage to set output for
            path: Path to output file/directory
        """
        if stage == PipelineStage.CLEANING:
            self.cleaned_csv_path = path
        elif stage == PipelineStage.ANALYSIS:
            self.analysis_json_path = path
        elif stage == PipelineStage.VISUALIZATION:
            self.visualization_dir = path
        elif stage == PipelineStage.REPORT:
            self.report_path = path
        elif stage == PipelineStage.SUMMARY:
            self.summary_path = path

    def get_all_outputs(self) -> Dict[str, Optional[str]]:
        """Get all output paths as a dictionary.

        Returns:
            Dictionary mapping stage names to output paths
        """
        return {
            "cleaned_csv": self.cleaned_csv_path,
            "analysis_json": self.analysis_json_path,
            "analysis_md": self.analysis_md_path,
            "visualization_dir": self.visualization_dir,
            "report": self.report_path,
            "summary": self.summary_path,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "source_file": self.source_file,
            "timestamp": self.timestamp,
            "cleaned_csv_path": self.cleaned_csv_path,
            "analysis_json_path": self.analysis_json_path,
            "analysis_md_path": self.analysis_md_path,
            "visualization_dir": self.visualization_dir,
            "report_path": self.report_path,
            "summary_path": self.summary_path,
            "completed_stages": self.completed_stages,
            "failed_stage": self.failed_stage,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        """Create from dictionary.

        Args:
            data: Dictionary with state values

        Returns:
            PipelineState instance
        """
        return cls(
            source_file=data["source_file"],
            timestamp=data.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S")),
            cleaned_csv_path=data.get("cleaned_csv_path"),
            analysis_json_path=data.get("analysis_json_path"),
            analysis_md_path=data.get("analysis_md_path"),
            visualization_dir=data.get("visualization_dir"),
            report_path=data.get("report_path"),
            summary_path=data.get("summary_path"),
            completed_stages=data.get("completed_stages", []),
            failed_stage=data.get("failed_stage"),
            error_message=data.get("error_message"),
        )
