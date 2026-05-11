# -*- coding: utf-8 -*-
"""
认证模块 DAO（模板版）

公开接口：
- `UserDAO`

内部方法：
- 无

说明：
- 提供用户读取/写入的持久化封装，业务逻辑放在 service。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session, object_session

from src.server.dao.dao_base import BaseDAO
from .models import BackupCode, LoginChallenge, RefreshToken, User


class UserDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def get_by_username(self, username: str) -> User | None:
        return self.db_session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db_session.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db_session.query(User).filter(User.id == user_id).first()

    def list_all(self) -> list[User]:
        return self.db_session.query(User).order_by(User.id.desc()).all()

    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        **fields,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            **fields,
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        return user

    def update(self, user: User, **fields) -> User:
        managed_user = user
        if object_session(user) is not self.db_session:
            if user.id is None:
                raise ValueError("用户不存在")
            fetched_user = self.get_by_id(user.id)
            if fetched_user is None:
                raise ValueError("用户不存在")
            managed_user = fetched_user

        for k, v in fields.items():
            setattr(managed_user, k, v)
        self.db_session.commit()
        self.db_session.refresh(managed_user)
        return managed_user

    def bump_token_version(self, user: User) -> User:
        managed_user = self.get_by_id(user.id)
        if managed_user is None:
            raise ValueError("用户不存在")
        managed_user.token_version += 1
        self.db_session.commit()
        self.db_session.refresh(managed_user)
        return managed_user

    def delete(self, user: User) -> None:
        self.db_session.delete(user)
        self.db_session.commit()


class RefreshTokenDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(self, user_id: int, jti: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self.db_session.add(refresh_token)
        self.db_session.commit()
        self.db_session.refresh(refresh_token)
        return refresh_token

    def get_by_jti(self, jti: str) -> RefreshToken | None:
        return (
            self.db_session.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        )

    def get_active_by_jti(self, jti: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        return (
            self.db_session.query(RefreshToken)
            .filter(
                RefreshToken.jti == jti,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .first()
        )

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        if refresh_token.revoked_at is None:
            refresh_token.revoked_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(refresh_token)
        return refresh_token

    def revoke_all_for_user(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        updated = (
            self.db_session.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .update({RefreshToken.revoked_at: now}, synchronize_session=False)
        )
        self.db_session.commit()
        return int(updated)


class BackupCodeDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_many(self, user_id: int, code_hashes: list[str]) -> list[BackupCode]:
        backup_codes = [
            BackupCode(user_id=user_id, code_hash=code_hash)
            for code_hash in code_hashes
        ]
        self.db_session.add_all(backup_codes)
        self.db_session.commit()
        for backup_code in backup_codes:
            self.db_session.refresh(backup_code)
        return backup_codes

    def list_active_for_user(self, user_id: int) -> list[BackupCode]:
        return (
            self.db_session.query(BackupCode)
            .filter(
                BackupCode.user_id == user_id,
                BackupCode.used_at.is_(None),
            )
            .order_by(BackupCode.id.asc())
            .all()
        )

    def mark_used(self, backup_code: BackupCode) -> BackupCode:
        if backup_code.used_at is None:
            backup_code.used_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(backup_code)
        return backup_code

    def delete_all_for_user(self, user_id: int) -> int:
        deleted = (
            self.db_session.query(BackupCode)
            .filter(BackupCode.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db_session.commit()
        return int(deleted)


class LoginChallengeDAO(BaseDAO):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create(
        self, user_id: int, challenge_jti: str, expires_at: datetime
    ) -> LoginChallenge:
        challenge = LoginChallenge(
            user_id=user_id,
            challenge_jti=challenge_jti,
            expires_at=expires_at,
        )
        self.db_session.add(challenge)
        self.db_session.commit()
        self.db_session.refresh(challenge)
        return challenge

    def get_by_jti(self, challenge_jti: str) -> LoginChallenge | None:
        return (
            self.db_session.query(LoginChallenge)
            .filter(LoginChallenge.challenge_jti == challenge_jti)
            .first()
        )

    def increment_attempts(self, challenge: LoginChallenge) -> LoginChallenge:
        challenge.attempt_count += 1
        self.db_session.commit()
        self.db_session.refresh(challenge)
        return challenge

    def consume(self, challenge: LoginChallenge) -> LoginChallenge:
        if challenge.consumed_at is None:
            challenge.consumed_at = datetime.now(timezone.utc)
            self.db_session.commit()
            self.db_session.refresh(challenge)
        return challenge
