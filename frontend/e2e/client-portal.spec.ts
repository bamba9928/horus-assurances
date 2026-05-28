import { expect, test } from "@playwright/test";

import { mockClientPortal } from "./mocks";

test("lets a client request OTP and open an available document", async ({ page }) => {
  await page.addInitScript(() => {
    window.open = (url) => {
      (window as Window & { __openedUrl?: string }).__openedUrl = String(url);
      return null;
    };
  });
  const mocks = await mockClientPortal(page);

  await page.goto("/client");

  await expect(page.getByRole("heading", { name: "Espace client" })).toBeVisible();
  await page.getByLabel("Jeton d'acces").fill("client-e2e-token");
  await page.getByRole("button", { name: "Ouvrir" }).click();

  await expect(page.getByRole("heading", { name: "Moussa Diop" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "HRS-2026-00042" })).toBeVisible();

  const attestation = page.locator(".document-action").filter({ hasText: "Attestation" });
  await attestation.getByRole("button", { name: "OTP" }).click();

  await expect(page.getByText("OTP mock genere pour le developpement.")).toBeVisible();
  await expect(attestation.getByLabel("OTP Attestation")).toHaveValue("123456");

  await attestation.getByRole("button", { name: "Ouvrir" }).click();

  await expect(page.getByText("Document autorise.")).toBeVisible();
  await expect
    .poll(() => page.evaluate(() => (window as Window & { __openedUrl?: string }).__openedUrl))
    .toBe("https://documents.example.test/attestation.pdf");
  expect(mocks.downloadOtpValues).toEqual(["123456"]);
});
