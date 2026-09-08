"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import {
  ALERTAS_DISPARADOS_EVENT,
  METRICAS_ATUALIZADAS_EVENT,
  type AlertasDisparadosPayload,
} from "@/lib/metricas-event-bus";

function notificarAlertas(payload: AlertasDisparadosPayload) {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (Notification.permission !== "granted") return;

  for (const alerta of payload.alertas) {
    const cliente = alerta.cliente_nome ?? `Cliente ${alerta.cliente_id}`;
    new Notification(`Alerta: ${cliente}`, {
      body: alerta.gatilho_nome ?? "Um gatilho disparou",
      tag: `alerta-${alerta.alerta_id}`,
    });
  }
}

/**
 * Componente invisível: mantém uma conexão SSE aberta com /api/eventos e força um refresh dos
 * Server Components (sem reload de página) quando o scheduler termina uma nova janela de coleta
 * ou quando um gatilho dispara um alerta — nesse segundo caso, também dispara uma notificação
 * nativa do navegador (se o usuário já tiver permitido).
 */
export function LiveRefresher() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }

    const source = new EventSource("/api/eventos");
    source.addEventListener(METRICAS_ATUALIZADAS_EVENT, () => router.refresh());
    source.addEventListener(ALERTAS_DISPARADOS_EVENT, (evento) => {
      try {
        notificarAlertas(JSON.parse(evento.data) as AlertasDisparadosPayload);
      } catch {
        // payload inesperado - ainda assim atualiza a tela, só não notifica
      }
      router.refresh();
    });

    return () => {
      source.close();
    };
  }, [router]);

  return null;
}
