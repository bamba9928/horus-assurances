import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendResponse } from "@/lib/server/backend";
import {
  clearClientAccessCookie,
  clientSpaceBackendUrl,
  getClientAccessToken,
  isClientDocumentDownloadPath,
} from "@/lib/server/client-portal";

export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export async function GET(request: Request, context: RouteContext) {
  return proxyClientSpace(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxyClientSpace(request, context);
}

async function proxyClientSpace(request: Request, context: RouteContext) {
  const cookieStore = await cookies();
  const clientToken = getClientAccessToken(cookieStore);

  if (!clientToken) {
    clearClientAccessCookie(cookieStore);
    return Response.json({ detail: "Session client expiree." }, { status: 401 });
  }

  const { path } = await context.params;
  const clientSpacePath = `/${path.join("/")}/`;
  const search = new URL(request.url).search;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
  const response = await forwardClientSpaceRequest(
    request,
    `${clientSpacePath}${search}`,
    clientToken,
    body,
  );

  if (response.status === 401 || response.status === 403) {
    if (response.status === 401) {
      clearClientAccessCookie(cookieStore);
    }
    return backendResponse(response);
  }

  const location = response.headers.get("location");
  if (location && isClientDocumentDownloadPath(clientSpacePath)) {
    return NextResponse.json({ download_url: location });
  }

  return backendResponse(response);
}

async function forwardClientSpaceRequest(
  request: Request,
  clientSpacePath: string,
  clientToken: string,
  body: string | undefined,
) {
  const headers = new Headers();
  headers.set("Accept", request.headers.get("accept") ?? "application/json");
  headers.set("Authorization", `Client-Token ${clientToken}`);

  const contentType = request.headers.get("content-type");
  if (contentType && body !== undefined) {
    headers.set("Content-Type", contentType);
  }

  const otp = request.headers.get("x-client-otp");
  if (otp) {
    headers.set("X-Client-OTP", otp);
  }

  return fetch(clientSpaceBackendUrl(clientSpacePath), {
    method: request.method,
    headers,
    body,
    cache: "no-store",
    redirect: "manual",
  });
}
