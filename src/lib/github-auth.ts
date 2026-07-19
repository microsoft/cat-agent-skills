/**
 * GitHub identity for the badge "You" panel.
 *
 * Local POC default: the **username box** (no network, no OAuth) — see
 * `authors.astro`. Anyone can type a login to preview the badge, because the
 * underlying contribution data is public.
 *
 * Real sign-in: GitHub OAuth **device flow**, enabled only when
 * `PUBLIC_GH_CLIENT_ID` is set. GitHub's device endpoints
 * (`/login/device/code`, `/login/oauth/access_token`) send no CORS headers, so
 * browser calls are routed through a proxy at `PUBLIC_GH_PROXY` (default
 * `/__gh`), which the Vite dev server proxies to https://github.com for local
 * testing (see `astro.config.mjs`). A production deploy needs its own tiny
 * proxy — that is the one non-static piece and is intentionally out of scope
 * for this POC. `api.github.com` (the viewer lookup) does send CORS headers, so
 * that call is made directly.
 */

export const GH_CLIENT_ID: string =
  (import.meta.env.PUBLIC_GH_CLIENT_ID as string | undefined) ?? "";
export const GH_PROXY: string =
  (import.meta.env.PUBLIC_GH_PROXY as string | undefined) ?? "/__gh";

/** True when a client id is configured, so the "Sign in with GitHub" path is live. */
export const deviceFlowEnabled = Boolean(GH_CLIENT_ID);

export interface DeviceCode {
  device_code: string;
  user_code: string;
  verification_uri: string;
  expires_in: number;
  interval: number;
}

async function ghPost(path: string, body: Record<string, string>): Promise<any> {
  const res = await fetch(`${GH_PROXY}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`GitHub request failed (${res.status})`);
  return res.json();
}

/**
 * Step 1: request a device + user code to show the signer.
 *
 * Scope is intentionally EMPTY: we only read the viewer's `login` from
 * `GET /user`, which any token can do. An empty scope keeps GitHub's consent
 * screen minimal ("verify your identity") and grants no profile/repo access.
 */
export async function requestDeviceCode(scope = ""): Promise<DeviceCode> {
  return ghPost("/login/device/code", { client_id: GH_CLIENT_ID, scope });
}

/** Step 2: poll until the user authorizes, returning an access token. */
export async function pollForToken(
  dc: DeviceCode,
  signal?: AbortSignal,
): Promise<string> {
  const intervalMs = Math.max(dc.interval || 5, 5) * 1000;
  const deadline = Date.now() + (dc.expires_in || 900) * 1000;
  while (Date.now() < deadline) {
    if (signal?.aborted) throw new Error("cancelled");
    await new Promise((r) => setTimeout(r, intervalMs));
    const data = await ghPost("/login/oauth/access_token", {
      client_id: GH_CLIENT_ID,
      device_code: dc.device_code,
      grant_type: "urn:ietf:params:oauth:grant-type:device_code",
    });
    if (data.access_token) return data.access_token as string;
    if (
      data.error &&
      data.error !== "authorization_pending" &&
      data.error !== "slow_down"
    ) {
      throw new Error(String(data.error_description || data.error));
    }
  }
  throw new Error("Device code expired — please try again.");
}

/** Step 3: resolve the signed-in user's login from the token. */
export async function fetchViewerLogin(token: string): Promise<string> {
  const res = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
    },
  });
  if (!res.ok) throw new Error(`GitHub user lookup failed (${res.status})`);
  const user = await res.json();
  return String(user.login);
}
