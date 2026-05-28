import { expect, test } from "@playwright/test";

import { mockInternalApp } from "./mocks";

test("guides quote creation with business sections and ASS product fields", async ({ page }) => {
  const mocks = await mockInternalApp(page);

  await page.goto("/resources/quotes");

  await expect(page.getByRole("heading", { name: "Devis" })).toBeVisible();
  await page.getByRole("button", { name: "Nouveau" }).click();

  const panel = page.locator("aside[aria-label='Nouveau devis']");
  await expect(panel.getByText("Rattachement")).toBeVisible();
  await expect(panel.getByText("Produit ASS", { exact: true })).toBeVisible();

  await panel.getByLabel("Client").selectOption("7");
  await panel.getByLabel("Vehicule").selectOption("12");
  await panel.getByLabel("Produit").selectOption("MOTO");

  await expect(panel.locator(".product-pill")).toHaveText("MOTO");
  await panel.getByLabel("Cylindre").fill("126");
  await panel.getByLabel("Usage").fill("NON_COMMERCIAL");
  await panel.getByRole("button", { name: "Garantie 1" }).click();
  await panel.getByRole("button", { name: "Enregistrer" }).click();

  await expect(page.getByText("devis cree.")).toBeVisible();
  expect(mocks.quoteCreateRequests).toEqual([
    expect.objectContaining({
      client: 7,
      vehicle: 12,
      product_type: "MOTO",
      coverage_options: [1],
      ass_product_data: {
        cylindre: 126,
        usage: "NON_COMMERCIAL",
      },
    }),
  ]);
});
