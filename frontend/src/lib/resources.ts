import type { ApiRecord, UserRole } from "@/types/api";

export type FieldKind = "text" | "date" | "money" | "status" | "json";

export type ResourceColumn = {
  key: string;
  label: string;
  kind?: FieldKind;
};

export type SelectOption = {
  label: string;
  value: string | number | boolean;
};

export type RelationConfig = {
  endpoint: string;
  labelKeys: string[];
};

export type ResourceFormField = {
  name: string;
  label: string;
  type:
    | "ass-product-data"
    | "checkbox"
    | "coverage-options"
    | "date"
    | "email"
    | "json"
    | "money"
    | "number"
    | "password"
    | "relation"
    | "select"
    | "tel"
    | "text"
    | "textarea";
  defaultValue?: unknown;
  helper?: string;
  inputMode?: "decimal" | "email" | "numeric" | "tel" | "text";
  layout?: "full";
  max?: number;
  min?: number;
  omitIfBlank?: boolean;
  options?: SelectOption[];
  placeholder?: string;
  relation?: RelationConfig;
  required?: boolean;
  section?: string;
  step?: number | string;
  transform?: "uppercase";
};

export type ResourceAction = {
  label: string;
  action: string;
  confirm?: string;
  guard?: {
    title: string;
    description: string;
    confirmationValue: string;
    preflightAction?: string;
    previewLabel?: string;
    warningItems?: string[];
  };
  disabledWhen?: {
    field: string;
    equals?: unknown;
    notEquals?: unknown;
    reason: string;
  };
};

export type ResourceDefinition = {
  slug: string;
  label: string;
  singular: string;
  endpoint: string;
  icon: string;
  roles: UserRole[];
  canCreate?: boolean;
  canDelete?: boolean;
  canEdit?: boolean;
  columns: ResourceColumn[];
  detailFields?: ResourceColumn[];
  formFields?: ResourceFormField[];
  actions?: ResourceAction[];
};

const GROUP_RELATION = {
  endpoint: "/groups",
  labelKeys: ["name", "slug"],
};

const CONTRIBUTOR_RELATION = {
  endpoint: "/contributors",
  labelKeys: ["username", "email"],
};

const CLIENT_RELATION = {
  endpoint: "/clients",
  labelKeys: ["display_name", "phone"],
};

const VEHICLE_RELATION = {
  endpoint: "/vehicles",
  labelKeys: ["registration_number", "brand", "model"],
};

const QUOTE_RELATION = {
  endpoint: "/quotes",
  labelKeys: ["reference", "client_display_name", "total_amount"],
};

const PAYMENT_RELATION = {
  endpoint: "/payments",
  labelKeys: ["id", "client_display_name", "amount", "status"],
};

const CONTRACT_RELATION = {
  endpoint: "/contracts",
  labelKeys: ["contract_number", "client_display_name", "status"],
};

const groupFields: ResourceFormField[] = [
  {
    name: "name",
    label: "Nom",
    type: "text",
    required: true,
    section: "Identification",
  },
  {
    name: "slug",
    label: "Slug",
    type: "text",
    helper: "Laisser vide pour conserver la generation automatique si elle est active cote backend.",
    omitIfBlank: true,
    section: "Identification",
  },
  {
    name: "status",
    label: "Statut",
    type: "select",
    defaultValue: "ACTIVE",
    required: true,
    section: "Etat",
    options: [
      { label: "Actif", value: "ACTIVE" },
      { label: "Suspendu", value: "SUSPENDED" },
      { label: "Archive", value: "ARCHIVED" },
    ],
  },
];

