"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BadgeCheck,
  Banknote,
  Bell,
  Building2,
  Car,
  Contact,
  CreditCard,
  FileText,
  Gauge,
  KeyRound,
  LogOut,
  Percent,
  ReceiptText,
  ShieldCheck,
  Users,
  Wallet,
} from "lucide-react";

import { useAuth } from "@/components/auth/AuthProvider";
import { resourcesForRole } from "@/lib/resources";

const iconMap = {
  activity: Activity,
  badge: BadgeCheck,
  banknote: Banknote,
  bell: Bell,
  building: Building2,
  car: Car,
  contact: Contact,
  "credit-card": CreditCard,
  "file-text": FileText,
  "key-round": KeyRound,
  percent: Percent,
  "receipt-text": ReceiptText,
  "shield-check": ShieldCheck,
  users: Users,
  wallet: Wallet,
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user } = useAuth();
  const navigationResources = resourcesForRole(user?.role);

  function handleLogout() {
    void logout().finally(() => router.replace("/login"));
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-square">H</div>
          <div>
            <strong>Horus</strong>
            <span>Assurances</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Navigation principale">
          <Link className={pathname === "/dashboard" ? "nav-item active" : "nav-item"} href="/dashboard">
            <Gauge size={18} />
            Dashboard
          </Link>

          {navigationResources.map((resource) => {
            const Icon = iconMap[resource.icon as keyof typeof iconMap] ?? FileText;
            const href = `/resources/${resource.slug}`;
            return (
              <Link
                className={pathname === href ? "nav-item active" : "nav-item"}
                href={href}
                key={resource.slug}
              >
                <Icon size={18} />
                {resource.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div>
            <span className="topbar-label">{user?.role}</span>
            <strong>{displayName(user)}</strong>
          </div>
          <button className="icon-button text-button" onClick={handleLogout} type="button">
            <LogOut size={18} />
            Deconnexion
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}

function displayName(user: ReturnType<typeof useAuth>["user"]) {
  if (!user) {
    return "";
  }
  const name = `${user.first_name ?? ""} ${user.last_name ?? ""}`.trim();
  return name || user.username;
}
