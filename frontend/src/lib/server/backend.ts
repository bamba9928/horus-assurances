import { NextResponse } from "next/server";

import type { ApiErrorPayload, TokenPair } from "@/types/api";

export const ACCESS_COOKIE_NAME = "horus_access";
export const REFRESH_COOKIE_NAME = "horus_refresh";

const ACCESS_MAX_AGE_SECONDS = 30 * 60;
const REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;

export const BACKEND_API_BASE_URL = (
  process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

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

export function backendUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${BACKEND_API_BASE_URL}${normalizedPath}`;
}

export function authCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    maxAge,
    path: "/",
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

export function setAuthCookies(cookieStore: CookieStore, tokens: TokenPair) {
  cookieStore.set(
    ACCESS_COOKIE_NAME,
    tokens.access,
    authCookieOptions(ACCESS_MAX_AGE_SECONDS),
  );
  cookieStore.set(
    REFRESH_COOKIE_NAME,
    tokens.refresh,
    authCookieOptions(REFRESH_MAX_AGE_SECONDS),
  );
}

export function clearAuthCookies(cookieStore: CookieStore) {
  cookieStore.delete(ACCESS_COOKIE_NAME);
  cookieStore.delete(REFRESH_COOKIE_NAME);
}

export function getAccessToken(cookieStore: CookieStore) {
  return cookieStore.get(ACCESS_COOKIE_NAME)?.value ?? "";
}

export function getRefreshToken(cookieStore: CookieStore) {
  return cookieStore.get(REFRESH_COOKIE_NAME)?.value ?? "";
}

export async function refreshAccessToken(cookieStore: CookieStore) {
  const refresh = getRefreshToken(cookieStore);
  if (!refresh) {
    clearAuthCookies(cookieStore);
    return "";
  }

  const response = await fetch(backendUrl("/auth/token/refresh/"), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });

  if (!response.ok) {
    clearAuthCookies(cookieStore);
    return "";
  }

  const payload = (await response.json()) as { access?: string; refresh?: string };
  if (!payload.access) {
    clearAuthCookies(cookieStore);
    return "";
  }

  setAuthCookies(cookieStore, {
    access: payload.access,
    refresh: payload.refresh ?? refresh,
  });
  return payload.access;
}

export async function backendResponse(response: Response) {
  if (response.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const contentType = response.headers.get("content-type") ?? "application/json";
  const body = await response.text();
  const headers = new Headers();
  headers.set("Content-Type", contentType);

  const location = response.headers.get("location");
  if (location) {
    headers.set("Location", location);
  }

  return new NextResponse(body, {
    status: response.status,
    headers,
  });
}

export async function errorResponse(status: number, payload: ApiErrorPayload) {
  return NextResponse.json(payload, { status });
}
