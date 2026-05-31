import type {
  ApiErrorPayload,
  AuthUser,
  ContractDocumentsPayload,
  DiotaliVerificationPayload,
  DashboardPayload,
  IssueReadinessPayload,
  PaginatedResponse,
  ProductionPayload,
  QuoteSummary,
} from "@/types/api";

const API_PROXY_BASE_URL = "/api/backend";

type RequestOptions = RequestInit & {
  proxyBaseUrl?: string;
};

export class ApiError extends Error {
  status: number;
  payload: ApiErrorPayload | string | null;

  constructor(message: string, status: number, payload: ApiErrorPayload | string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function getApiBaseUrl() {
  return "Proxy Next.js HttpOnly";
}

export async function login(username: string, password: string): Promise<AuthUser> {
  return request<AuthUser>("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    proxyBaseUrl: "/api/auth",
  });
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>("/me", { proxyBaseUrl: "/api/auth" });
}

export async function logout() {
  await request<unknown>("/logout", {
    method: "POST",
    proxyBaseUrl: "/api/auth",
  });
}

export async function fetchDashboard(): Promise<DashboardPayload> {
  return request<DashboardPayload>("/dashboard/");
}

export async function fetchProduction(params: URLSearchParams): Promise<ProductionPayload> {
  const query = params.toString();
  return request<ProductionPayload>(`/production/${query ? `?${query}` : ""}`);
}

export async function fetchQuoteSummary(id: number | string): Promise<QuoteSummary> {
  return request<QuoteSummary>(`/quotes/${id}/summary/`);
}

export async function fetchContractDocuments(
  id: number | string,
): Promise<ContractDocumentsPayload> {
  return request<ContractDocumentsPayload>(`/contracts/${id}/documents/`);
}

export async function fetchContractIssueReadiness(
  id: number | string,
): Promise<IssueReadinessPayload> {
  return request<IssueReadinessPayload>(`/contracts/${id}/issue-readiness/`);
}

export async function fetchContractDiotaliVerification(
  id: number | string,
): Promise<DiotaliVerificationPayload> {
  return request<DiotaliVerificationPayload>(`/contracts/${id}/diotali-verification/`);
}

export async function listResource<T>(
  endpoint: string,
  params: URLSearchParams,
): Promise<PaginatedResponse<T>> {
  const query = params.toString();
  return request<PaginatedResponse<T>>(`${endpoint}/${query ? `?${query}` : ""}`);
}

export async function createResource<T>(
  endpoint: string,
  payload: Record<string, unknown>,
): Promise<T> {
  return request<T>(`${endpoint}/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateResource<T>(
  endpoint: string,
  id: number | string,
  payload: Record<string, unknown>,
): Promise<T> {
  return request<T>(`${endpoint}/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteResource(endpoint: string, id: number | string) {
  await request<unknown>(`${endpoint}/${id}/`, {
    method: "DELETE",
  });
}

export async function runResourceAction<T>(
  endpoint: string,
  id: number | string,
  action: string,
  payload?: Record<string, unknown>,
): Promise<T> {
  return request<T>(`${endpoint}/${id}/${action}/`, {
    method: "POST",
    body: payload ? JSON.stringify(payload) : JSON.stringify({}),
  });
}

export async function fetchResourceAction<T>(
  endpoint: string,
  id: number | string,
  action: string,
): Promise<T> {
  return request<T>(`${endpoint}/${id}/${action}/`);
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { proxyBaseUrl = API_PROXY_BASE_URL, ...fetchOptions } = options;
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${proxyBaseUrl}${path}`, {
    ...fetchOptions,
    credentials: "same-origin",
    headers,
  });

  if (!response.ok) {
    const payload = await readErrorPayload(response);
    throw new ApiError(errorMessage(payload, response.status), response.status, payload);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function readErrorPayload(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as ApiErrorPayload;
  } catch {
    return text;
  }
}

export function errorMessage(payload: ApiErrorPayload | string | null, status: number) {
  if (typeof payload === "string") {
    return payload;
  }
  if (payload?.detail) {
    return payload.detail;
  }
  if (payload?.non_field_errors?.length) {
    return payload.non_field_errors.join(" ");
  }
  const diotaliPublic = payload?.diotali_public;
  if (isRecord(diotaliPublic)) {
    const message =
      stringValue(diotaliPublic.correction_message) ||
      stringValue(diotaliPublic.message) ||
      stringValue(diotaliPublic.operationMessage);
    if (message) {
      return message;
    }
  }
  const issueReadiness = payload?.issue_readiness;
  if (Array.isArray(issueReadiness) && issueReadiness.length) {
    const messages = issueReadiness
      .map((item) => (isRecord(item) ? stringValue(item.failure) : ""))
      .filter(Boolean);
    if (messages.length) {
      return messages.join(" ");
    }
  }
  return `Erreur API ${status}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}
