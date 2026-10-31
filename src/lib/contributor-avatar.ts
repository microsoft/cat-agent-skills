import { authorKey, normalizeLogin } from "./badges";

// Official asset: https://copilot.microsoft.com/static/cmc/favicon.svg
export function contributorAvatar(login: string | null | undefined, name: string): string | null {
  if (!normalizeLogin(login) && authorKey(login, name) === "copilot-cowork-team") {
    return "/copilot.svg";
  }
  const github = normalizeLogin(login);
  return github ? `https://github.com/${github}.png?size=96` : null;
}