const userFields: ResourceFormField[] = [
  { name: "username", label: "Identifiant", type: "text", required: true, section: "Compte" },
  { name: "email", label: "Email", type: "email", section: "Compte" },
  { name: "first_name", label: "Prenom", type: "text", section: "Identite" },
  { name: "last_name", label: "Nom", type: "text", section: "Identite" },
  {
    name: "role",
    label: "Role",
    type: "select",
    defaultValue: "CONTRIBUTOR",
    required: true,
    section: "Droits",
    options: [
      { label: "Admin general", value: "GENERAL_ADMIN" },
      { label: "Admin groupe", value: "GROUP_ADMIN" },
      { label: "Apporteur", value: "CONTRIBUTOR" },
    ],
  },
  {
    name: "partner_group",
    label: "Groupe",
    type: "relation",
    relation: GROUP_RELATION,
    omitIfBlank: true,
    section: "Droits",
  },
  { name: "phone", label: "Telephone", type: "tel", inputMode: "tel", section: "Identite" },
  {
    name: "password",
    label: "Mot de passe",
    type: "password",
    omitIfBlank: true,
    section: "Compte",
  },
  { name: "is_active", label: "Actif", type: "checkbox", defaultValue: true, section: "Etat" },
];

const contributorFields: ResourceFormField[] = userFields.filter(
  (field) => field.name !== "role",
);

const clientFields: ResourceFormField[] = [
  {
    name: "partner_group",
    label: "Groupe",
    type: "relation",
    relation: GROUP_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "contributor",
    label: "Apporteur",
    type: "relation",
    relation: CONTRIBUTOR_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "client_type",
    label: "Type client",
    type: "select",
    defaultValue: "INDIVIDUAL",
    required: true,
    section: "Identite",
    options: [
      { label: "Personne physique", value: "INDIVIDUAL" },
      { label: "Personne morale", value: "COMPANY" },
    ],
  },
  { name: "first_name", label: "Prenom", type: "text", section: "Identite" },
  { name: "last_name", label: "Nom", type: "text", section: "Identite" },
  { name: "company_name", label: "Societe", type: "text", section: "Identite" },
  { name: "email", label: "Email", type: "email", section: "Contact" },
  {
    name: "phone",
    label: "Telephone",
    type: "tel",
    inputMode: "tel",
    required: true,
    section: "Contact",
  },
  { name: "address", label: "Adresse", type: "textarea", layout: "full", section: "Contact" },
  { name: "identity_number", label: "Piece identite", type: "text", section: "Identite" },
  { name: "is_active", label: "Actif", type: "checkbox", defaultValue: true, section: "Etat" },
];

const vehicleFields: ResourceFormField[] = [
  {
    name: "partner_group",
    label: "Groupe",
    type: "relation",
    relation: GROUP_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "client",
    label: "Client",
    type: "relation",
    relation: CLIENT_RELATION,
    required: true,
    section: "Rattachement",
  },
  {
    name: "contributor",
    label: "Apporteur",
    type: "relation",
    relation: CONTRIBUTOR_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "registration_number",
    label: "Immatriculation",
    type: "text",
    required: true,
    placeholder: "DK-1234-AA",
    section: "Vehicule",
    transform: "uppercase",
  },
  { name: "brand", label: "Marque", type: "text", required: true, section: "Vehicule" },
  { name: "model", label: "Modele", type: "text", required: true, section: "Vehicule" },
  {
    name: "chassis_number",
    label: "Chassis",
    type: "text",
    section: "Vehicule",
    transform: "uppercase",
  },
  {
    name: "genre",
    label: "Genre ASS",
    type: "text",
    required: true,
    defaultValue: "VP",
    section: "Caracteristiques ASS",
    transform: "uppercase",
  },
  {
    name: "energy",
    label: "Energie",
    type: "select",
    defaultValue: "ESSENCE",
    required: true,
    section: "Caracteristiques ASS",
    options: [
      { label: "Essence", value: "ESSENCE" },
      { label: "Diesel", value: "DIESEL" },
      { label: "Electrique", value: "ELECTRIQUE" },
      { label: "Hybride", value: "HYBRIDE" },
    ],
  },
  {
    name: "fiscal_power",
    label: "Puissance fiscale",
    type: "number",
    inputMode: "numeric",
    min: 0,
    section: "Caracteristiques ASS",
  },
  {
    name: "seats",
    label: "Places",
    type: "number",
    defaultValue: 5,
    inputMode: "numeric",
    min: 1,
    section: "Caracteristiques ASS",
  },
  {
    name: "first_registration_date",
    label: "1ere mise en circulation",
    type: "date",
    section: "Vehicule",
  },
  {
    name: "new_value",
    label: "Valeur neuve",
    type: "money",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Valeurs",
  },
  {
    name: "current_value",
    label: "Valeur actuelle",
    type: "money",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Valeurs",
  },
  { name: "is_active", label: "Actif", type: "checkbox", defaultValue: true, section: "Etat" },
];

