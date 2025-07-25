from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

from .enums import SubProcess, ReviewStatus


@dataclass
class VideoDescription:
    """User-provided video description with metadata"""
    text: str
    duration: float = 5.0  # seconds
    fps: int = 24
    resolution: Tuple[int, int] = (1920, 1080)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubProcessDescription:
    """Decomposed sub-process description"""
    process_type: SubProcess
    description: str
    parameters: Dict[str, Any]
    order: int = 0
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ReviewFeedback:
    """Feedback from VLM-Reviewer"""
    status: ReviewStatus
    score: float
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)
    reviewed_at: datetime = field(default_factory=datetime.now)
    
    @property
    def passed(self) -> bool:
        return self.status == ReviewStatus.PASSED


@dataclass
class RenderSettings:
    """Blender render settings"""
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100
    fps: int = 24
    file_format: str = "FFMPEG"
    codec: str = "H264"
    quality: str = "HIGH"
    samples: int = 128


@dataclass
class AssetInfo:
    """3D asset information"""
    name: str
    filepath: str
    asset_type: str  # character, prop, environment
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScriptResult:
    """Result of script execution"""
    success: bool
    script: str
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    artifacts: List[str] = field(default_factory=list)  # Generated files