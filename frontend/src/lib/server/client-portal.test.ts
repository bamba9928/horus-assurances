import { describe, expect, it } from "vitest";

import {
  clientAccessCookieOptions,
  clientSpaceBackendUrl,
  isClientDocumentDownloadPath,
} from "@/lib/server/client-portal";

describe("client portal server helpers", () => {
  it("builds client-space backend URLs under the configured API base", () => {
    expect(clientSpaceBackendUrl("/me/")).toBe(
      "http://127.0.0.1:8000/api/v1/client-space/me/",
    );
    expect(clientSpaceBackendUrl("contracts/")).toBe(
      "http://127.0.0.1:8000/api/v1/client-space/contracts/",
    );
  });

  it("uses HttpOnly cookie options for the raw client token", () => {
    expect(clientAccessCookieOptions(120)).toMatchObject({
      httpOnly: true,
      maxAge: 120,
      path: "/",
      sameSite: "lax",
    });
  });

  it("detects only OTP-protected document download paths", () => {
    expect(isClientDocumentDownloadPath("/contracts/12/documents/attestation/")).toBe(true);
    expect(isClientDocumentDownloadPath("/contracts/12/documents/carte-brune/")).toBe(true);
    expect(isClientDocumentDownloadPath("/contracts/12/documents/otp/")).toBe(false);
    expect(isClientDocumentDownloadPath("/notifications/")).toBe(false);
  });
});
