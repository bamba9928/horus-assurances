import { expect, test } from "@playwright/test";

import { mockInternalApp } from "./mocks";

test("requires preview and typed confirmation before ASS QR issue", async ({ page }) => {
  const mocks = await mockInternalApp(page);

  await page.goto("/resources/contracts");

  await expect(page.getByRole("heading", { name: "Contrats" })).toBeVisible();
  await page.getByRole("button", { name: "Emettre QR" }).click();

  const dialog = page.getByRole("dialog", { name: "Emission ASS/QR" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("/api/v1/partner/qrcode.request")).toBeVisible();

  const confirmButton = dialog.getByRole("button", { name: "Confirmer l'action" });
  await expect(confirmButton).toBeDisabled();
  await dialog.getByLabel("Confirmation requise: saisir EMETTRE").fill("CONFIRMER");
  await expect(confirmButton).toBeDisabled();
  await dialog.getByLabel("Confirmation requise: saisir EMETTRE").fill("EMETTRE");
  await expect(confirmButton).toBeEnabled();

  await confirmButton.click();

  expect(mocks.issueRequests).toHaveLength(1);
  await expect(page.getByText("Emettre QR effectue.")).toBeVisible();
  await expect(page.getByText("SN004E2E")).toBeVisible();
});
