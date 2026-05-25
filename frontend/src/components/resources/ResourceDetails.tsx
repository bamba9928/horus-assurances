"use client";

import { displayValue, formatDate, formatMoney } from "@/lib/format";
import type { ResourceDefinition, ResourceColumn } from "@/lib/resources";
import type { ApiRecord } from "@/types/api";

export function ResourceDetails({
  record,
  resource,
}: {
  record: ApiRecord;
  resource: ResourceDefinition;
}) {
  const fields = resource.detailFields ?? resource.columns;

  return (
    <div className="details-panel">
      <dl className="detail-grid">
        {fields.map((field) => (
          <div className={field.kind === "json" ? "detail-item wide" : "detail-item"} key={field.key}>
            <dt>{field.label}</dt>
            <dd>{renderDetail(record[field.key], field)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function renderDetail(value: unknown, field: ResourceColumn) {
  if (field.kind === "date") {
    return formatDate(value);
  }
  if (field.kind === "money") {
    return formatMoney(value);
  }
  if (field.kind === "status") {
    return <span className="status-pill">{displayValue(value)}</span>;
  }
  if (field.kind === "json") {
    return <pre className="inline-json">{JSON.stringify(value ?? null, null, 2)}</pre>;
  }
  return displayValue(value);
}