const quoteFields: ResourceFormField[] = [
  {
    name: "partner_group",
    label: "Groupe",
    type: "relation",
    relation: GROUP_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "client",
    label: "Client",
    type: "relation",
    relation: CLIENT_RELATION,
    required: true,
    section: "Rattachement",
  },
  {
    name: "vehicle",
    label: "Vehicule",
    type: "relation",
    relation: VEHICLE_RELATION,
    required: true,
    section: "Rattachement",
  },
  {
    name: "contributor",
    label: "Apporteur",
    type: "relation",
    relation: CONTRIBUTOR_RELATION,
    omitIfBlank: true,
    section: "Rattachement",
  },
  {
    name: "product_type",
    label: "Produit",
    type: "select",
    defaultValue: "AUTO",
    required: true,
    section: "Produit",
    options: [
      { label: "Auto", value: "AUTO" },
      { label: "Moto", value: "MOTO" },
      { label: "Flotte", value: "FLEET" },
      { label: "Remorque", value: "TRAILER" },
      { label: "Bus ecole", value: "SCHOOL_BUS" },
      { label: "Garage", value: "GARAGE" },
    ],
  },
  {
    name: "periodicity",
    label: "Periodicite",
    type: "select",
    defaultValue: "MOIS",
    required: true,
    section: "Produit",
    options: [
      { label: "Jours", value: "JOURS" },
      { label: "Mois", value: "MOIS" },
      { label: "Annees", value: "ANNEES" },
    ],
  },
  {
    name: "duration",
    label: "Duree",
    type: "number",
    defaultValue: 12,
    inputMode: "numeric",
    min: 1,
    max: 120,
    required: true,
    section: "Produit",
  },
  { name: "effective_date", label: "Date effet", type: "date", section: "Periode" },
  { name: "expiration_date", label: "Date expiration", type: "date", section: "Periode" },
  {
    name: "coverage_options",
    label: "Garanties optionnelles",
    type: "coverage-options",
    defaultValue: [],
    helper: "Selection rapide des codes de garanties ASS courants.",
    layout: "full",
    section: "Garanties",
  },
  {
    name: "ass_product_data",
    label: "Donnees produit ASS",
    type: "ass-product-data",
    defaultValue: {},
    helper: "Champs transmis dans ass_product_data selon le produit choisi.",
    layout: "full",
    section: "Produit ASS",
  },
  {
    name: "civil_liability_amount",
    label: "RC",
    type: "money",
    defaultValue: "0.00",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Montants",
  },
  {
    name: "premium_amount",
    label: "Prime",
    type: "money",
    defaultValue: "0.00",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Montants",
  },
  {
    name: "fees_amount",
    label: "Frais",
    type: "money",
    defaultValue: "0.00",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Montants",
  },
];

const paymentFields: ResourceFormField[] = [
  {
    name: "quote",
    label: "Devis",
    type: "relation",
    relation: QUOTE_RELATION,
    required: true,
    section: "Dossier",
  },
  {
    name: "method",
    label: "Methode",
    type: "select",
    defaultValue: "WALLET",
    required: true,
    section: "Encaissement",
    options: [
      { label: "Wallet", value: "WALLET" },
      { label: "Wave", value: "WAVE" },
      { label: "Orange Money", value: "ORANGE_MONEY" },
    ],
  },
  {
    name: "external_reference",
    label: "Reference externe",
    type: "text",
    helper: "Reference provider ou transactionnelle si deja connue.",
    section: "Encaissement",
  },
  {
    name: "idempotency_key",
    label: "Cle idempotence",
    type: "text",
    helper: "Cle unique recommandee pour eviter les doublons d'action.",
    section: "Securite",
  },
];

