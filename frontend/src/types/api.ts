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

export type ReferenceSummary = {
  id: number | null;
  code: string | null;
  ass_code: string;
  label: string;
  value?: string;
  source?: string;
  duration?: number;
  periodicity?: string;
  requires_trailer_section?: boolean;
};

export type GuaranteeSummary = {
  id: number;
  code: string;
  ass_code: string;
  ass_id: number | null;
  label: string;
  is_mandatory: boolean;
  is_default_selected: boolean;
  is_readonly: boolean;
  selected: boolean;
  payload_value: string | number;
};

export type ContractDocumentItem = {
  code: string;
  label: string;
  vehicle_role: string;
  document_kind: string;
  required_after_issue: boolean;
  expected_after_issue?: boolean;
  available: boolean;
  contract_id: number | null;
  contract_number: string;
  attestation_reference: string;
  url?: string;
};

export type TrailerDocumentsSummary = {
  applies: boolean;
  requires_four_documents: boolean;
  reference_vehicle: string;
  reference_vehicle_contract_id: number | null;
  reference_vehicle_contract: ApiRecord | null;
  complete: boolean;
};

export type QuoteSummary = {
  id: number;
  reference: string;
  status: string;
  client: ApiRecord;
  vehicle: ApiRecord;
  references: {
    brand: ReferenceSummary;
    genre: ReferenceSummary;
    energy: ReferenceSummary;
    product: ReferenceSummary;
    duration: ReferenceSummary;
  };
  validity: {
    effective_date: string | null;
    expiration_date: string | null;
    expiration_source: string;
    duration: number;
    periodicity: string;
  };
  guarantees: {
    mandatory: GuaranteeSummary[];
    optional: GuaranteeSummary[];
    selected_coverage_options: unknown[];
  };
  amounts: Record<string, string>;
  commission: ApiRecord;
  payment: ApiRecord & {
    exists: boolean;
    status: string;
    amount: string;
  };
  trailer_rule: {
    visible: boolean;
    source: string;
    genre_requires_trailer_section: boolean;
    matched_rules: ApiRecord[];
  };
  expected_documents: ContractDocumentItem[];
  can_issue: {
    allowed: boolean;
    reasons: string[];
    requires_contract_creation: boolean;
    contract_id: number | null;
    contract_status: string;
  };
};

export type ContractDocumentsPayload = {
  id: number;
  status: string;
  contract_number: string;
  attestation_reference: string | null;
  qr_code_reference: string;
  attestation_url: string;
  carte_brune_url: string;
  documents: ContractDocumentItem[];
  trailer_documents: TrailerDocumentsSummary;
  issued_at: string | null;
};

export type IssueReadinessPayload = {
  ready: boolean;
  operation: string;
  product_type: string;
  ass_method: string;
  ass_endpoint: string;
  checks: Array<{
    code: string;
    passed: boolean;
    success: string;
    failure: string;
    detail?: unknown;
  }>;
  payload: ApiRecord | null;
  expected_response_fields: ApiRecord;
  expected_documents: ContractDocumentItem[];
  trailer_documents: TrailerDocumentsSummary;
  public_vehicle_verification: ApiRecord;
};

export type DiotaliVerificationPayload = {
  operation: string;
  registration_number: string;
  normalized_registration_number: string;
  public_endpoints: ApiRecord[];
  verification: ApiRecord & {
    is_valid?: boolean;
    status?: string;
    blocks_issue?: boolean;
    message?: string;
    attestation_number?: string;
    expiration_date?: string;
    suggested_effective_date?: string;
    correction_message?: string;
  };
  result: ApiRecord;
};

export type ProductionUserSummary = {
  id: number | null;
  username: string;
  display_name: string;
};

export type ProductionGroupSummary = {
  id: number;
  name: string;
  slug: string;
};

export type ProductionRow = {
  id: number | null;
  entry_id: string;
  entry_type: "CONTRACT" | "QUOTE" | "PAYMENT";
  contract_id: number | null;
  quote_id: number;
  payment_id: number | null;
  contract_reference: string;
  client: string;
  client_phone: string;
  vehicle: string;
  registration_number: string;
  product: string;
  contract_status: string;
  payment_status: string;
  amount: string;
  commission: string;
  commission_status: string;
  contributor: ProductionUserSummary;
  group: ProductionGroupSummary;
  created_at: string;
  effective_date: string | null;
  expiration_date: string | null;
  attestation_available: boolean;
  carte_brune_available: boolean;
  has_trailer: boolean;
  documents_available_count: number;
};

export type ProductionSummary = {
  total_items: number;
  total_contracts: number;
  total_quotes_without_contract: number;
  total_payments_without_contract: number;
  issued_contracts: number;
  pending_contracts: number;
  failed_contracts: number;
  paid_payments: number;
  pending_payments: number;
  failed_payments: number;
  total_amount: string;
  total_paid_amount: string;
  total_commission_amount: string;
  contracts_with_trailer: number;
  items_with_trailer: number;
  documents_available_count: number;
};

export type ProductionPayload = {
  scope: string;
  filters: Record<string, unknown>;
  summary: ProductionSummary;
  breakdowns: {
    daily: Array<ProductionSummary & { date: string }>;
    monthly: Array<ProductionSummary & { month: string }>;
    by_group: Array<ProductionSummary & { id: number; name: string }>;
    by_contributor: Array<ProductionSummary & ProductionUserSummary>;
  };
  count: number;
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
    export: boolean;
    max_export_rows: number;
    truncated: boolean;
  };
  results: ProductionRow[];
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
