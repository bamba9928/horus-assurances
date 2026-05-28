export type UserRole = "GENERAL_ADMIN" | "GROUP_ADMIN" | "CONTRIBUTOR";

export type AuthUser = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  partner_group: number | null;
  partner_group_name: string | null;
  phone: string;
  is_active: boolean;
};

export type TokenPair = {
  access: string;
  refresh: string;
};

export type DashboardCounts = {
  groups: number;
  users: number;
  contributors: number;
  clients: number;
  vehicles: number;
  quotes: number;
  payments: number;
  confirmed_payments: number;
  contracts: number;
  issued_contracts: number;
  commissions: number;
  wallets: number;
  audit_logs: number;
  unread_notifications: number;
};

export type DashboardPayload = {
  scope: "platform" | "group" | "contributor" | "none";
  counts: DashboardCounts;
};

export type ApiRecord = Record<string, unknown> & {
  id?: number | string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type ApiErrorPayload = {
  detail?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
};

export type DeliveryChannel = "SMS" | "EMAIL" | "MANUAL";

export type ClientDocumentKind = "attestation" | "carte_brune";

export type ClientPortalProfile = {
  id: number;
  display_name: string;
  client_type: string;
  first_name: string;
  last_name: string;
  company_name: string;
  email: string;
  phone: string;
  address: string;
  partner_group_name: string;
};

export type ClientPortalContract = {
  id: number;
  status: string;
  contract_number: string;
  attestation_reference: string | null;
  qr_code_reference: string;
  attestation_available: boolean;
  carte_brune_available: boolean;
  issued_at: string | null;
  created_at: string;
  vehicle_registration_number: string;
  vehicle_brand: string;
  vehicle_model: string;
  product_type: string;
  total_amount: string;
};

export type ClientPortalDocuments = {
  id: number;
  status: string;
  contract_number: string;
  attestation_reference: string | null;
  qr_code_reference: string;
  attestation_available: boolean;
  carte_brune_available: boolean;
  otp_required: boolean;
  issued_at: string | null;
};

export type ClientPortalNotification = {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  target_type: string;
  target_id: string;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type ClientPortalOtpResponse = {
  otp: string | null;
  document_kind: ClientDocumentKind;
  mock_delivery: boolean;
  provider: string;
  delivery_channel: DeliveryChannel;
  destination: string;
  secret_returned: boolean;
  expires_at: string;
};

export type ClientPortalDownloadResponse = {
  download_url: string;
};
