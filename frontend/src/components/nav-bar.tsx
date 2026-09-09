"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Relatórios" },
  { href: "/gatilhos", label: "Gatilhos" },
  { href: "/alertas", label: "Central de alertas" },
  { href: "/janelas", label: "Janelas" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-black/5 bg-white px-6 sm:px-10">
      <div className="mx-auto flex max-w-6xl gap-6 text-sm font-medium text-zinc-500">
        {LINKS.map((link) => {
          const ativo = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`border-b-2 py-4 transition ${
                ativo ? "border-amber-500 text-zinc-900" : "border-transparent hover:text-zinc-900"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
