import { cookies } from "next/headers";

import { backendResponse } from "@/lib/server/backend";
import {
  clearClientAccessCookie,
  clientSpaceBackendUrl,
  setClientAccessCookie,
} from "@/lib/server/client-portal";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const payload = (await request.json()) as { token?: string };
  const token = payload.token?.trim() ?? "";

  if (!token) {
    clearClientAccessCookie(cookieStore);
    return Response.json({ detail: "Jeton client obligatoire." }, { status: 400 });
  }

  const profileResponse = await fetch(clientSpaceBackendUrl("/me/"), {
    headers: {
      Accept: "application/json",
      Authorization: `Client-Token ${token}`,
    },
    cache: "no-store",
  });

  if (!profileResponse.ok) {
    clearClientAccessCookie(cookieStore);
    return backendResponse(profileResponse);
  }

  setClientAccessCookie(cookieStore, token);
  return backendResponse(profileResponse);
}
