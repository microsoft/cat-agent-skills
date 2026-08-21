"""Copilot Studio client wrapper for AI Red Teaming.

Thin async wrapper around the preview `microsoft-agents-copilotstudio-client`
package so the red-team runner can talk to a published Copilot Studio agent with
a simple `start_conversation_async()` / `ask_question_async()` interface.

Preview install (from a terminal, virtual env activated):

    pip install msal msal-extensions
    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ \
        microsoft-agents-core microsoft-agents-copilotstudio-client microsoft-agents-authentication-msal

Auth uses an interactive MSAL public-client flow (device/interactive) and caches
the token on disk so repeated scan probes reuse it. Configure the four required
values as environment variables (see .env.example) or pass an
`McsConnectionSettings` instance explicitly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

# --- Auth (MSAL) -----------------------------------------------------------
import msal

# --- Copilot Studio client (preview) ---------------------------------------
# Import names follow the microsoft-agents-copilotstudio-client preview package.
from microsoft.agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformCloud,
    AgentType,
)
from microsoft.agents.core.models import ActivityTypes  # noqa: F401  (re-exported for callers)

_TOKEN_CACHE_PATH = Path(os.path.expanduser("~")) / ".mcs_redteam_token_cache.bin"
# Power Platform API scope used by the Copilot Studio Direct-to-Engine client.
_SCOPE = ["https://api.powerplatform.com/.default"]


def _write_token_cache(cache: "msal.SerializableTokenCache") -> None:
    """Persist the MSAL token cache with owner-only permissions.

    The cache can contain refresh tokens, so it must not be world-readable on a
    shared machine. We create the file with 0o600 (owner read/write only) before
    writing and re-assert the mode afterwards. On Windows, POSIX mode bits are
    advisory; for stronger protection there, prefer msal-extensions'
    encrypted/persisted cache (PersistedTokenCache with a DPAPI-backed store).
    """
    data = cache.serialize().encode("utf-8")
    # Open with O_CREAT|O_WRONLY|O_TRUNC and a restrictive mode so the file is
    # never briefly created world-readable.
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(_TOKEN_CACHE_PATH), flags, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    try:
        os.chmod(_TOKEN_CACHE_PATH, 0o600)
    except OSError:
        pass  # best-effort on platforms where chmod is a no-op


class McsConnectionSettings:
    """Connection settings for a published Copilot Studio agent."""

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        app_client_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        agent_identifier: Optional[str] = None,
        cloud: PowerPlatformCloud = PowerPlatformCloud.PROD,
        agent_type: AgentType = AgentType.PUBLISHED,
    ) -> None:
        self.tenant_id = tenant_id or os.environ["TENANT_ID"]
        self.app_client_id = app_client_id or os.environ["APP_CLIENT_ID"]
        self.environment_id = environment_id or os.environ["ENVIRONMENT_ID"]
        self.agent_identifier = agent_identifier or os.environ["AGENT_IDENTIFIER"]
        self.cloud = cloud
        self.agent_type = agent_type


def _acquire_token(settings: McsConnectionSettings) -> str:
    """Acquire an access token via MSAL, using a persistent on-disk cache."""
    cache = msal.SerializableTokenCache()
    if _TOKEN_CACHE_PATH.exists():
        cache.deserialize(_TOKEN_CACHE_PATH.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        client_id=settings.app_client_id,
        authority=f"https://login.microsoftonline.com/{settings.tenant_id}",
        token_cache=cache,
    )

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(_SCOPE, account=accounts[0])

    if not result:
        # Interactive fallback (opens a browser). Swap for device-code flow in
        # headless environments: app.acquire_token_by_device_flow(...).
        result = app.acquire_token_interactive(scopes=_SCOPE)

    if cache.has_state_changed:
        _write_token_cache(cache)

    if "access_token" not in result:
        raise RuntimeError(
            f"Failed to acquire token: {result.get('error')}: {result.get('error_description')}"
        )
    return result["access_token"]


class McsCopilotClient:
    """Async helper that wraps the preview CopilotClient.

    Usage:
        client = McsCopilotClient()                 # settings from env vars
        await client.start_conversation_async()
        activities = await client.ask_question_async("Hello")
    """

    def __init__(self, connection_settings: Optional[McsConnectionSettings] = None) -> None:
        self.settings = connection_settings or McsConnectionSettings()
        token = _acquire_token(self.settings)

        conn = ConnectionSettings(
            environment_id=self.settings.environment_id,
            agent_identifier=self.settings.agent_identifier,
            cloud=self.settings.cloud,
            copilot_agent_type=self.settings.agent_type,
        )
        self._client = CopilotClient(conn, token)
        self._conversation_id: Optional[str] = None

    async def start_conversation_async(self) -> List[object]:
        """Start a conversation and capture the conversation id. Returns the
        welcome activities."""
        activities: List[object] = []
        async for activity in self._client.start_conversation():
            activities.append(activity)
            conv = getattr(getattr(activity, "conversation", None), "id", None)
            if conv:
                self._conversation_id = conv
        return activities

    async def ask_question_async(self, question: str) -> List[object]:
        """Send a prompt to the agent and return all returned activities."""
        if not self._conversation_id:
            await self.start_conversation_async()
        activities: List[object] = []
        async for activity in self._client.ask_question(question, self._conversation_id):
            activities.append(activity)
        return activities
