"""Agnostic Google integration used by Frame Flow."""

from typing import Protocol

from frame.data.account import Account
from frame.flow.settings import FlowSettings

from .account import GoogleAccountAPI
from .calendar import GoogleCalendarAPI
from .client import GoogleOAuthConfig
from .photos import GooglePhotosAPI
from .tasks import GoogleTasksAPI
from .transport import GoogleTransport, UrllibGoogleTransport


class GoogleIntegrationProtocol(Protocol):
    """Agnostic interface for Google integration helpers."""

    settings: FlowSettings

    def get_account_api(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> GoogleAccountAPI | None: ...

    def get_photos_api(
        self, transport: GoogleTransport | None = None
    ) -> GooglePhotosAPI | None: ...

    def get_calendar_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleCalendarAPI | None: ...

    def get_tasks_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleTasksAPI | None: ...

    async def verify_account(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> Account | None: ...


class GoogleIntegration:
    """Concrete Google integration for a Frame Flow settings object."""

    def __init__(
        self,
        settings: FlowSettings,
        transport: GoogleTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    def _active_transport(self, transport: GoogleTransport | None) -> GoogleTransport:
        return transport or self.transport or UrllibGoogleTransport()

    def get_account_api(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> GoogleAccountAPI | None:
        token = self.settings.google_token
        if token is None:
            return None
        active_transport = self._active_transport(transport)
        active_oauth = oauth_config or GoogleOAuthConfig(
            client_id="", client_secret="", redirect_uri=""
        )
        return GoogleAccountAPI(active_transport, token, active_oauth)

    get_google_account_api = get_account_api

    def get_photos_api(
        self, transport: GoogleTransport | None = None
    ) -> GooglePhotosAPI | None:
        token = self.settings.google_token
        if token is None:
            return None
        return GooglePhotosAPI(self._active_transport(transport), token)

    get_google_photos_api = get_photos_api

    def get_calendar_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleCalendarAPI | None:
        token = self.settings.google_token
        if token is None:
            return None
        return GoogleCalendarAPI(self._active_transport(transport), token)

    get_google_calendar_api = get_calendar_api

    def get_tasks_api(
        self, transport: GoogleTransport | None = None
    ) -> GoogleTasksAPI | None:
        token = self.settings.google_token
        if token is None:
            return None
        return GoogleTasksAPI(self._active_transport(transport), token)

    get_google_tasks_api = get_tasks_api

    async def verify_account(
        self,
        transport: GoogleTransport | None = None,
        oauth_config: GoogleOAuthConfig | None = None,
    ) -> Account | None:
        account_api = self.get_account_api(transport, oauth_config)
        if account_api is None or self.settings.google_token is None:
            return None

        token = self.settings.google_token
        if (
            token.is_expired
            and token.refresh_token
            and oauth_config
            and oauth_config.client_id
        ):
            refreshed = await account_api.refresh_token(token.refresh_token)
            self.settings.google_token = refreshed
            token = refreshed

        return await account_api.get_account(token)

    verify_google_account = verify_account


# Backward-compatible aliases.
GoogleService = GoogleIntegration
GoogleProvider = GoogleIntegration
GoogleManager = GoogleIntegration
GoogleController = GoogleIntegration
GoogleOAuthClient = GoogleIntegration
GoogleFlowClient = GoogleIntegration
GoogleIntegrationClient = GoogleIntegration
GoogleIntegrationClientAlias = GoogleIntegration
