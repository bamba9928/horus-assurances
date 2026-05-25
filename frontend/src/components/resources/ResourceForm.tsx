"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { listResource } from "@/lib/api";
import { buildPayload } from "@/lib/resource-form";
import {
  editablePayload,
  formatRelationOption,
  initialPayload,
  type ResourceDefinition,
  type ResourceFormField,
} from "@/lib/resources";
import type { ApiRecord, PaginatedResponse } from "@/types/api";

type FormValues = Record<string, unknown>;
type RelationOptions = Record<string, Array<{ label: string; value: number | string }>>;

export function ResourceForm({
  mode,
  onCancel,
  onSubmit,
  record,
  resource,
}: {
  mode: "create" | "edit";
  onCancel: () => void;
  onSubmit: (payload: ApiRecord) => Promise<void>;
  record?: ApiRecord;
  resource: ResourceDefinition;
}) {
  const formFields = useMemo(() => resource.formFields ?? [], [resource.formFields]);
  const [values, setValues] = useState<FormValues>(() =>
    mode === "edit" && record ? editablePayload(resource, record) : initialPayload(resource),
  );
  const [relationOptions, setRelationOptions] = useState<RelationOptions>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadRelationOptions() {
      const entries = await Promise.all(
        formFields
          .filter((field) => field.type === "relation" && field.relation)
          .map(async (field) => {
            const params = new URLSearchParams({ page_size: "100" });
            try {
              const response: PaginatedResponse<ApiRecord> = await listResource(
                field.relation!.endpoint,
                params,
              );
              return [
                field.name,
                response.results.map((item) => ({
                  label: formatRelationOption(item, field.relation!),
                  value: item.id ?? "",
                })),
              ] as const;
            } catch {
              return [field.name, []] as const;
            }
          }),
      );

      if (mounted) {
        setRelationOptions(Object.fromEntries(entries));
      }
    }

    loadRelationOptions();
    return () => {
      mounted = false;
    };
  }, [formFields]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await onSubmit(buildPayload(formFields, values));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Enregistrement impossible");
    } finally {
      setSubmitting(false);
    }
  }

  function setValue(name: string, value: unknown) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        {formFields.map((field) => (
          <FormField
            field={field}
            key={field.name}
            options={relationOptions[field.name] ?? []}
            value={values[field.name]}
            onChange={(value) => setValue(field.name, value)}
          />
        ))}
      </div>

      {error ? <p className="form-error">{error}</p> : null}

      <div className="panel-actions">
        <button className="secondary-button" onClick={onCancel} type="button">
          Annuler
        </button>
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? "Enregistrement..." : "Enregistrer"}
        </button>
      </div>
    </form>
  );
}

function FormField({
  field,
  onChange,
  options,
  value,
}: {
  field: ResourceFormField;
  onChange: (value: unknown) => void;
  options: Array<{ label: string; value: number | string }>;
  value: unknown;
}) {
  const commonLabel = (
    <>
      {field.label}
      {field.required ? <span className="required-marker"> *</span> : null}
    </>
  );

  if (field.type === "checkbox") {
    return (
      <label className="checkbox-field">
        <input
          checked={Boolean(value)}
          onChange={(event) => onChange(event.target.checked)}
          type="checkbox"
        />
        {commonLabel}
      </label>
    );
  }

  if (field.type === "select") {
    return (
      <label>
        {commonLabel}
        <select
          required={field.required}
          value={valueToInput(value)}
          onChange={(event) => onChange(event.target.value)}
        >
          {!field.required ? <option value="">Non renseigne</option> : null}
          {(field.options ?? []).map((option) => (
            <option key={String(option.value)} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
        {field.helper ? <span className="field-help">{field.helper}</span> : null}
      </label>
    );
  }

  if (field.type === "relation") {
    return (
      <label>
        {commonLabel}
        <select
          required={field.required}
          value={valueToInput(value)}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Selectionner</option>
          {options.map((option) => (
            <option key={String(option.value)} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
        {field.helper ? <span className="field-help">{field.helper}</span> : null}
      </label>
    );
  }

  if (field.type === "textarea" || field.type === "json") {
    return (
      <label className={field.type === "json" ? "wide-field" : undefined}>
        {commonLabel}
        <textarea
          required={field.required}
          value={field.type === "json" ? jsonValueToInput(value) : valueToInput(value)}
          onChange={(event) => onChange(event.target.value)}
          spellCheck={false}
        />
        {field.helper ? <span className="field-help">{field.helper}</span> : null}
      </label>
    );
  }

  return (
    <label>
      {commonLabel}
      <input
        required={field.required}
        type={inputType(field.type)}
        value={valueToInput(value)}
        onChange={(event) => onChange(event.target.value)}
      />
      {field.helper ? <span className="field-help">{field.helper}</span> : null}
    </label>
  );
}

function inputType(type: ResourceFormField["type"]) {
  if (type === "email") {
    return "email";
  }
  if (type === "password") {
    return "password";
  }
  if (type === "tel") {
    return "tel";
  }
  if (type === "money" || type === "number") {
    return "number";
  }
  if (type === "date") {
    return "date";
  }
  return "text";
}

function jsonValueToInput(value: unknown) {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value ?? null, null, 2);
}

function valueToInput(value: unknown) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value);
}
