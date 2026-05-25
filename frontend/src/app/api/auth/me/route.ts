import { cookies } from "next/headers";

import {
  backendResponse,
  backendUrl,
  clearAuthCookies,
  getAccessToken,
  refreshAccessToken,
} from "@/lib/server/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  const cookieStore = await cookies();
  let access = getAccessToken(cookieStore);

  if (!access) {
    access = await refreshAccessToken(cookieStore);
  }

  if (!access) {
    clearAuthCookies(cookieStore);
    return Response.json({ detail: "Session expiree." }, { status: 401 });
  }

  let response = await fetch(backendUrl("/auth/me/"), {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${access}`,
    },
    cache: "no-store",
  });

  if (response.status === 401) {
    access = await refreshAccessToken(cookieStore);
    if (access) {
      response = await fetch(backendUrl("/auth/me/"), {
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${access}`,
        },
        cache: "no-store",
      });
    }
  }

  if (response.status === 401) {
    clearAuthCookies(cookieStore);
  }

  return backendResponse(response);
}
