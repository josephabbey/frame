"""Account and OAuth models shared by API provider implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Account:
    id: str
    provider: str
    display_name: str
    email: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True, slots=True)
class OAuthToken:
    """A token set returned by an OAuth provider.

    ``refresh_token`` should only be persisted in a secure credential store.
    """

    access_token: str
    token_type: str
    expires_at: datetime | None = None
    refresh_token: str | None = None
    scopes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(
            self.expires_at.tzinfo
        )


class AccountAPI(ABC):
    """The OAuth lifecycle that account providers must expose."""

    @abstractmethod
    async def get_account(self, token: OAuthToken) -> Account: ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> OAuthToken: ...
