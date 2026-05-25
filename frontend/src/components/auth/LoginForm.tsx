"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { LockKeyhole, LogIn } from "lucide-react";

import { useAuth } from "@/components/auth/AuthProvider";
import { getApiBaseUrl } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login(username, password);
      router.replace("/dashboard");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Connexion impossible");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="brand-mark" aria-hidden="true">
          <LockKeyhole size={26} />
        </div>
        <div>
          <p className="eyebrow">Horus Assurances</p>
          <h1 id="login-title">Connexion</h1>
        </div>

        <form className="form-stack" onSubmit={handleSubmit}>
          <label>
            Identifiant
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>

          <label>
            Mot de passe
            <input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={submitting}>
            <LogIn size={18} />
            {submitting ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <p className="api-hint">{getApiBaseUrl()}</p>
      </section>
    </main>
  );
}
