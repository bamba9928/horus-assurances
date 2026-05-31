import { describe, expect, it } from "vitest";

import {
  buildProductionSearchParams,
  DEFAULT_PRODUCTION_FILTERS,
} from "@/lib/production";

describe("buildProductionSearchParams", () => {
  it("serializes only active production filters", () => {
    const params = buildProductionSearchParams({
      ...DEFAULT_PRODUCTION_FILTERS,
      client: "Awa",
      contract_status: "ISSUED",
      contributor: "apporteur",
      group: "dakar",
      issued: "true",
      page: 2,
      payment_status: "CONFIRMED",
      product: "AUTO",
      registration_number: "DK-1234",
      today: true,
      with_trailer: "false",
    });

    expect(params.toString()).toContain("page=2");
    expect(params.get("today")).toBe("true");
    expect(params.get("client")).toBe("Awa");
    expect(params.get("contributor")).toBe("apporteur");
    expect(params.get("group")).toBe("dakar");
    expect(params.get("contract_status")).toBe("ISSUED");
    expect(params.get("payment_status")).toBe("CONFIRMED");
    expect(params.get("product")).toBe("AUTO");
    expect(params.get("immatriculation")).toBe("DK-1234");
    expect(params.get("issued")).toBe("true");
    expect(params.get("remorque")).toBe("false");
    expect(params.has("date_debut")).toBe(false);
  });
});
