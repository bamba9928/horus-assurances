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

function isBlank(value: unknown) {
  return value === null || value === undefined || value === "";
}
