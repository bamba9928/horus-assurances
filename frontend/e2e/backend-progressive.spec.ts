import { expect, test } from "@playwright/test";

import { mockInternalApp } from "./mocks";

test("shows quote summary with mandatory guarantees and trailer documents", async ({ page }) => {
  await mockInternalApp(page);

  await page.goto("/resources/quotes");
  await page.getByRole("button", { name: "Details" }).click();

  const panel = page.locator("aside[aria-label='Details']");
  await expect(panel.getByText("Resume proposition")).toBeVisible();
  await expect(panel.getByText("Responsabilite civile readonly")).toBeVisible();
  await expect(panel.getByText("Carte brune CEDEAO readonly")).toBeVisible();
  await expect(panel.getByText("Attestation vehicule tracteur")).toBeVisible();
  await expect(panel.getByText("Remorque: section visible")).toBeVisible();
});

test("shows contract readiness, documents and explicit Diotali verification", async ({ page }) => {
  await mockInternalApp(page);

  await page.goto("/resources/contracts");
  await page.getByRole("button", { name: "Details" }).click();

  const panel = page.locator("aside[aria-label='Details']");
  await expect(panel.getByText("Controles Diotali")).toBeVisible();
  await expect(panel.getByText("Le paiement est confirme.")).toBeVisible();
  await expect(panel.getByText("Documents contrat")).toBeVisible();

  await panel.getByRole("button", { name: "Verifier Diotali" }).click();
  await expect(panel.getByText("Diotali NOT_FOUND")).toBeVisible();
});

test("shows production filters, totals and rows", async ({ page }) => {
  await mockInternalApp(page);

  await page.goto("/production");

  await expect(page.getByRole("heading", { name: "Production" })).toBeVisible();
  await expect(page.getByText("Contrats emis")).toBeVisible();
  await expect(page.getByText("HRS-2026-00042")).toBeVisible();
  await expect(page.getByText("Awa Fall")).toBeVisible();

  await page.getByLabel("Remorque").selectOption("true");
  await page.getByRole("button", { name: "Filtrer" }).click();
  await expect(page.getByText("remorque=true")).toBeVisible();
});
