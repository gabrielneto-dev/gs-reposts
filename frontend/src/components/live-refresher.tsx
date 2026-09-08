"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { METRICAS_ATUALIZADAS_EVENT } from "@/lib/metricas-event-bus";

/**
 * Componente invisível: mantém uma conexão SSE aberta com /api/eventos e força um refresh dos
 * Server Components (sem reload de página) quando o scheduler termina uma nova janela de coleta.
 */
export function LiveRefresher() {
  const router = useRouter();

  useEffect(() => {
    const source = new EventSource("/api/eventos");
    source.addEventListener(METRICAS_ATUALIZADAS_EVENT, () => {
      router.refresh();
    });

    return () => {
      source.close();
    };
  }, [router]);

  return null;
}
