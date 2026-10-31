import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from websockets.asyncio.server import ServerConnection, serve

from frame.data.account import OAuthToken
from frame.flow import FlowClient, FlowSettings
from frame.flow.settings import FlowSettingsStore
from frame.google import (
    GoogleAccountAPI,
    GoogleCalendarAPI,
    GoogleOAuthConfig,
    GooglePhotosAPI,
    GoogleTasksAPI,
)


class MockGoogleTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Mapping[str, str] | None]] = []

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        del params, json
        self.calls.append((method, url, headers))
        if url.endswith("/userinfo"):
            return {
                "sub": "google-user-123",
                "name": "Jane Doe",
                "email": "jane@example.com",
                "picture": "https://example.com/jane.jpg",
            }
        if url.endswith("/token"):
            return {
                "access_token": "new-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "reused-refresh-token",
            }
        return {}


def test_flow_client_initialization_and_urls():
    settings = FlowSettings(
        frame_key="123456789012345678901234",
        flow_url="https://frame-flow.vercel.app",
    )
    client = FlowClient(settings)
    assert client.websocket_url == settings.websocket_url
    assert client.is_connected is False
    assert client.is_relay_connected is False


def test_flow_client_handles_messages_and_credentials(tmp_path):
    async def run():
        store = FlowSettingsStore(tmp_path / "settings.json")
        client = FlowClient(settings_store=store)

        connected_events = 0

        def on_connected_cb():
            nonlocal connected_events
            connected_events += 1

        client.on_connected(on_connected_cb)

        oauth_events: list[tuple[str, OAuthToken]] = []
        client.on_oauth_credentials(lambda prov, tok: oauth_events.append((prov, tok)))

        settings_events: list[FlowSettings] = []
        client.on_settings_update(lambda s: settings_events.append(s))

        custom_received = []
        client.register_handler(
            "custom.alert", lambda payload: custom_received.append(payload)
        )

        # 1. Connected
        await client._handle_message(json.dumps({"type": "connected"}))
        assert connected_events == 1
        assert client.is_relay_connected is True

        # 2. Google credentials
        raw_creds = {
            "type": "google.credentials",
            "credentials": {
                "access_token": "flow-access-token",
                "refresh_token": "flow-refresh-token",
                "token_type": "Bearer",
                "expiry_date": 1730000000000,
                "scopes": [
                    "openid",
                    "email",
                    "https://www.googleapis.com/auth/photoslibrary.readonly",
                ],
            },
        }
        await client._handle_message(json.dumps(raw_creds))

        assert len(oauth_events) == 1
        provider, token = oauth_events[0]
        assert provider == "google"
        assert token.access_token == "flow-access-token"
        assert token.refresh_token == "flow-refresh-token"
        assert "openid" in token.scopes
        # Persisted to settings and store
        assert client.settings.google_token is not None
        assert client.settings.google_token.access_token == "flow-access-token"
        loaded_store_settings = store.load()
        assert loaded_store_settings.google_token is not None
        assert loaded_store_settings.google_token.access_token == "flow-access-token"

        # 3. Remote settings update
        update_msg = {
            "type": "settings.update",
            "settings": {
                "frame_name": "Balcony Frame",
                "display_refresh_seconds": 60,
                "custom": {"brightness": 80},
            },
        }
        await client._handle_message(json.dumps(update_msg))
        assert len(settings_events) == 1
        assert client.settings.frame_name == "Balcony Frame"
        assert client.settings.display_refresh_seconds == 60
        assert store.load().frame_name == "Balcony Frame"

        # 4. Custom message
        await client._handle_message(
            json.dumps({"type": "custom.alert", "level": "info"})
        )
        assert len(custom_received) == 1
        assert custom_received[0]["level"] == "info"

    asyncio.run(run())


def test_flow_client_google_api_factories_and_verification():
    async def run():
        token = OAuthToken(
            access_token="valid-token",
            token_type="Bearer",
            refresh_token="valid-refresh",
            expires_at=datetime.now(UTC),
        )
        settings = FlowSettings(
            frame_key="123456789012345678901234",
            google_token=token,
        )
        client = FlowClient(settings)

        transport = MockGoogleTransport()
        account_api = client.get_google_account_api(transport=transport)
        assert isinstance(account_api, GoogleAccountAPI)
        assert isinstance(
            client.get_google_photos_api(transport=transport), GooglePhotosAPI
        )
        assert isinstance(
            client.get_google_calendar_api(transport=transport), GoogleCalendarAPI
        )
        assert isinstance(
            client.get_google_tasks_api(transport=transport), GoogleTasksAPI
        )

        profile = await client.verify_google_account(
            transport=transport,
            oauth_config=GoogleOAuthConfig("client", "secret", "https://redirect"),
        )
        assert profile is not None
        assert profile.email == "jane@example.com"
        assert profile.display_name == "Jane Doe"

    asyncio.run(run())


def test_flow_client_live_websocket_connection_and_reconnection():
    async def run():
        received_from_device = []
        server_sockets: list[ServerConnection] = []

        async def mock_relay(websocket: ServerConnection):
            server_sockets.append(websocket)
            # Send connected
            await websocket.send(json.dumps({"type": "connected"}))
            async for message in websocket:
                received_from_device.append(json.loads(message))

        async with serve(mock_relay, "127.0.0.1", 0) as server:
            port = server.sockets[0].getsockname()[1]
            ws_url = f"ws://127.0.0.1:{port}/api/socket?role=device&key=123456789012345678901234"

            client = FlowClient(
                websocket_url=ws_url,
                reconnect_delay=0.1,
                max_reconnect_delay=0.5,
            )

            client.start()
            # Wait for connected
            for _ in range(50):
                if client.is_relay_connected:
                    break
                await asyncio.sleep(0.05)

            assert client.is_relay_connected is True

            # Send google credentials from mock server to device
            creds_payload = {
                "type": "google.credentials",
                "credentials": {
                    "access_token": "live-test-token",
                    "refresh_token": "live-refresh",
                    "token_type": "Bearer",
                    "expiry_date": None,
                    "scopes": ["photoslibrary.readonly"],
                },
            }
            await server_sockets[0].send(json.dumps(creds_payload))

            # Wait for acknowledgement to be sent back from device
            for _ in range(50):
                if any(
                    msg.get("type") == "oauth.success" for msg in received_from_device
                ):
                    break
                await asyncio.sleep(0.05)

            assert client.settings.google_token is not None
            assert client.settings.google_token.access_token == "live-test-token"
            assert any(
                msg.get("type") == "oauth.success" for msg in received_from_device
            )

            await client.stop()
            assert client.is_connected is False

    asyncio.run(run())
