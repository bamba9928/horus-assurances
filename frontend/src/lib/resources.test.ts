import { describe, expect, it } from "vitest";

import {
  canCreate,
  canDelete,
  canEdit,
  editablePayload,
  getResource,
  initialPayload,
  resourcesForRole,
} from "@/lib/resources";

describe("resources configuration", () => {
  it("limits contributor navigation to operational resources", () => {
    const slugs = resourcesForRole("CONTRIBUTOR").map((resource) => resource.slug);

    expect(slugs).toContain("clients");
    expect(slugs).toContain("vehicles");
    expect(slugs).toContain("quotes");
    expect(slugs).toContain("client-access-tokens");
    expect(slugs).not.toContain("groups");
    expect(slugs).not.toContain("users");
    expect(slugs).not.toContain("audit-logs");
  });

  it("allows creating but not editing client access tokens", () => {
    const resource = getResource("client-access-tokens");

    expect(resource).toBeDefined();
    expect(canCreate(resource!)).toBe(true);
    expect(canEdit(resource!)).toBe(false);
    expect(canDelete(resource!)).toBe(false);
  });

  it("builds form defaults from field definitions", () => {
    const resource = getResource("quotes");

    expect(initialPayload(resource!)).toMatchObject({
      product_type: "AUTO",
      periodicity: "MOIS",
      duration: 12,
      coverage_options: [],
      ass_product_data: {},
    });
  });

  it("keeps only editable configured fields", () => {
    const resource = getResource("clients");
    const payload = editablePayload(resource!, {
      id: 10,
      display_name: "Awa Fall",
      phone: "771234567",
      partner_group_name: "Groupe A",
      client_type: "INDIVIDUAL",
      is_active: true,
    });

    expect(payload).toEqual(
      expect.objectContaining({
        phone: "771234567",
        client_type: "INDIVIDUAL",
        is_active: true,
      }),
    );
    expect(payload).not.toHaveProperty("display_name");
    expect(payload).not.toHaveProperty("partner_group_name");
  });
});
