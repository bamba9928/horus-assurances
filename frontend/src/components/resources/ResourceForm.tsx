"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { listResource } from "@/lib/api";
import { buildPayload, validateBusinessRules } from "@/lib/resource-form";
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
type FormSection = {
  title: string;
  fields: ResourceFormField[];
};

const DEFAULT_COVERAGE_OPTIONS = [
  { label: "Garantie 1", value: 1 },
  { label: "Garantie 2", value: 2 },
  { label: "Garantie 4", value: 4 },
];

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
  const sections = useMemo(() => groupFormFields(formFields), [formFields]);
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
      const validationErrors = validateBusinessRules(resource.slug, values);
      if (validationErrors.length) {
        throw new Error(validationErrors.join(" "));
      }
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
      <div className="form-sections">
        {sections.map((section) => (
          <fieldset className="form-section" key={section.title}>
            <legend>{section.title}</legend>
            <div className="form-grid">
              {section.fields.map((field) => (
                <FormField
                  allValues={values}
                  field={field}
                  key={field.name}
                  options={relationOptions[field.name] ?? []}
                  value={values[field.name]}
                  onChange={(value) => setValue(field.name, value)}
                />
              ))}
            </div>
          </fieldset>
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
  allValues,
  field,
  onChange,
  options,
  value,
}: {
  allValues: FormValues;
  field: ResourceFormField;
  onChange: (value: unknown) => void;
  options: Array<{ label: string; value: number | string }>;
  value: unknown;
}) {
  const labelClassName = fieldClassName(field);
  const commonLabel = (
    <>
      {field.label}
      {field.required ? <span className="required-marker"> *</span> : null}
    </>
  );

  if (field.type === "checkbox") {
    return (
      <label className="checkbox-field field-shell">
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
      <label className={labelClassName}>
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
      <label className={labelClassName}>
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

  if (field.type === "coverage-options") {
    return (
      <CoverageOptionsField
        field={field}
        onChange={onChange}
        value={value}
      />
    );
  }

  if (field.type === "ass-product-data") {
    return (
      <AssProductDataField
        field={field}
        onChange={onChange}
        productType={String(allValues.product_type ?? "AUTO")}
        value={value}
      />
    );
  }

  if (field.type === "textarea" || field.type === "json") {
    return (
      <label className={labelClassName}>
        {commonLabel}
        <textarea
          placeholder={field.placeholder}
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
    <label className={labelClassName}>
      {commonLabel}
      <input
        inputMode={field.inputMode}
        max={field.max}
        min={field.min}
        placeholder={field.placeholder}
        required={field.required}
        step={field.step}
        type={inputType(field.type)}
        value={valueToInput(value)}
        onChange={(event) => onChange(normalizeInputValue(field, event.target.value))}
      />
      {field.helper ? <span className="field-help">{field.helper}</span> : null}
    </label>
  );
}

function CoverageOptionsField({
  field,
  onChange,
  value,
}: {
  field: ResourceFormField;
  onChange: (value: unknown) => void;
  value: unknown;
}) {
  const selectedValues = numberArray(value);
  const typedValue = Array.isArray(value) ? selectedValues.join(", ") : valueToInput(value);
  const options = field.options?.length ? field.options : DEFAULT_COVERAGE_OPTIONS;

  function toggleCoverage(rawValue: string | number | boolean) {
    const numericValue = Number(rawValue);
    const nextValues = selectedValues.includes(numericValue)
      ? selectedValues.filter((item) => item !== numericValue)
      : [...selectedValues, numericValue].sort((left, right) => left - right);
    onChange(nextValues);
  }

  return (
    <div className="compound-field wide-field">
      <div className="compound-label">
        <strong>{field.label}</strong>
        {field.required ? <span className="required-marker"> *</span> : null}
      </div>
      <div className="choice-grid">
        {options.map((option) => {
          const checked = selectedValues.includes(Number(option.value));
          return (
            <button
              aria-pressed={checked}
              className={checked ? "choice-button active" : "choice-button"}
              key={String(option.value)}
              onClick={() => toggleCoverage(option.value)}
              type="button"
            >
              {option.label}
            </button>
          );
        })}
      </div>
      <label className="inline-field">
        Codes garanties
        <input
          inputMode="numeric"
          onChange={(event) => onChange(event.target.value)}
          placeholder="1, 2, 4"
          value={typedValue}
        />
      </label>
      {field.helper ? <span className="field-help">{field.helper}</span> : null}
    </div>
  );
}

function AssProductDataField({
  field,
  onChange,
  productType,
  value,
}: {
  field: ResourceFormField;
  onChange: (value: unknown) => void;
  productType: string;
  value: unknown;
}) {
  const data = asRecord(value);

  function updateValue(name: string, nextValue: unknown) {
    onChange({ ...data, [name]: nextValue });
  }

  return (
    <div className="compound-field wide-field">
      <div className="compound-label">
        <strong>{field.label}</strong>
        <span className="product-pill">{productType || "AUTO"}</span>
      </div>
      <div className="product-field-grid">
        {productType === "AUTO" ? (
          <>
            <label>
              Garanties PT
              <input
                inputMode="numeric"
                onChange={(event) => updateValue("garantiesOptPT", event.target.value)}
                placeholder="1, 2"
                value={numberListInput(data.garantiesOptPT)}
              />
            </label>
            <label>
              Garanties AR
              <input
                inputMode="numeric"
                onChange={(event) => updateValue("garantiesOptAR", event.target.value)}
                placeholder="4"
                value={numberListInput(data.garantiesOptAR)}
              />
            </label>
            <label>
              Garanties AS
              <input
                inputMode="numeric"
                onChange={(event) => updateValue("garantiesOptAS", event.target.value)}
                placeholder="1, 4"
                value={numberListInput(data.garantiesOptAS)}
              />
            </label>
          </>
        ) : null}

        {productType === "MOTO" ? (
          <>
            <label>
              Cylindre
              <input
                inputMode="numeric"
                min={1}
                onChange={(event) => updateValue("cylindre", event.target.value)}
                placeholder="126"
                type="number"
                value={valueToInput(data.cylindre)}
              />
            </label>
            <label>
              Usage
              <input
                onChange={(event) => updateValue("usage", event.target.value)}
                placeholder="NON_COMMERCIAL"
                value={valueToInput(data.usage)}
              />
            </label>
          </>
        ) : null}

        {productType === "TRAILER" ? (
          <label className="wide-field">
            Reference vehicule tracteur
            <input
              onChange={(event) =>
                updateValue("referenceVehicule", event.target.value.toUpperCase())
              }
              placeholder="DK-TRACT-001"
              value={valueToInput(data.referenceVehicule)}
            />
          </label>
        ) : null}

        {productType === "GARAGE" ? (
          <label>
            Nombre de cartes
            <input
              inputMode="numeric"
              min={1}
              onChange={(event) => updateValue("nombreCarte", event.target.value)}
              type="number"
              value={valueToInput(data.nombreCarte ?? 1)}
            />
          </label>
        ) : null}

        {productType === "FLEET" ? (
          <>
            <label>
              Reference flotte
              <input
                onChange={(event) => updateValue("referenceFlotte", event.target.value)}
                placeholder="HORUS-FLEET-001"
                value={valueToInput(data.referenceFlotte)}
              />
            </label>
            <label className="wide-field">
              Requests flotte
              <textarea
                onChange={(event) => updateValue("requests", event.target.value)}
                placeholder='[{"requestId":"HORUS-FLEET-001-1"}]'
                spellCheck={false}
                value={jsonValueToInput(data.requests ?? [])}
              />
            </label>
          </>
        ) : null}

        {productType === "SCHOOL_BUS" ? (
          <p className="product-note">
            Les champs ASS bus ecole sont derives du vehicule, de la periode, des montants et
            des garanties.
          </p>
        ) : null}
      </div>
      {field.helper ? <span className="field-help">{field.helper}</span> : null}
    </div>
  );
}

function groupFormFields(fields: ResourceFormField[]): FormSection[] {
  const sections = new Map<string, ResourceFormField[]>();
  for (const field of fields) {
    const title = field.section ?? "Informations";
    sections.set(title, [...(sections.get(title) ?? []), field]);
  }
  return Array.from(sections.entries()).map(([title, sectionFields]) => ({
    title,
    fields: sectionFields,
  }));
}

function fieldClassName(field: ResourceFormField) {
  const classNames = ["field-shell"];
  if (
    field.layout === "full" ||
    field.type === "json" ||
    field.type === "textarea" ||
    field.type === "ass-product-data" ||
    field.type === "coverage-options"
  ) {
    classNames.push("wide-field");
  }
  return classNames.join(" ");
}

function normalizeInputValue(field: ResourceFormField, value: string) {
  if (field.transform === "uppercase") {
    return value.toUpperCase();
  }
  return value;
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

function numberArray(value: unknown) {
  if (Array.isArray(value)) {
    return value.map(Number).filter((item) => Number.isFinite(item));
  }
  if (typeof value === "string") {
    return value
      .split(/[,\s]+/)
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));
  }
  return [];
}

function numberListInput(value: unknown) {
  return Array.isArray(value) ? numberArray(value).join(", ") : valueToInput(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}