const contractFields: ResourceFormField[] = [
  {
    name: "payment",
    label: "Paiement confirme",
    type: "relation",
    relation: PAYMENT_RELATION,
    required: true,
    section: "Emission",
  },
];

const clientAccessFields: ResourceFormField[] = [
  {
    name: "client",
    label: "Client",
    type: "relation",
    relation: CLIENT_RELATION,
    required: true,
    section: "Beneficiaire",
  },
  {
    name: "contract",
    label: "Contrat",
    type: "relation",
    relation: CONTRACT_RELATION,
    required: true,
    section: "Beneficiaire",
  },
  {
    name: "delivery_channel",
    label: "Canal",
    type: "select",
    defaultValue: "MANUAL",
    required: true,
    section: "Remise",
    options: [
      { label: "Manuel", value: "MANUAL" },
      { label: "SMS", value: "SMS" },
      { label: "Email", value: "EMAIL" },
    ],
  },
  {
    name: "expires_in_days",
    label: "Expiration en jours",
    type: "number",
    defaultValue: 30,
    inputMode: "numeric",
    min: 1,
    max: 365,
    section: "Remise",
  },
];

const commissionRuleFields: ResourceFormField[] = [
  {
    name: "partner_group",
    label: "Groupe",
    type: "relation",
    relation: GROUP_RELATION,
    omitIfBlank: true,
    section: "Portee",
  },
  {
    name: "contributor",
    label: "Apporteur",
    type: "relation",
    relation: CONTRIBUTOR_RELATION,
    omitIfBlank: true,
    section: "Portee",
  },
  {
    name: "percentage_rate",
    label: "Taux",
    type: "number",
    defaultValue: "0.0000",
    inputMode: "decimal",
    min: 0,
    max: 100,
    step: "0.0001",
    section: "Calcul",
  },
  {
    name: "fixed_amount",
    label: "Montant fixe",
    type: "money",
    defaultValue: "0.00",
    inputMode: "decimal",
    min: 0,
    step: "0.01",
    section: "Calcul",
  },
  { name: "is_active", label: "Active", type: "checkbox", defaultValue: true, section: "Etat" },
];

const baseDetailFields: ResourceColumn[] = [
  { key: "id", label: "ID" },
  { key: "created_at", label: "Creation", kind: "date" },
  { key: "updated_at", label: "Mise a jour", kind: "date" },
];

