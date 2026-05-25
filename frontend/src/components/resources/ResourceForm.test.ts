import { describe, expect, it } from "vitest";

import { buildPayload } from "@/lib/resource-form";
import type { ResourceFormField } from "@/lib/resources";

const fields: ResourceFormField[] = [
  { name: "client", label: "Client", type: "relation", required: true },
  { name: "contributor", label: "Apporteur", type: "relation", omitIfBlank: true },
  { name: "duration", label: "Duree", type: "number" },
  { name: "fees_amount", label: "Frais", type: "money" },
  { name: "coverage_options", label: "Garanties", type: "json" },
  { name: "is_active", label: "Actif", type: "checkbox" },
  { name: "effective_date", label: "Date effet", type: "date" },
  { name: "password", label: "Mot de passe", type: "password", omitIfBlank: true },
];

describe("buildPayload", () => {
  it("converts form values to backend payload types", () => {
    const payload = buildPayload(fields, {
      client: "12",
      contributor: "",
      duration: "6",
      fees_amount: "3000.00",
      coverage_options: "[1,2,4]",
      is_active: true,
      effective_date: "2026-05-25",
      password: "",
    });

    expect(payload).toEqual({
      client: 12,
      duration: 6,
      fees_amount: "3000.00",
      coverage_options: [1, 2, 4],
      is_active: true,
      effective_date: "2026-05-25",
    });
  });

  it("raises on invalid JSON fields", () => {
    expect(() =>
      buildPayload(fields, {
        client: "12",
        duration: "6",
        fees_amount: "3000.00",
        coverage_options: "{bad json",
        is_active: true,
      }),
    ).toThrow();
  });
});
