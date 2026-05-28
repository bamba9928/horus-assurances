import { describe, expect, it } from "vitest";

import { buildPayload, validateBusinessRules } from "@/lib/resource-form";
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

  it("converts guided quote business fields to backend payloads", () => {
    const quoteFields: ResourceFormField[] = [
      { name: "product_type", label: "Produit", type: "select" },
      { name: "coverage_options", label: "Garanties", type: "coverage-options" },
      { name: "ass_product_data", label: "Donnees ASS", type: "ass-product-data" },
    ];

    const payload = buildPayload(quoteFields, {
      product_type: "MOTO",
      coverage_options: [1, 2, 4],
      ass_product_data: {
        cylindre: "126",
        usage: "NON_COMMERCIAL",
      },
    });

    expect(payload).toEqual({
      product_type: "MOTO",
      coverage_options: [1, 2, 4],
      ass_product_data: {
        cylindre: 126,
        usage: "NON_COMMERCIAL",
      },
    });
  });

  it("parses ASS product arrays entered as text", () => {
    const quoteFields: ResourceFormField[] = [
      { name: "product_type", label: "Produit", type: "select" },
      { name: "ass_product_data", label: "Donnees ASS", type: "ass-product-data" },
    ];

    const payload = buildPayload(quoteFields, {
      product_type: "AUTO",
      ass_product_data: {
        garantiesOptPT: "1, 2",
        garantiesOptAR: "4",
      },
    });

    expect(payload.ass_product_data).toEqual({
      garantiesOptPT: [1, 2],
      garantiesOptAR: [4],
    });
  });
});

describe("validateBusinessRules", () => {
  it("validates client identity according to client type", () => {
    expect(
      validateBusinessRules("clients", {
        client_type: "COMPANY",
        company_name: "",
      }),
    ).toContain("Client personne morale : la societe est obligatoire.");
  });

  it("validates quote dates and ASS product requirements", () => {
    const errors = validateBusinessRules("quotes", {
      product_type: "MOTO",
      duration: 0,
      effective_date: "2026-05-30",
      expiration_date: "2026-05-29",
      ass_product_data: { usage: "" },
    });

    expect(errors).toEqual(
      expect.arrayContaining([
        "Devis : la duree doit etre comprise entre 1 et 120.",
        "Devis : la date d'effet doit etre anterieure a la date d'expiration.",
        "Produit moto : le cylindre est obligatoire.",
        "Produit moto : l'usage est obligatoire.",
      ]),
    );
  });
});
