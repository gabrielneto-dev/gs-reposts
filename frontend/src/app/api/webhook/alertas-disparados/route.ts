import { NextResponse } from "next/server";

import {
  ALERTAS_DISPARADOS_EVENT,
  metricasEventBus,
  type AlertasDisparadosPayload,
} from "@/lib/metricas-event-bus";

/**
 * Recebido do backend/ (avaliação de gatilhos) sempre que algum alerta dispara. Mesmo padrão de
 * `metricas-atualizadas/route.ts`: chamada servidor-a-servidor, só repassa pro barramento em
 * memória — quem decide o que fazer é o Route Handler de SSE (/api/eventos).
 */
export async function POST(request: Request) {
  const payload = (await request.json()) as AlertasDisparadosPayload;
  metricasEventBus.emit(ALERTAS_DISPARADOS_EVENT, payload);
  return NextResponse.json({ ok: true });
}
