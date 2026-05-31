import { describe, expect, it } from "vitest";

import { errorMessage } from "@/lib/api";

describe("errorMessage", () => {
  it("surfaces Diotali correction messages from blocked issues", () => {
    expect(
      errorMessage(
        {
          diotali_public: {
            blocks_issue: true,
            correction_message:
              "Une attestation Diotali est deja valide. Corriger la date d'effet.",
          },
        },
        400,
      ),
    ).toBe("Une attestation Diotali est deja valide. Corriger la date d'effet.");
  });
});
