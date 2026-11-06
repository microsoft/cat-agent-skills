import { normalizeLogin } from "./badges";

export function contributorAvatar(login: string | null | undefined, _name: string): string | null {
  const github = normalizeLogin(login);
  return github ? `https://github.com/${github}.png?size=96` : null;
}
