import { cookies } from "next/headers";

import {
  backendResponse,
  backendUrl,
  clearAuthCookies,
  errorResponse,
  setAuthCookies,
} from "@/lib/server/backend";
import type { TokenPair } from "@/types/api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const credentials = (await request.json()) as {
    username?: string;
    password?: string;
  };

  const tokenResponse = await fetch(backendUrl("/auth/token/"), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    }),
    cache: "no-store",
  });

  if (!tokenResponse.ok) {
    clearAuthCookies(cookieStore);
    return backendResponse(tokenResponse);
  }

  const tokens = (await tokenResponse.json()) as Partial<TokenPair>;
  if (!tokens.access || !tokens.refresh) {
    clearAuthCookies(cookieStore);
    return errorResponse(502, { detail: "Reponse d'authentification incomplete." });
  }

  setAuthCookies(cookieStore, {
    access: tokens.access,
    refresh: tokens.refresh,
  });

  const profileResponse = await fetch(backendUrl("/auth/me/"), {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${tokens.access}`,
    },
    cache: "no-store",
  });

  if (!profileResponse.ok) {
    clearAuthCookies(cookieStore);
  }

  return backendResponse(profileResponse);
}