export const resources: ResourceDefinition[] = [
  {
    slug: "groups",
    label: "Groupes",
    singular: "groupe",
    endpoint: "/groups",
    icon: "building",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    columns: [
      { key: "id", label: "ID" },
      { key: "name", label: "Nom" },
      { key: "slug", label: "Slug" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    detailFields: [
      { key: "name", label: "Nom" },
      { key: "slug", label: "Slug" },
      { key: "status", label: "Statut", kind: "status" },
      ...baseDetailFields,
    ],
    formFields: groupFields,
  },
  {
    slug: "users",
    label: "Utilisateurs",
    singular: "utilisateur",
    endpoint: "/users",
    icon: "users",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    columns: [
      { key: "id", label: "ID" },
      { key: "username", label: "Login" },
      { key: "email", label: "Email" },
      { key: "role", label: "Role", kind: "status" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "is_active", label: "Actif" },
    ],
    detailFields: [
      { key: "username", label: "Login" },
      { key: "email", label: "Email" },
      { key: "first_name", label: "Prenom" },
      { key: "last_name", label: "Nom" },
      { key: "phone", label: "Telephone" },
      { key: "role", label: "Role", kind: "status" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "is_active", label: "Actif" },
      ...baseDetailFields,
    ],
    formFields: userFields,
  },
  {
    slug: "contributors",
    label: "Apporteurs",
    singular: "apporteur",
    endpoint: "/contributors",
    icon: "badge",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    columns: [
      { key: "id", label: "ID" },
      { key: "username", label: "Login" },
      { key: "email", label: "Email" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "is_active", label: "Actif" },
    ],
    detailFields: [
      { key: "username", label: "Login" },
      { key: "email", label: "Email" },
      { key: "first_name", label: "Prenom" },
      { key: "last_name", label: "Nom" },
      { key: "phone", label: "Telephone" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "is_active", label: "Actif" },
      ...baseDetailFields,
    ],
    formFields: contributorFields,
  },
  {
    slug: "clients",
    label: "Clients",
    singular: "client",
    endpoint: "/clients",
    icon: "contact",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    columns: [
      { key: "id", label: "ID" },
      { key: "display_name", label: "Client" },
      { key: "phone", label: "Telephone" },
      { key: "email", label: "Email" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "contributor_username", label: "Apporteur" },
    ],
    detailFields: [
      { key: "display_name", label: "Client" },
      { key: "client_type", label: "Type", kind: "status" },
      { key: "phone", label: "Telephone" },
      { key: "email", label: "Email" },
      { key: "address", label: "Adresse" },
      { key: "identity_number", label: "Piece identite" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "is_active", label: "Actif" },
      ...baseDetailFields,
    ],
    formFields: clientFields,
  },
  {
    slug: "vehicles",
    label: "Vehicules",
    singular: "vehicule",
    endpoint: "/vehicles",
    icon: "car",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    columns: [
      { key: "id", label: "ID" },
      { key: "registration_number", label: "Immatriculation" },
      { key: "client_display_name", label: "Client" },
      { key: "brand", label: "Marque" },
      { key: "model", label: "Modele" },
      { key: "energy", label: "Energie" },
    ],
    detailFields: [
      { key: "registration_number", label: "Immatriculation" },
      { key: "client_display_name", label: "Client" },
      { key: "brand", label: "Marque" },
      { key: "model", label: "Modele" },
      { key: "chassis_number", label: "Chassis" },
      { key: "genre", label: "Genre ASS" },
      { key: "energy", label: "Energie" },
      { key: "fiscal_power", label: "Puissance fiscale" },
      { key: "seats", label: "Places" },
      { key: "new_value", label: "Valeur neuve", kind: "money" },
      { key: "current_value", label: "Valeur actuelle", kind: "money" },
      { key: "is_active", label: "Actif" },
      ...baseDetailFields,
    ],
    formFields: vehicleFields,
  },
  {
    slug: "quotes",
    label: "Devis",
    singular: "devis",
    endpoint: "/quotes",
    icon: "file-text",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    columns: [
      { key: "id", label: "ID" },
      { key: "reference", label: "Reference" },
      { key: "client_display_name", label: "Client" },
      { key: "product_type", label: "Produit", kind: "status" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "total_amount", label: "Total", kind: "money" },
    ],
    detailFields: [
      { key: "reference", label: "Reference" },
      { key: "client_display_name", label: "Client" },
      { key: "vehicle_registration_number", label: "Vehicule" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "product_type", label: "Produit", kind: "status" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "periodicity", label: "Periodicite" },
      { key: "duration", label: "Duree" },
      { key: "effective_date", label: "Date effet" },
      { key: "expiration_date", label: "Date expiration" },
      { key: "coverage_options", label: "Garanties", kind: "json" },
      { key: "ass_product_data", label: "Donnees ASS", kind: "json" },
      { key: "civil_liability_amount", label: "RC", kind: "money" },
      { key: "premium_amount", label: "Prime", kind: "money" },
      { key: "fees_amount", label: "Frais", kind: "money" },
      { key: "total_amount", label: "Total", kind: "money" },
      ...baseDetailFields,
    ],
    formFields: quoteFields,
  },
  {
    slug: "payments",
    label: "Paiements",
    singular: "paiement",
    endpoint: "/payments",
    icon: "credit-card",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    columns: [
      { key: "id", label: "ID" },
      { key: "quote_reference", label: "Devis" },
      { key: "client_display_name", label: "Client" },
      { key: "method", label: "Methode", kind: "status" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "amount", label: "Montant", kind: "money" },
    ],
    detailFields: [
      { key: "quote_reference", label: "Devis" },
      { key: "client_display_name", label: "Client" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "method", label: "Methode", kind: "status" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "amount", label: "Montant", kind: "money" },
      { key: "currency", label: "Devise" },
      { key: "external_reference", label: "Reference externe" },
      { key: "idempotency_key", label: "Cle idempotence" },
      { key: "confirmed_at", label: "Confirmation", kind: "date" },
      ...baseDetailFields,
    ],
    formFields: paymentFields,
    actions: [
      {
        label: "Confirmer",
        action: "confirm",
        guard: {
          title: "Confirmation paiement",
          description:
            "Cette action confirme l'encaissement et peut alimenter le wallet du groupe. Verifiez le montant, la devise et la reference avant de continuer.",
          confirmationValue: "CONFIRMER",
          warningItems: [
            "Ne confirmez pas un paiement externe sans preuve provider.",
            "L'action est journalisee et modifie l'etat financier du dossier.",
          ],
        },
        disabledWhen: {
          field: "status",
          notEquals: "PENDING",
          reason: "Seuls les paiements en attente peuvent etre confirmes.",
        },
      },
    ],
  },
  {
    slug: "contracts",
    label: "Contrats",
    singular: "contrat",
    endpoint: "/contracts",
    icon: "shield-check",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "contract_number", label: "Contrat" },
      { key: "client_display_name", label: "Client" },
      { key: "vehicle_registration_number", label: "Vehicule" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    detailFields: [
      { key: "contract_number", label: "Contrat" },
      { key: "quote_reference", label: "Devis" },
      { key: "client_display_name", label: "Client" },
      { key: "vehicle_registration_number", label: "Vehicule" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "attestation_reference", label: "Reference attestation" },
      { key: "qr_code_reference", label: "Reference QR" },
      { key: "issued_at", label: "Emission", kind: "date" },
      ...baseDetailFields,
    ],
    formFields: contractFields,
    actions: [
      {
        label: "Emettre QR",
        action: "issue",
        guard: {
          title: "Emission ASS/QR",
          description:
            "Cette action appelle ASS/Diotali et peut creer une attestation externe. Controlez la previsualisation du payload avant de confirmer.",
          confirmationValue: "EMETTRE",
          preflightAction: "ass-payload-preview",
          previewLabel: "Previsualisation ASS/QR",
          warningItems: [
            "Ne lancez pas l'emission depuis un contrat de production non verifie.",
            "Le paiement doit etre confirme et le contrat ne doit pas deja etre emis.",
            "Aucune action de stock QR ASS n'est exposee dans Horus.",
          ],
        },
        disabledWhen: {
          field: "status",
          equals: "ISSUED",
          reason: "Le contrat est deja emis.",
        },
      },
    ],
  },
  {
    slug: "client-access-tokens",
    label: "Acces client",
    singular: "jeton client",
    endpoint: "/client-access-tokens",
    icon: "key-round",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "client_display_name", label: "Client" },
      { key: "contract_number", label: "Contrat" },
      { key: "delivery_channel", label: "Canal", kind: "status" },
      { key: "is_active", label: "Actif" },
      { key: "expires_at", label: "Expiration", kind: "date" },
    ],
    detailFields: [
      { key: "client_display_name", label: "Client" },
      { key: "contract_number", label: "Contrat" },
      { key: "delivery_channel", label: "Canal", kind: "status" },
      { key: "is_active", label: "Actif" },
      { key: "expires_at", label: "Expiration", kind: "date" },
      { key: "used_at", label: "Utilisation", kind: "date" },
      { key: "revoked_at", label: "Revocation", kind: "date" },
      { key: "access_url", label: "Lien remis" },
      { key: "token", label: "Jeton brut" },
      { key: "mock_delivery", label: "Provider mock" },
      { key: "provider", label: "Provider" },
      { key: "destination", label: "Destination" },
      { key: "secret_returned", label: "Secret retourne" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    formFields: clientAccessFields,
    actions: [
      {
        label: "Revoquer",
        action: "revoke",
        guard: {
          title: "Revocation acces client",
          description:
            "Cette action coupe l'acces du client au portail pour ce jeton. Verifiez le client et le contrat avant de continuer.",
          confirmationValue: "REVOQUER",
        },
        disabledWhen: {
          field: "is_active",
          equals: false,
          reason: "Le jeton est deja inactif.",
        },
      },
      {
        label: "Renouveler",
        action: "renew",
        guard: {
          title: "Renouvellement acces client",
          description:
            "Cette action cree un nouveau secret client et remplace l'acces courant. L'ancien lien ne doit plus etre communique.",
          confirmationValue: "RENOUVELER",
        },
      },
      {
        label: "Renvoyer",
        action: "resend-link",
        guard: {
          title: "Renvoi lien client",
          description:
            "Cette action renvoie le lien d'acces client par le canal configure. Verifiez la destination avant de continuer.",
          confirmationValue: "RENVOYER",
        },
        disabledWhen: {
          field: "is_active",
          equals: false,
          reason: "Le jeton est inactif.",
        },
      },
    ],
  },
  {
    slug: "commission-rules",
    label: "Regles commission",
    singular: "regle",
    endpoint: "/commission-rules",
    icon: "percent",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    columns: [
      { key: "id", label: "ID" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "percentage_rate", label: "Taux" },
      { key: "fixed_amount", label: "Fixe", kind: "money" },
      { key: "is_active", label: "Actif" },
    ],
    detailFields: [
      { key: "partner_group_name", label: "Groupe" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "percentage_rate", label: "Taux" },
      { key: "fixed_amount", label: "Fixe", kind: "money" },
      { key: "is_active", label: "Actif" },
      ...baseDetailFields,
    ],
    formFields: commissionRuleFields,
  },
  {
    slug: "commissions",
    label: "Commissions",
    singular: "commission",
    endpoint: "/commissions",
    icon: "banknote",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    canCreate: false,
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "contract_number", label: "Contrat" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "amount", label: "Montant", kind: "money" },
      { key: "net_to_pay_amount", label: "Net", kind: "money" },
    ],
    detailFields: [
      { key: "contract_number", label: "Contrat" },
      { key: "contributor_username", label: "Apporteur" },
      { key: "status", label: "Statut", kind: "status" },
      { key: "base_amount", label: "Base", kind: "money" },
      { key: "percentage_rate", label: "Taux" },
      { key: "fixed_amount", label: "Fixe", kind: "money" },
      { key: "amount", label: "Commission", kind: "money" },
      { key: "net_to_pay_amount", label: "Net", kind: "money" },
      { key: "generated_at", label: "Generation", kind: "date" },
      { key: "paid_at", label: "Paiement", kind: "date" },
      ...baseDetailFields,
    ],
    actions: [
      {
        label: "Marquer payee",
        action: "mark-paid",
        guard: {
          title: "Paiement commission",
          description:
            "Cette action marque la commission comme payee. Verifiez le montant, le net a verser et le statut comptable avant de continuer.",
          confirmationValue: "PAYER",
        },
        disabledWhen: {
          field: "status",
          equals: "PAID",
          reason: "La commission est deja marquee payee.",
        },
      },
    ],
  },
  {
    slug: "wallets",
    label: "Wallets",
    singular: "wallet",
    endpoint: "/wallets",
    icon: "wallet",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    canCreate: false,
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "balance", label: "Solde", kind: "money" },
      { key: "currency", label: "Devise" },
      { key: "updated_at", label: "MAJ", kind: "date" },
    ],
  },
  {
    slug: "wallet-transactions",
    label: "Transactions wallet",
    singular: "transaction",
    endpoint: "/wallet-transactions",
    icon: "receipt-text",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    canCreate: false,
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "partner_group_name", label: "Groupe" },
      { key: "direction", label: "Sens", kind: "status" },
      { key: "amount", label: "Montant", kind: "money" },
      { key: "balance_after", label: "Solde apres", kind: "money" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
  },
  {
    slug: "audit-logs",
    label: "Audit logs",
    singular: "log",
    endpoint: "/audit-logs",
    icon: "activity",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN"],
    canCreate: false,
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "actor_username", label: "Acteur" },
      { key: "action", label: "Action", kind: "status" },
      { key: "target_type", label: "Cible" },
      { key: "target_id", label: "ID cible" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    detailFields: [
      { key: "actor_username", label: "Acteur" },
      { key: "action", label: "Action", kind: "status" },
      { key: "target_type", label: "Cible" },
      { key: "target_id", label: "ID cible" },
      { key: "metadata", label: "Metadonnees", kind: "json" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
  },
  {
    slug: "notifications",
    label: "Notifications",
    singular: "notification",
    endpoint: "/notifications",
    icon: "bell",
    roles: ["GENERAL_ADMIN", "GROUP_ADMIN", "CONTRIBUTOR"],
    canCreate: false,
    canEdit: false,
    canDelete: false,
    columns: [
      { key: "id", label: "ID" },
      { key: "title", label: "Titre" },
      { key: "notification_type", label: "Type", kind: "status" },
      { key: "is_read", label: "Lue" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    detailFields: [
      { key: "title", label: "Titre" },
      { key: "message", label: "Message" },
      { key: "notification_type", label: "Type", kind: "status" },
      { key: "target_type", label: "Cible" },
      { key: "target_id", label: "ID cible" },
      { key: "metadata", label: "Metadonnees", kind: "json" },
      { key: "is_read", label: "Lue" },
      { key: "read_at", label: "Lecture", kind: "date" },
      { key: "created_at", label: "Creation", kind: "date" },
    ],
    actions: [{ label: "Marquer lue", action: "mark-read" }],
  },
];

export function getResource(slug: string) {
  return resources.find((resource) => resource.slug === slug);
}

export function resourcesForRole(role: UserRole | undefined) {
  if (!role) {
    return [];
  }
  return resources.filter((resource) => resource.roles.includes(role));
}

export function canCreate(resource: ResourceDefinition) {
  return resource.canCreate !== false && Boolean(resource.formFields?.length);
}

export function canEdit(resource: ResourceDefinition) {
  return resource.canEdit !== false && Boolean(resource.formFields?.length);
}

export function canDelete(resource: ResourceDefinition) {
  return resource.canDelete !== false;
}

export function actionDisabledReason(record: ApiRecord, action: ResourceAction) {
  const rule = action.disabledWhen;
  if (!rule) {
    return "";
  }

  const value = record[rule.field];
  if ("equals" in rule && value === rule.equals) {
    return rule.reason;
  }
  if ("notEquals" in rule && value !== rule.notEquals) {
    return rule.reason;
  }
  return "";
}

export function initialPayload(resource: ResourceDefinition): ApiRecord {
  return Object.fromEntries(
    (resource.formFields ?? []).map((field) => [
      field.name,
      field.defaultValue ?? defaultValueForField(field),
    ]),
  );
}

export function editablePayload(resource: ResourceDefinition, record: ApiRecord): ApiRecord {
  return Object.fromEntries(
    (resource.formFields ?? []).map((field) => [
      field.name,
      record[field.name] ?? field.defaultValue ?? defaultValueForField(field),
    ]),
  );
}

export function formatRelationOption(record: ApiRecord, relation: RelationConfig) {
  const parts = relation.labelKeys
    .map((key) => record[key])
    .filter((value) => value !== null && value !== undefined && value !== "")
    .map(String);
  return parts.length ? parts.join(" - ") : `#${String(record.id ?? "")}`;
}

function defaultValueForField(field: ResourceFormField) {
  if (field.type === "checkbox") {
    return false;
  }
  if (field.type === "json") {
    return field.name.endsWith("options") ? [] : {};
  }
  if (field.type === "coverage-options") {
    return [];
  }
  if (field.type === "ass-product-data") {
    return {};
  }
  return "";
}
