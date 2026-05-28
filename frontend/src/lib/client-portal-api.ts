import { request } from "@/lib/api";
import type {
  ClientDocumentKind,
  ClientPortalContract,
  ClientPortalDocuments,
  ClientPortalDownloadResponse,
  ClientPortalNotification,
  ClientPortalOtpResponse,
  ClientPortalProfile,
  DeliveryChannel,
} from "@/types/api";

const CLIENT_SESSION_BASE_URL = "/api/client-session";
const CLIENT_SPACE_BASE_URL = "/api/client-space";

const DOCUMENT_ENDPOINTS: Record<ClientDocumentKind, string> = {
  attestation: "attestation",
  carte_brune: "carte-brune",
};

export function clientDocumentPath(contractId: number, documentKind: ClientDocumentKind) {
  return `/contracts/${contractId}/documents/${DOCUMENT_ENDPOINTS[documentKind]}/`;
}

export async function loginClientPortal(token: string): Promise<ClientPortalProfile> {
  return request<ClientPortalProfile>("/login", {
    method: "POST",
    body: JSON.stringify({ token }),
    proxyBaseUrl: CLIENT_SESSION_BASE_URL,
  });
}

export async function logoutClientPortal() {
  await request<unknown>("/logout", {
    method: "POST",
    proxyBaseUrl: CLIENT_SESSION_BASE_URL,
  });
}

export async function fetchClientPortalProfile(): Promise<ClientPortalProfile> {
  return request<ClientPortalProfile>("/me/", { proxyBaseUrl: CLIENT_SPACE_BASE_URL });
}

export async function fetchClientPortalContracts(): Promise<ClientPortalContract[]> {
  return request<ClientPortalContract[]>("/contracts/", {
    proxyBaseUrl: CLIENT_SPACE_BASE_URL,
  });
}

export async function fetchClientPortalDocuments(
  contractId: number,
): Promise<ClientPortalDocuments> {
  return request<ClientPortalDocuments>(`/contracts/${contractId}/documents/`, {
    proxyBaseUrl: CLIENT_SPACE_BASE_URL,
  });
}

export async function fetchClientPortalNotifications(): Promise<ClientPortalNotification[]> {
  return request<ClientPortalNotification[]>("/notifications/", {
    proxyBaseUrl: CLIENT_SPACE_BASE_URL,
  });
}

export async function requestClientDocumentOtp(
  contractId: number,
  documentKind: ClientDocumentKind,
  deliveryChannel: DeliveryChannel = "MANUAL",
): Promise<ClientPortalOtpResponse> {
  return request<ClientPortalOtpResponse>(`/contracts/${contractId}/documents/otp/`, {
    method: "POST",
    body: JSON.stringify({
      document_kind: documentKind,
      delivery_channel: deliveryChannel,
    }),
    proxyBaseUrl: CLIENT_SPACE_BASE_URL,
  });
}

export async function downloadClientDocument(
  contractId: number,
  documentKind: ClientDocumentKind,
  otp: string,
): Promise<ClientPortalDownloadResponse> {
  return request<ClientPortalDownloadResponse>(clientDocumentPath(contractId, documentKind), {
    headers: {
      "X-Client-OTP": otp,
    },
    proxyBaseUrl: CLIENT_SPACE_BASE_URL,
  });
}
