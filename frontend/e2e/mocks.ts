import type { Page, Route } from "@playwright/test";

import {
  adminUser,
  clientsPage,
  contributorsPage,
  clientContract,
  clientDocuments,
  clientNotifications,
  clientProfile,
  contractIssuePreview,
  contractIssued,
  contractsPage,
  createdMotoQuote,
  groupsPage,
  quotesPage,
  vehiclesPage,
} from "./fixtures";

type InternalAppMocks = {
  issueRequests: string[];
  quoteCreateRequests: unknown[];
};

type ClientPortalMocks = {
  downloadOtpValues: string[];
};

export async function mockInternalApp(page: Page): Promise<InternalAppMocks> {
  const issueRequests: string[] = [];
  const quoteCreateRequests: unknown[] = [];

  await page.route("**/api/auth/me", (route) => json(route, adminUser));
  await page.route("**/api/auth/logout", (route) => json(route, {}));
  await page.route("**/api/backend/**", async (route) => {
    const url = new URL(route.request().url());
    const request = route.request();
    if (request.method() === "GET" && url.pathname === "/api/backend/contracts/") {
      return json(route, contractsPage);
    }
    if (request.method() === "GET" && url.pathname === "/api/backend/quotes/") {
      return json(route, quotesPage);
    }
    if (request.method() === "POST" && url.pathname === "/api/backend/quotes/") {
      quoteCreateRequests.push(JSON.parse(request.postData() ?? "{}"));
      return json(route, createdMotoQuote, 201);
    }
    if (request.method() === "GET" && url.pathname === "/api/backend/groups/") {
      return json(route, groupsPage);
    }
    if (request.method() === "GET" && url.pathname === "/api/backend/clients/") {
      return json(route, clientsPage);
    }
    if (request.method() === "GET" && url.pathname === "/api/backend/vehicles/") {
      return json(route, vehiclesPage);
    }
    if (request.method() === "GET" && url.pathname === "/api/backend/contributors/") {
      return json(route, contributorsPage);
    }
    if (
      request.method() === "POST" &&
      url.pathname === "/api/backend/contracts/42/ass-payload-preview/"
    ) {
      return json(route, contractIssuePreview);
    }
    if (request.method() === "POST" && url.pathname === "/api/backend/contracts/42/issue/") {
      issueRequests.push(request.postData() ?? "");
      return json(route, contractIssued);
    }
    return json(route, { detail: "Route mock introuvable." }, 404);
  });

  return { issueRequests, quoteCreateRequests };
}

export async function mockClientPortal(page: Page): Promise<ClientPortalMocks> {
  let authenticated = false;
  const downloadOtpValues: string[] = [];

  await page.route("**/api/client-session/login", async (route) => {
    if (route.request().method() !== "POST") {
      return route.fallback();
    }
    authenticated = true;
    return json(route, clientProfile);
  });
  await page.route("**/api/client-session/logout", async (route) => {
    authenticated = false;
    return json(route, {});
  });
  await page.route("**/api/client-space/**", async (route) => {
    if (!authenticated) {
      return json(route, { detail: "Session client expiree." }, 401);
    }

    const url = new URL(route.request().url());
    const method = route.request().method();
    if (method === "GET" && url.pathname === "/api/client-space/me/") {
      return json(route, clientProfile);
    }
    if (method === "GET" && url.pathname === "/api/client-space/contracts/") {
      return json(route, [clientContract]);
    }
    if (method === "GET" && url.pathname === "/api/client-space/notifications/") {
      return json(route, clientNotifications);
    }
    if (method === "GET" && url.pathname === "/api/client-space/contracts/42/documents/") {
      return json(route, clientDocuments);
    }
    if (method === "POST" && url.pathname === "/api/client-space/contracts/42/documents/otp/") {
      return json(route, {
        otp: "123456",
        document_kind: "attestation",
        mock_delivery: true,
        provider: "mock",
        delivery_channel: "MANUAL",
        destination: "771234567",
        secret_returned: true,
        expires_at: "2026-05-25T10:15:00Z",
      });
    }
    if (
      method === "GET" &&
      url.pathname === "/api/client-space/contracts/42/documents/attestation/"
    ) {
      downloadOtpValues.push(route.request().headers()["x-client-otp"] ?? "");
      return json(route, {
        download_url: "https://documents.example.test/attestation.pdf",
      });
    }

    return json(route, { detail: "Route mock introuvable." }, 404);
  });

  return { downloadOtpValues };
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    body: JSON.stringify(body),
    contentType: "application/json",
    status,
  });
}
