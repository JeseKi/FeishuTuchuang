# -*- coding: utf-8 -*-
"""External provider schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderImplementation = Literal["real", "mock"]


class ExternalProviderOut(BaseModel):
    key: str
    label: str
    kind: str
    implementation: ProviderImplementation
    is_enabled: bool
    settings_json: str = Field(default="{}")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
