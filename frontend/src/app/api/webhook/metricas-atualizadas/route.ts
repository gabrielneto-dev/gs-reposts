import { NextResponse } from "next/server";

import {
  METRICAS_ATUALIZADAS_EVENT,
  metricasEventBus,
  type MetricasAtualizadasPayload,
} from "@/lib/metricas-event-bus";

/**
 * Recebido do backend/ (scheduler) ao fim de cada janela de coleta. Chamada servidor-a-servidor,
 * nunca vem do navegador — sem CORS envolvido. Só repassa pro barramento em memória; quem decide
 * o que fazer com isso é o Route Handler de SSE (/api/eventos).
 */
export async function POST(request: Request) {
  const payload = (await request.json()) as MetricasAtualizadasPayload;
  metricasEventBus.emit(METRICAS_ATUALIZADAS_EVENT, payload);
  return NextResponse.json({ ok: true });
}
