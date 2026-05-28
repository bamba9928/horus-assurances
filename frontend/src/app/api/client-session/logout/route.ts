import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { clearClientAccessCookie } from "@/lib/server/client-portal";

export const dynamic = "force-dynamic";

export async function POST() {
  clearClientAccessCookie(await cookies());
  return new NextResponse(null, { status: 204 });
}
