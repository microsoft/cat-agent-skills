"""Copilot Studio client wrapper for the external content-safety scanner.

Thin async wrapper around the published `microsoft-agents-copilotstudio-client`
package so the red-team runner can talk to a published Copilot Studio agent with
a simple `start_conversation_async()` / `ask_question_async()` interface.

Auth uses an interactive MSAL public-client flow with encrypted OS-backed token
persistence. There is no plaintext fallback. Configure the four required
values as environment variables (see .env.example) or pass an
`McsConnectionSettings` instance explicitly.
"""

from __future__ import annotations

import os
import hashlib
import warnings
from pathlib import Path
from typing import List, Optional

# --- Auth (MSAL) -----------------------------------------------------------
import msal
from msal_extensions import PersistedTokenCache, build_encrypted_persistence

# --- Published Copilot Studio client --------------------------------------
from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
    PowerPlatformCloud,
    AgentType,
)
from microsoft_agents.activity import ActivityTypes  # noqa: F401  (re-exported for callers)

_CACHE_ROOT = Path.home() / ".copilot-content-safety-scan" / "token-cache"
_LEGACY_CACHE_PATH = Path.home() / ".mcs_redteam_token_cache.bin"
# Power Platform API scope used by the Copilot Studio Direct-to-Engine client.
_SCOPE = ["https://api.powerplatform.com/.default"]


def _encrypted_cache(settings: "McsConnectionSettings") -> PersistedTokenCache:
    """Use DPAPI, Keychain or libsecret, scoped by tenant and application."""
    cache_id = hashlib.sha256(
        f"{settings.tenant_id}:{settings.app_client_id}".encode("utf-8")
    ).hexdigest()
    _CACHE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    persistence = build_encrypted_persistence(str(_CACHE_ROOT / f"{cache_id}.bin"))
    if not persistence.is_encrypted:
        raise RuntimeError("Encrypted MSAL persistence is unavailable; plaintext caching is disabled.")
    if _LEGACY_CACHE_PATH.exists():
        warnings.warn(
            "The old plaintext token cache still exists. It will not be read, "
            "migrated or deleted automatically. Review/revoke old sign-in "
            "sessions and remove that legacy cache through your approved process.",
            RuntimeWarning,
            stacklevel=2,
        )
    return PersistedTokenCache(persistence)


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
    """Acquire a user token; cache writes are encrypted and managed by MSAL."""
    cache = _encrypted_cache(settings)

    app = msal.PublicClientApplication(
        client_id=settings.app_client_id,
        authority=f"https://login.microsoftonline.com/{settings.tenant_id}",
        token_cache=cache,
    )

    result = None
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(_SCOPE, account=accounts[0])

    if not result or "access_token" not in result:
        result = app.acquire_token_interactive(scopes=_SCOPE)

    if not result or "access_token" not in result:
        raise RuntimeError(
            f"Failed to acquire token: {(result or {}).get('error', 'no_token_returned')}"
        )
    return result["access_token"]


class McsCopilotClient:
    """Async helper that wraps the published CopilotClient.

    Usage:
        client = McsCopilotClient()                 # settings from env vars
        await client.start_conversation_async()
        activities = await client.ask_question_async("Hello")
    """

    def __init__(
        self,
        connection_settings: Optional[McsConnectionSettings] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self.settings = connection_settings or McsConnectionSettings()
        token = access_token or _acquire_token(self.settings)

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
