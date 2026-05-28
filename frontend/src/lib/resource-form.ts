import type { ApiRecord } from "@/types/api";
import type { ResourceFormField } from "@/lib/resources";

export function buildPayload(
  fields: ResourceFormField[],
  values: Record<string, unknown>,
): ApiRecord {
  const payload: ApiRecord = {};

  for (const field of fields) {
    const rawValue = values[field.name];
    if (field.omitIfBlank && isBlank(rawValue)) {
      continue;
    }

    if (field.type === "json") {
      payload[field.name] =
        typeof rawValue === "string" ? JSON.parse(rawValue || "null") : rawValue;
      continue;
    }

    if (field.type === "coverage-options") {
      payload[field.name] = normalizeCoverageOptions(rawValue);
      continue;
    }

    if (field.type === "ass-product-data") {
      payload[field.name] = normalizeAssProductData(
        String(values.product_type ?? ""),
        rawValue,
      );
      continue;
    }

    if (field.type === "checkbox") {
      payload[field.name] = Boolean(rawValue);
      continue;
    }

    if (field.type === "number" || field.type === "relation") {
      payload[field.name] = isBlank(rawValue) ? null : Number(rawValue);
      continue;
    }

    if (field.type === "money") {
      payload[field.name] = isBlank(rawValue) ? "0.00" : String(rawValue);
      continue;
    }

    if (field.type === "date") {
      payload[field.name] = isBlank(rawValue) ? null : String(rawValue);
      continue;
    }

    payload[field.name] = rawValue ?? "";
  }

  return payload;
}

export function validateBusinessRules(
  resourceSlug: string,
  values: Record<string, unknown>,
) {
  const errors: string[] = [];

  if (resourceSlug === "clients") {
    const clientType = String(values.client_type ?? "");
    const firstName = String(values.first_name ?? "").trim();
    const lastName = String(values.last_name ?? "").trim();
    const companyName = String(values.company_name ?? "").trim();
    if (clientType === "INDIVIDUAL" && !firstName && !lastName) {
      errors.push("Client personne physique : renseigner au moins un prenom ou un nom.");
    }
    if (clientType === "COMPANY" && !companyName) {
      errors.push("Client personne morale : la societe est obligatoire.");
    }
  }

  if (resourceSlug === "vehicles") {
    const seats = optionalNumber(values.seats);
    const fiscalPower = optionalNumber(values.fiscal_power);
    const newValue = optionalNumber(values.new_value);
    const currentValue = optionalNumber(values.current_value);
    if (seats !== null && seats < 1) {
      errors.push("Vehicule : le nombre de places doit etre superieur a 0.");
    }
    if (fiscalPower !== null && fiscalPower < 0) {
      errors.push("Vehicule : la puissance fiscale ne peut pas etre negative.");
    }
    if (newValue !== null && currentValue !== null && currentValue > newValue) {
      errors.push("Vehicule : la valeur actuelle ne peut pas depasser la valeur neuve.");
    }
  }

  if (resourceSlug === "quotes") {
    const duration = optionalNumber(values.duration);
    if (duration === null || duration < 1 || duration > 120) {
      errors.push("Devis : la duree doit etre comprise entre 1 et 120.");
    }
    if (dateAfter(values.effective_date, values.expiration_date)) {
      errors.push("Devis : la date d'effet doit etre anterieure a la date d'expiration.");
    }
    for (const fieldName of ["civil_liability_amount", "premium_amount", "fees_amount"]) {
      const amount = optionalNumber(values[fieldName]);
      if (amount !== null && amount < 0) {
        errors.push("Devis : les montants ne peuvent pas etre negatifs.");
        break;
      }
    }
    validateAssProductData(String(values.product_type ?? ""), values.ass_product_data, errors);
  }

  if (resourceSlug === "client-access-tokens") {
    const expiresInDays = optionalNumber(values.expires_in_days);
    if (expiresInDays !== null && (expiresInDays < 1 || expiresInDays > 365)) {
      errors.push("Acces client : l'expiration doit etre comprise entre 1 et 365 jours.");
    }
  }

  if (resourceSlug === "commission-rules") {
    const percentageRate = optionalNumber(values.percentage_rate);
    const fixedAmount = optionalNumber(values.fixed_amount);
    if (percentageRate !== null && (percentageRate < 0 || percentageRate > 100)) {
      errors.push("Commission : le taux doit etre compris entre 0 et 100.");
    }
    if (fixedAmount !== null && fixedAmount < 0) {
      errors.push("Commission : le montant fixe ne peut pas etre negatif.");
    }
  }

  return errors;
}

function normalizeCoverageOptions(value: unknown) {
  if (Array.isArray(value)) {
    return value.map(Number).filter((item) => Number.isFinite(item));
  }
  if (typeof value === "string") {
    return parseNumberList(value);
  }
  return [];
}

function normalizeAssProductData(productType: string, value: unknown) {
  const data = isRecord(value) ? value : {};
  const normalized: ApiRecord = {};

  for (const [key, rawValue] of Object.entries(data)) {
    if (isBlank(rawValue)) {
      continue;
    }

    if (key === "cylindre" || key === "nombreCarte") {
      normalized[key] = Number(rawValue);
      continue;
    }

    if (key === "requests" && typeof rawValue === "string") {
      normalized[key] = JSON.parse(rawValue || "[]");
      continue;
    }

    if (
      productType === "AUTO" &&
      ["garantiesOptPT", "garantiesOptAR", "garantiesOptAS"].includes(key)
    ) {
      normalized[key] = Array.isArray(rawValue) ? rawValue : parseNumberList(String(rawValue));
      continue;
    }

    normalized[key] = rawValue;
  }

  return normalized;
}

function validateAssProductData(
  productType: string,
  value: unknown,
  errors: string[],
) {
  const data = isRecord(value) ? value : {};
  if (productType === "MOTO") {
    if (isBlank(data.cylindre)) {
      errors.push("Produit moto : le cylindre est obligatoire.");
    }
    if (isBlank(data.usage)) {
      errors.push("Produit moto : l'usage est obligatoire.");
    }
  }
  if (productType === "TRAILER" && isBlank(data.referenceVehicule)) {
    errors.push("Produit remorque : la reference du vehicule tracteur est obligatoire.");
  }
  if (productType === "GARAGE") {
    const nombreCarte = optionalNumber(data.nombreCarte);
    if (nombreCarte !== null && nombreCarte < 1) {
      errors.push("Produit garage : le nombre de cartes doit etre superieur a 0.");
    }
  }
  if (productType === "FLEET" && !isBlank(data.requests)) {
    try {
      const requests =
        typeof data.requests === "string" ? JSON.parse(data.requests) : data.requests;
      if (!Array.isArray(requests)) {
        errors.push("Produit flotte : requests doit etre une liste JSON.");
      }
    } catch {
      errors.push("Produit flotte : requests doit etre un JSON valide.");
    }
  }
}

function parseNumberList(value: string) {
  return value
    .split(/[,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map(Number)
    .filter((item) => Number.isFinite(item));
}

function optionalNumber(value: unknown) {
  if (isBlank(value)) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function dateAfter(start: unknown, end: unknown) {
  if (isBlank(start) || isBlank(end)) {
    return false;
  }
  return String(start) > String(end);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isBlank(value: unknown) {
  return value === null || value === undefined || value === "";
}
