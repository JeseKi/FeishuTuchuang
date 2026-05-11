# -*- coding: utf-8 -*-
"""OAuth DAO."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.server.dao.dao_base import BaseDAO
from .models import OAuthAccount, OAuthLoginTicket


class OAuthAccountDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get_by_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        return (
            self.db_session.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
            .first()
        )

    def get_by_provider_user(self, provider: str, user_id: int) -> OAuthAccount | None:
        return (
            self.db_session.query(OAuthAccount)
            .filter(OAuthAccount.provider == provider, OAuthAccount.user_id == user_id)
            .first()
        )

    def create(
        self,
        *,
        provider: str,
        provider_user_id: str,
        user_id: int,
        provider_username: str | None,
        provider_email: str | None,
        provider_name: str | None,
        avatar_url: str | None,
    ) -> OAuthAccount:
        account = OAuthAccount(
            provider=provider,
            provider_user_id=provider_user_id,
            user_id=user_id,
            provider_username=provider_username,
            provider_email=provider_email,
            provider_name=provider_name,
            avatar_url=avatar_url,
        )
        self.db_session.add(account)
        self.db_session.commit()
        self.db_session.refresh(account)
        return account

    def update_metadata(
        self,
        account: OAuthAccount,
        *,
        provider_username: str | None,
        provider_email: str | None,
        provider_name: str | None,
        avatar_url: str | None,
    ) -> OAuthAccount:
        account.provider_username = provider_username
        account.provider_email = provider_email
        account.provider_name = provider_name
        account.avatar_url = avatar_url
        account.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(account)
        return account


class OAuthLoginTicketDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(
        self,
        *,
        ticket_hash: str,
        provider: str,
        user_id: int,
        challenge_token: str | None,
        expires_at: datetime,
    ) -> OAuthLoginTicket:
        ticket = OAuthLoginTicket(
            ticket_hash=ticket_hash,
            provider=provider,
            user_id=user_id,
            challenge_token=challenge_token,
            expires_at=expires_at,
        )
        self.db_session.add(ticket)
        self.db_session.commit()
        self.db_session.refresh(ticket)
        return ticket

    def get_by_hash(self, ticket_hash: str) -> OAuthLoginTicket | None:
        return (
            self.db_session.query(OAuthLoginTicket)
            .filter(OAuthLoginTicket.ticket_hash == ticket_hash)
            .first()
        )

    def consume(self, ticket: OAuthLoginTicket) -> OAuthLoginTicket:
        if ticket.consumed_at is None:
            ticket.consumed_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(ticket)
        return ticket

