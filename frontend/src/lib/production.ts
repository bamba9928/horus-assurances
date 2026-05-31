export type ProductionFilters = {
  client: string;
  contract_status: string;
  contributor: string;
  date_debut: string;
  date_fin: string;
  group: string;
  issued: string;
  month: string;
  page: number;
  page_size: number;
  payment_status: string;
  product: string;
  registration_number: string;
  today: boolean;
  with_trailer: string;
};

export const DEFAULT_PRODUCTION_FILTERS: ProductionFilters = {
  client: "",
  contract_status: "",
  contributor: "",
  date_debut: "",
  date_fin: "",
  group: "",
  issued: "",
  month: "",
  page: 1,
  page_size: 20,
  payment_status: "",
  product: "",
  registration_number: "",
  today: false,
  with_trailer: "",
};

export function buildProductionSearchParams(filters: ProductionFilters) {
  const params = new URLSearchParams({
    page: String(filters.page),
    page_size: String(filters.page_size),
  });

  if (filters.today) {
    params.set("today", "true");
  }
  setParam(params, "month", filters.month);
  setParam(params, "date_debut", filters.date_debut);
  setParam(params, "date_fin", filters.date_fin);
  setParam(params, "contributor", filters.contributor);
  setParam(params, "group", filters.group);
  setParam(params, "product", filters.product);
  setParam(params, "contract_status", filters.contract_status);
  setParam(params, "payment_status", filters.payment_status);
  setParam(params, "immatriculation", filters.registration_number);
  setParam(params, "client", filters.client);
  setParam(params, "issued", filters.issued);
  setParam(params, "remorque", filters.with_trailer);
  return params;
}

function setParam(params: URLSearchParams, key: string, value: string) {
  const normalized = value.trim();
  if (normalized) {
    params.set(key, normalized);
  }
}
