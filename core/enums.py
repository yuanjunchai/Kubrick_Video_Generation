from enum import Enum #Enumerations


class SubProcess(Enum):
    """Five sub-processes of mise-en-scène"""
    SCENE = "scene"
    CHARACTER = "character"
    MOTION = "motion"
    LIGHTING = "lighting"
    CINEMATOGRAPHY = "cinematography"


class ReviewStatus(Enum):
    """Review status outcomes"""
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVISION = "needs_revision"


class MotionType(Enum):
    """Supported motion types"""
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    FLY = "fly"
    IDLE = "idle"
    CUSTOM = "custom"


class CameraAnimation(Enum):
    """Camera animation types"""
    STATIC = "static"
    ORBIT = "orbit"
    DOLLY = "dolly"
    PAN = "pan"
    TRACKING = "tracking"
    HANDHELD = "handheld"


class LightingType(Enum):
    """Lighting setup types"""
    SUN = "sun"
    POINT = "point"
    SPOT = "spot"
    AREA = "area"
    HDRI = "hdri"