import { normalizeLogin } from "./badges";

const LOCAL_AVATARS: Record<string, string> = {
  microsoft: "/microsoft.svg",
};

export function contributorAvatar(login: string | null | undefined, _name: string): string | null {
  const github = normalizeLogin(login);
  if (!github) return null;
  return LOCAL_AVATARS[github] ?? `https://github.com/${github}.png?size=96`;
}
