"use client";

import { useParams } from "next/navigation";

import { ResourcePage } from "@/components/resources/ResourcePage";

export default function ResourceRoutePage() {
  const params = useParams<{ resource: string }>();

  return <ResourcePage slug={params.resource} />;
}
