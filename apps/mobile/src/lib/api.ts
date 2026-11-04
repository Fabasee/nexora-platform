export type NexoraProduct = {
  key: string;
  name: string;
  description: string;
};

type ProductListResponse = {
  results: NexoraProduct[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getApiBaseUrl(): string {
  const value = process.env.EXPO_PUBLIC_API_BASE_URL?.trim();
  if (!value) throw new Error("EXPO_PUBLIC_API_BASE_URL is not configured.");

  const normalized = value.replace(/\/+$/, "");
  if (!/^https?:\/\//i.test(normalized)) {
    throw new Error("The Nexora API base URL must use HTTP or HTTPS.");
  }
  return normalized;
}

export async function fetchAccessibleProducts(
  idToken: string,
): Promise<NexoraProduct[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/products/`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${idToken}`,
    },
  });

  if (!response.ok) {
    throw new ApiError("Unable to load Nexora products.", response.status);
  }

  const payload = (await response.json()) as ProductListResponse;
  if (!payload || !Array.isArray(payload.results)) {
    throw new ApiError("The Nexora API returned an invalid response.", response.status);
  }
  return payload.results;
}

export type NexoraAccount = {
  id: string;
  status: "active" | "suspended" | "deactivated";
  created_at: string;
  providers: { provider: string; last_authenticated_at: string | null }[];
};

export async function fetchCurrentAccount(idToken: string): Promise<NexoraAccount> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/account/me/`, {
    method: "GET",
    headers: { Accept: "application/json", Authorization: `Bearer ${idToken}` },
  });
  if (!response.ok) throw new ApiError("Unable to load Nexora account.", response.status);
  const payload = (await response.json()) as NexoraAccount;
  if (!payload || typeof payload.id !== "string" || !Array.isArray(payload.providers)) {
    throw new ApiError("The Nexora API returned an invalid account response.", response.status);
  }
  return payload;
}


export type NexoraSecurityEvent = {
  id: string;
  event_type: string;
  occurred_at: string;
  provider: string;
  source_ip: string | null;
  user_agent: string;
};

export async function fetchSecurityEvents(idToken: string): Promise<NexoraSecurityEvent[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/account/security-events/`, {
    method: "GET",
    headers: { Accept: "application/json", Authorization: `Bearer ${idToken}` },
  });
  if (!response.ok) {
    throw new ApiError("Unable to load Nexora security events.", response.status);
  }
  const payload = (await response.json()) as { results?: NexoraSecurityEvent[] };
  if (!payload || !Array.isArray(payload.results)) {
    throw new ApiError("The Nexora API returned an invalid security event response.", response.status);
  }
  return payload.results;
}


export type NexoraIdentitySession = {
  id: string;
  provider: string;
  authenticated_at: string;
  created_at: string;
  last_seen_at: string;
  revoked_at: string | null;
  is_active: boolean;
  is_current: boolean;
  source_ip: string | null;
  user_agent: string;
};

export async function fetchIdentitySessions(idToken: string): Promise<NexoraIdentitySession[]> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/account/sessions/`, {
    method: "GET",
    headers: { Accept: "application/json", Authorization: `Bearer ${idToken}` },
  });
  if (!response.ok) throw new ApiError("Unable to load Nexora sessions.", response.status);
  const payload = (await response.json()) as { results?: NexoraIdentitySession[] };
  if (!payload || !Array.isArray(payload.results)) {
    throw new ApiError("The Nexora API returned an invalid session response.", response.status);
  }
  return payload.results;
}

export async function revokeIdentitySession(idToken: string, sessionId: string): Promise<void> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/account/sessions/${encodeURIComponent(sessionId)}/revoke/`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${idToken}`,
      },
    },
  );
  if (!response.ok) throw new ApiError("Unable to revoke Nexora session.", response.status);
}
