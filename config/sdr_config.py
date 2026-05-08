from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class RsidFilter(BaseModel):
    """Glob patterns controlling which report suites are included or excluded."""

    include: list[str] = Field(default_factory=lambda: ["*"])
    exclude: list[str] = Field(default_factory=list)


class SdrMetadata(BaseModel):
    """Optional metadata written into the generated SDR file."""

    organization: Optional[str] = None
    author: Optional[str] = None


class SdrConfig(BaseModel):
    """Top-level configuration loaded from config.yaml."""

    template_path: Path = Path("aa_en_BRD_SDR_template.xlsx")
    output_dir: Path = Path("./out/")
    rsids: RsidFilter = Field(default_factory=RsidFilter)
    metadata: SdrMetadata = Field(default_factory=SdrMetadata)
    log_retention_days: int = 30

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SdrConfig":
        """Load an SdrConfig from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
