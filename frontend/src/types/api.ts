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
