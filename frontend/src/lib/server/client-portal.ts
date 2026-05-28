import { backendUrl } from "@/lib/server/backend";

export const CLIENT_ACCESS_COOKIE_NAME = "horus_client_access";

const CLIENT_ACCESS_MAX_AGE_SECONDS = 30 * 24 * 60 * 60;

type CookieStore = {
  get: (name: string) => { value: string } | undefined;
  set: (
    name: string,
    value: string,
    options: {
      httpOnly: boolean;
      maxAge: number;
      path: string;
      sameSite: "lax";
      secure: boolean;
    },
  ) => void;
  delete: (name: string) => void;
};

export function clientAccessCookieOptions(maxAge = CLIENT_ACCESS_MAX_AGE_SECONDS) {
  return {
    httpOnly: true,
    maxAge,
    path: "/",
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

export function setClientAccessCookie(cookieStore: CookieStore, token: string) {
  cookieStore.set(
    CLIENT_ACCESS_COOKIE_NAME,
    token,
    clientAccessCookieOptions(),
  );
}

export function clearClientAccessCookie(cookieStore: CookieStore) {
  cookieStore.delete(CLIENT_ACCESS_COOKIE_NAME);
}

export function getClientAccessToken(cookieStore: CookieStore) {
  return cookieStore.get(CLIENT_ACCESS_COOKIE_NAME)?.value ?? "";
}

export function clientSpaceBackendUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return backendUrl(`/client-space${normalizedPath}`);
}

export function isClientDocumentDownloadPath(path: string) {
  return /^\/contracts\/\d+\/documents\/(attestation|carte-brune)\/$/.test(path);
}
