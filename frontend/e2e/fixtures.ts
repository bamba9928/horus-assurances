import type {
  AuthUser,
  ClientPortalContract,
  ClientPortalDocuments,
  ClientPortalNotification,
  ClientPortalProfile,
  PaginatedResponse,
} from "../src/types/api";

export const adminUser: AuthUser = {
  id: 1,
  username: "admin",
  email: "admin@horus.test",
  first_name: "Awa",
  last_name: "Ndiaye",
  role: "GENERAL_ADMIN",
  partner_group: null,
  partner_group_name: null,
  phone: "770000000",
  is_active: true,
};

export const contractReady = {
  id: 42,
  contract_number: "HRS-2026-00042",
  quote_reference: "11111111-1111-4111-8111-111111111111",
  client_display_name: "Moussa Diop",
  vehicle_registration_number: "DK-1234-AA",
  status: "READY_TO_ISSUE",
  attestation_reference: "",
  qr_code_reference: "",
  issued_at: null,
  created_at: "2026-05-25T10:00:00Z",
  updated_at: "2026-05-25T10:00:00Z",
};

export const contractIssued = {
  ...contractReady,
  status: "ISSUED",
  attestation_reference: "SN004E2E",
  qr_code_reference: "QR-E2E-00042",
  issued_at: "2026-05-25T10:05:00Z",
  updated_at: "2026-05-25T10:05:00Z",
};

export const contractsPage: PaginatedResponse<typeof contractReady> = {
  count: 1,
  next: null,
  previous: null,
  results: [contractReady],
};

export const quotesPage: PaginatedResponse<Record<string, unknown>> = {
  count: 0,
  next: null,
  previous: null,
  results: [],
};

export const groupsPage: PaginatedResponse<Record<string, unknown>> = {
  count: 1,
  next: null,
  previous: null,
  results: [{ id: 3, name: "Groupe Dakar", slug: "dakar" }],
};

export const clientsPage: PaginatedResponse<Record<string, unknown>> = {
  count: 1,
  next: null,
  previous: null,
  results: [{ id: 7, display_name: "Moussa Diop", phone: "771234567" }],
};

export const vehiclesPage: PaginatedResponse<Record<string, unknown>> = {
  count: 1,
  next: null,
  previous: null,
  results: [
    {
      id: 12,
      registration_number: "DK-1234-AA",
      brand: "Toyota",
      model: "Corolla",
    },
  ],
};

export const contributorsPage: PaginatedResponse<Record<string, unknown>> = {
  count: 1,
  next: null,
  previous: null,
  results: [{ id: 9, username: "apporteur", email: "apporteur@horus.test" }],
};

export const createdMotoQuote = {
  id: 88,
  reference: "22222222-2222-4222-8222-222222222222",
  client_display_name: "Moussa Diop",
  vehicle_registration_number: "DK-1234-AA",
  product_type: "MOTO",
  status: "DRAFT",
  total_amount: "0.00",
};

export const contractIssuePreview = {
  preview_only: true,
  operation: "qrcode_issue",
  product_type: "AUTO",
  ass_method: "request_qrcode",
  ass_endpoint: "/api/v1/partner/qrcode.request",
  payload: {
    assure: {
      nom: "Diop",
      prenom: "Moussa",
    },
    vehicule: {
      immatriculation: "DK-1234-AA",
      marque: "Toyota",
      modele: "Corolla",
    },
    referenceTrxPartner: "PAY-E2E-00042",
    responsabiliteCivile: 25000,
  },
};

export const clientProfile: ClientPortalProfile = {
  id: 7,
  display_name: "Moussa Diop",
  client_type: "INDIVIDUAL",
  first_name: "Moussa",
  last_name: "Diop",
  company_name: "",
  email: "moussa@example.test",
  phone: "771234567",
  address: "Dakar",
  partner_group_name: "Groupe Dakar",
};

export const clientContract: ClientPortalContract = {
  id: 42,
  status: "ISSUED",
  contract_number: "HRS-2026-00042",
  attestation_reference: "SN004E2E",
  qr_code_reference: "QR-E2E-00042",
  attestation_available: true,
  carte_brune_available: true,
  issued_at: "2026-05-25T10:05:00Z",
  created_at: "2026-05-25T10:00:00Z",
  vehicle_registration_number: "DK-1234-AA",
  vehicle_brand: "Toyota",
  vehicle_model: "Corolla",
  product_type: "AUTO",
  total_amount: "25000.00",
};

export const clientDocuments: ClientPortalDocuments = {
  id: 42,
  status: "ISSUED",
  contract_number: "HRS-2026-00042",
  attestation_reference: "SN004E2E",
  qr_code_reference: "QR-E2E-00042",
  attestation_available: true,
  carte_brune_available: true,
  otp_required: true,
  issued_at: "2026-05-25T10:05:00Z",
};

export const clientNotifications: ClientPortalNotification[] = [
  {
    id: 11,
    notification_type: "CONTRACT_ISSUED",
    title: "Contrat emis",
    message: "Votre contrat HRS-2026-00042 est disponible.",
    target_type: "contracts.contract",
    target_id: "42",
    metadata: { contract_id: 42 },
    is_read: false,
    read_at: null,
    created_at: "2026-05-25T10:06:00Z",
  },
];
