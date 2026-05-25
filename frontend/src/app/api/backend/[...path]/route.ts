import { cookies } from "next/headers";

import {
  backendResponse,
  backendUrl,
  clearAuthCookies,
  getAccessToken,
  refreshAccessToken,
} from "@/lib/server/backend";

export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export async function GET(request: Request, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function PUT(request: Request, context: RouteContext) {
  return proxyBackend(request, context);
}

export async function DELETE(request: Request, context: RouteContext) {
  return proxyBackend(request, context);
}

async function proxyBackend(request: Request, context: RouteContext) {
  const cookieStore = await cookies();
  const { path } = await context.params;
  let access = getAccessToken(cookieStore);

  if (!access) {
    access = await refreshAccessToken(cookieStore);
  }

  if (!access) {
    clearAuthCookies(cookieStore);
    return Response.json({ detail: "Session expiree." }, { status: 401 });
  }

  const backendPath = `/${path.join("/")}/${new URL(request.url).search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
  let response = await forwardRequest(request, backendPath, access, body);

  if (response.status === 401) {
    access = await refreshAccessToken(cookieStore);
    if (access) {
      response = await forwardRequest(request, backendPath, access, body);
    }
  }

  if (response.status === 401) {
    clearAuthCookies(cookieStore);
  }

  return backendResponse(response);
}

async function forwardRequest(
  request: Request,
  backendPath: string,
  access: string,
  body: string | undefined,
) {
  const headers = new Headers();
  headers.set("Accept", request.headers.get("accept") ?? "application/json");
  headers.set("Authorization", `Bearer ${access}`);

  const contentType = request.headers.get("content-type");
  if (contentType && body !== undefined) {
    headers.set("Content-Type", contentType);
  }

  return fetch(backendUrl(backendPath), {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  });
}
