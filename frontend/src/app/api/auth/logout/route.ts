import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { clearAuthCookies } from "@/lib/server/backend";

export const dynamic = "force-dynamic";

export async function POST() {
  clearAuthCookies(await cookies());
  return new NextResponse(null, { status: 204 });
}
