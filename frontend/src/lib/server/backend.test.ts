import { describe, expect, it } from "vitest";

import { authCookieOptions, backendUrl } from "@/lib/server/backend";

describe("backend proxy helpers", () => {
  it("builds backend URLs without exposing tokens to the browser", () => {
    expect(backendUrl("/clients/")).toBe("http://127.0.0.1:8000/api/v1/clients/");
    expect(backendUrl("quotes/")).toBe("http://127.0.0.1:8000/api/v1/quotes/");
  });

  it("uses HttpOnly cookie options for JWT storage", () => {
    expect(authCookieOptions(60)).toMatchObject({
      httpOnly: true,
      maxAge: 60,
      path: "/",
      sameSite: "lax",
    });
  });
});
