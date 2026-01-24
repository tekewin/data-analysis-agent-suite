"""Chart manifest generation for metadata tracking."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import uuid

from .generator import GeneratedChart


# =============================================================================
# MANIFEST DATACLASSES
# =============================================================================

@dataclass
class ChartManifestEntry:
    """Metadata for a single chart in the manifest."""

    id: str
    chart_type: str
    title: str
    filename: str
    columns_used: List[str]
    description: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'chart_type': self.chart_type,
            'title': self.title,
            'filename': self.filename,
            'columns_used': self.columns_used,
            'description': self.description,
            'generated_at': self.generated_at,
        }


@dataclass
class ChartManifest:
    """Complete manifest of generated charts."""

    source_file: str
    generated_at: str
    output_dir: str
    dashboard_file: str
    charts: List[ChartManifestEntry] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'source_file': self.source_file,
            'generated_at': self.generated_at,
            'output_dir': self.output_dir,
            'dashboard_file': self.dashboard_file,
            'total_charts': len(self.charts),
            'charts': [c.to_dict() for c in self.charts],
        }


# =============================================================================
# MANIFEST GENERATION
# =============================================================================

def create_manifest_entry(chart: GeneratedChart) -> ChartManifestEntry:
    """
    Create a manifest entry from a generated chart.

    Args:
        chart: GeneratedChart object

    Returns:
        ChartManifestEntry with metadata
    """
    return ChartManifestEntry(
        id=str(uuid.uuid4())[:8],  # Short unique ID
        chart_type=chart.chart_type,
        title=chart.title,
        filename=chart.filename,
        columns_used=chart.columns_used,
        description=chart.description,
        generated_at=datetime.now().isoformat(),
    )


def create_manifest(
    charts: List[GeneratedChart],
    source_file: str,
    output_dir: str,
    dashboard_file: str = 'index.html',
) -> ChartManifest:
    """
    Create a manifest for all generated charts.

    Args:
        charts: List of GeneratedChart objects
        source_file: Name of source data file
        output_dir: Output directory path
        dashboard_file: Name of dashboard file

    Returns:
        ChartManifest object
    """
    entries = [create_manifest_entry(chart) for chart in charts]

    return ChartManifest(
        source_file=source_file,
        generated_at=datetime.now().isoformat(),
        output_dir=output_dir,
        dashboard_file=dashboard_file,
        charts=entries,
    )


def save_manifest(manifest: ChartManifest, output_dir: str) -> str:
    """
    Save manifest to a JSON file.

    Args:
        manifest: ChartManifest to save
        output_dir: Directory to save the file

    Returns:
        Path to saved manifest file
    """
    output_path = Path(output_dir) / 'chart_manifest.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)

    return str(output_path.resolve())


def load_manifest(manifest_path: str) -> ChartManifest:
    """
    Load a manifest from a JSON file.

    Args:
        manifest_path: Path to manifest JSON file

    Returns:
        ChartManifest object
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    charts = [
        ChartManifestEntry(
            id=c['id'],
            chart_type=c['chart_type'],
            title=c['title'],
            filename=c['filename'],
            columns_used=c['columns_used'],
            description=c['description'],
            generated_at=c['generated_at'],
        )
        for c in data.get('charts', [])
    ]

    return ChartManifest(
        source_file=data.get('source_file', ''),
        generated_at=data.get('generated_at', ''),
        output_dir=data.get('output_dir', ''),
        dashboard_file=data.get('dashboard_file', 'index.html'),
        charts=charts,
        version=data.get('version', '1.0'),
    )
