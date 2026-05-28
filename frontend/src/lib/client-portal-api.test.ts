import { describe, expect, it } from "vitest";

import { clientDocumentPath } from "@/lib/client-portal-api";

describe("client portal api helpers", () => {
  it("maps document kinds to backend routes", () => {
    expect(clientDocumentPath(42, "attestation")).toBe(
      "/contracts/42/documents/attestation/",
    );
    expect(clientDocumentPath(42, "carte_brune")).toBe(
      "/contracts/42/documents/carte-brune/",
    );
  });
});
