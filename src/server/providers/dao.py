# -*- coding: utf-8 -*-
"""External provider registry DAO."""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import ExternalProviderRecord


class ExternalProviderDAO:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_key(self, key: str) -> ExternalProviderRecord | None:
        return (
            self._db.query(ExternalProviderRecord)
            .filter(ExternalProviderRecord.key == key)
            .first()
        )

    def list_all(self) -> list[ExternalProviderRecord]:
        return (
            self._db.query(ExternalProviderRecord)
            .order_by(ExternalProviderRecord.key.asc())
            .all()
        )

    def upsert(
        self,
        *,
        key: str,
        label: str,
        kind: str,
        implementation: str,
        is_enabled: bool = True,
        settings_json: str = "{}",
    ) -> ExternalProviderRecord:
        record = self.get_by_key(key)
        if record is None:
            record = ExternalProviderRecord(
                key=key,
                label=label,
                kind=kind,
                implementation=implementation,
                is_enabled=is_enabled,
                settings_json=settings_json,
            )
            self._db.add(record)
        else:
            record.label = label
            record.kind = kind
            record.implementation = implementation
            record.is_enabled = is_enabled
            record.settings_json = settings_json

        self._db.commit()
        self._db.refresh(record)
        return record
