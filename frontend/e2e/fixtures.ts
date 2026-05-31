import type {
  AuthUser,
  ContractDocumentsPayload,
  ClientPortalContract,
  ClientPortalDocuments,
  ClientPortalNotification,
  ClientPortalProfile,
  PaginatedResponse,
  ProductionPayload,
  QuoteSummary,
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
  count: 1,
  next: null,
  previous: null,
  results: [
    {
      id: 55,
      reference: "QUOTE-E2E-00055",
      client_display_name: "Moussa Diop",
      vehicle_registration_number: "DK-1234-AA",
      product_type: "TRAILER",
      status: "DRAFT",
      total_amount: "25000.00",
    },
  ],
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
  ready: true,
  operation: "diotali_issue_readiness",
  product_type: "AUTO",
  ass_method: "request_qrcode",
  ass_endpoint: "/api/v1/partner/qrcode.request",
  checks: [
    {
      code: "payment_status",
      passed: true,
      success: "Le paiement est confirme.",
      failure: "Le paiement doit etre confirme.",
    },
  ],
  expected_documents: [],
  trailer_documents: {
    applies: false,
    requires_four_documents: false,
    reference_vehicle: "",
    reference_vehicle_contract_id: null,
    reference_vehicle_contract: null,
    complete: false,
  },
  public_vehicle_verification: {
    status: "not_run",
    endpoint: "diotali-verification",
    required_for_issue: true,
  },
  expected_response_fields: {},
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

export const quoteSummary: QuoteSummary = {
  id: 55,
  reference: "QUOTE-E2E-00055",
  status: "DRAFT",
  client: {
    id: 7,
    display_name: "Moussa Diop",
    phone: "771234567",
  },
  vehicle: {
    id: 12,
    registration_number: "DK-1234-AA",
    brand: "Toyota",
    model: "Corolla",
  },
  references: {
    brand: { id: 1, code: "TOYOTA", ass_code: "TOYOTA", label: "Toyota", source: "reference" },
    genre: { id: 2, code: "REMORQUE", ass_code: "REMORQUE", label: "Remorque", source: "reference" },
    energy: { id: 3, code: "ESSENCE", ass_code: "ESSENCE", label: "Essence", source: "reference" },
    product: { id: 4, code: "TRAILER", ass_code: "TRAILER", label: "Remorque", source: "reference" },
    duration: {
      id: 5,
      code: "D12",
      ass_code: "D12",
      label: "12 mois",
      duration: 12,
      periodicity: "MOIS",
      source: "reference",
    },
  },
  validity: {
    effective_date: "2026-05-29",
    expiration_date: "2026-11-28",
    expiration_source: "stored",
    duration: 12,
    periodicity: "MOIS",
  },
  guarantees: {
    mandatory: [
      {
        id: 1,
        code: "RC",
        ass_code: "RC",
        ass_id: 1,
        label: "Responsabilite civile",
        is_mandatory: true,
        is_default_selected: true,
        is_readonly: true,
        selected: true,
        payload_value: 1,
      },
      {
        id: 2,
        code: "CEDEAO",
        ass_code: "CEDEAO",
        ass_id: 2,
        label: "Carte brune CEDEAO",
        is_mandatory: true,
        is_default_selected: true,
        is_readonly: true,
        selected: true,
        payload_value: 2,
      },
    ],
    optional: [],
    selected_coverage_options: [],
  },
  amounts: {
    civil_liability_amount: "20000.00",
    premium_amount: "22000.00",
    fees_amount: "3000.00",
    contributor_commission_amount: "1000.00",
    group_commission_amount: "0.00",
    commission_total_amount: "1000.00",
    net_to_pay_after_commission: "24000.00",
    total_to_pay: "25000.00",
  },
  commission: {},
  payment: {
    exists: false,
    status: "",
    amount: "0.00",
  },
  trailer_rule: {
    visible: true,
    source: "form_rule",
    genre_requires_trailer_section: true,
    matched_rules: [],
  },
  expected_documents: [
    {
      code: "TRACTOR_ATTESTATION",
      label: "Attestation vehicule tracteur",
      vehicle_role: "tractor",
      document_kind: "attestation",
      required_after_issue: true,
      expected_after_issue: true,
      available: true,
      contract_id: 42,
      contract_number: "HRS-2026-00042",
      attestation_reference: "SN004E2E",
    },
    {
      code: "TRAILER_ATTESTATION",
      label: "Attestation remorque",
      vehicle_role: "trailer",
      document_kind: "attestation",
      required_after_issue: true,
      expected_after_issue: true,
      available: false,
      contract_id: null,
      contract_number: "",
      attestation_reference: "",
    },
  ],
  can_issue: {
    allowed: false,
    reasons: ["Aucun paiement n'est rattache au devis."],
    requires_contract_creation: true,
    contract_id: null,
    contract_status: "",
  },
};

export const contractDocuments: ContractDocumentsPayload = {
  id: 42,
  status: "READY_TO_ISSUE",
  contract_number: "HRS-2026-00042",
  attestation_reference: "",
  qr_code_reference: "",
  attestation_url: "",
  carte_brune_url: "",
  documents: [
    {
      code: "ATTESTATION",
      label: "Attestation",
      vehicle_role: "insured_vehicle",
      document_kind: "attestation",
      required_after_issue: true,
      available: false,
      contract_id: 42,
      contract_number: "HRS-2026-00042",
      attestation_reference: "",
    },
    {
      code: "CARTE_BRUNE",
      label: "Carte brune CEDEAO",
      vehicle_role: "insured_vehicle",
      document_kind: "carte_brune",
      required_after_issue: true,
      available: false,
      contract_id: 42,
      contract_number: "HRS-2026-00042",
      attestation_reference: "",
    },
  ],
  trailer_documents: {
    applies: false,
    requires_four_documents: false,
    reference_vehicle: "",
    reference_vehicle_contract_id: null,
    reference_vehicle_contract: null,
    complete: false,
  },
  issued_at: null,
};

export const productionPayload: ProductionPayload = {
  scope: "platform",
  filters: {},
  summary: {
    total_items: 2,
    total_contracts: 1,
    total_quotes_without_contract: 0,
    total_payments_without_contract: 1,
    issued_contracts: 1,
    pending_contracts: 0,
    failed_contracts: 0,
    paid_payments: 2,
    pending_payments: 0,
    failed_payments: 0,
    total_amount: "33000.00",
    total_paid_amount: "33000.00",
    total_commission_amount: "1000.00",
    contracts_with_trailer: 1,
    items_with_trailer: 1,
    documents_available_count: 2,
  },
  breakdowns: {
    daily: [{ date: "2026-05-29", total_items: 2 } as ProductionPayload["breakdowns"]["daily"][number]],
    monthly: [
      { month: "2026-05", total_items: 2, total_amount: "33000.00" } as ProductionPayload["breakdowns"]["monthly"][number],
    ],
    by_group: [
      { id: 3, name: "Groupe Dakar", total_items: 2 } as ProductionPayload["breakdowns"]["by_group"][number],
    ],
    by_contributor: [
      {
        id: 9,
        username: "apporteur",
        display_name: "Apporteur Dakar",
        total_items: 2,
      } as ProductionPayload["breakdowns"]["by_contributor"][number],
    ],
  },
  count: 2,
  pagination: {
    page: 1,
    page_size: 20,
    total_count: 2,
    total_pages: 1,
    has_next: false,
    has_previous: false,
    export: false,
    max_export_rows: 5000,
    truncated: false,
  },
  results: [
    {
      id: 42,
      entry_id: "contract-42",
      entry_type: "CONTRACT",
      contract_id: 42,
      quote_id: 55,
      payment_id: 66,
      contract_reference: "HRS-2026-00042",
      client: "Moussa Diop",
      client_phone: "771234567",
      vehicle: "Toyota Corolla",
      registration_number: "DK-1234-AA",
      product: "TRAILER",
      contract_status: "ISSUED",
      payment_status: "CONFIRMED",
      amount: "25000.00",
      commission: "1000.00",
      commission_status: "PENDING",
      contributor: { id: 9, username: "apporteur", display_name: "Apporteur Dakar" },
      group: { id: 3, name: "Groupe Dakar", slug: "dakar" },
      created_at: "2026-05-29T10:00:00Z",
      effective_date: "2026-05-29",
      expiration_date: "2026-11-28",
      attestation_available: true,
      carte_brune_available: true,
      has_trailer: true,
      documents_available_count: 2,
    },
    {
      id: null,
      entry_id: "payment-77",
      entry_type: "PAYMENT",
      contract_id: null,
      quote_id: 56,
      payment_id: 77,
      contract_reference: "",
      client: "Awa Fall",
      client_phone: "771234568",
      vehicle: "Nissan Qashqai",
      registration_number: "DK-5678-BB",
      product: "AUTO",
      contract_status: "NO_CONTRACT",
      payment_status: "CONFIRMED",
      amount: "8000.00",
      commission: "0.00",
      commission_status: "",
      contributor: { id: 9, username: "apporteur", display_name: "Apporteur Dakar" },
      group: { id: 3, name: "Groupe Dakar", slug: "dakar" },
      created_at: "2026-05-29T11:00:00Z",
      effective_date: "2026-05-29",
      expiration_date: "2026-11-28",
      attestation_available: false,
      carte_brune_available: false,
      has_trailer: false,
      documents_available_count: 0,
    },
  ],
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
