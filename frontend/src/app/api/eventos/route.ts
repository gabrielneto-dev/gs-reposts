import {
  ALERTAS_DISPARADOS_EVENT,
  METRICAS_ATUALIZADAS_EVENT,
  metricasEventBus,
  type AlertasDisparadosPayload,
  type MetricasAtualizadasPayload,
} from "@/lib/metricas-event-bus";

export const dynamic = "force-dynamic";

const HEARTBEAT_MS = 25_000;

/**
 * SSE consumido pelo navegador (mesma origem, sem CORS). Repassa cada evento recebido nos webhooks
 * (métricas atualizadas E alertas disparados) pra todo cliente conectado, que reage disparando
 * router.refresh() — ver components/live-refresher.tsx.
 */
export async function GET(request: Request) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const enviarMetricas = (payload: MetricasAtualizadasPayload) => {
        controller.enqueue(
          encoder.encode(`event: ${METRICAS_ATUALIZADAS_EVENT}\ndata: ${JSON.stringify(payload)}\n\n`)
        );
      };
      const enviarAlertas = (payload: AlertasDisparadosPayload) => {
        controller.enqueue(
          encoder.encode(`event: ${ALERTAS_DISPARADOS_EVENT}\ndata: ${JSON.stringify(payload)}\n\n`)
        );
      };

      metricasEventBus.on(METRICAS_ATUALIZADAS_EVENT, enviarMetricas);
      metricasEventBus.on(ALERTAS_DISPARADOS_EVENT, enviarAlertas);

      const heartbeat = setInterval(() => {
        controller.enqueue(encoder.encode(": heartbeat\n\n"));
      }, HEARTBEAT_MS);

      request.signal.addEventListener("abort", () => {
        clearInterval(heartbeat);
        metricasEventBus.off(METRICAS_ATUALIZADAS_EVENT, enviarMetricas);
        metricasEventBus.off(ALERTAS_DISPARADOS_EVENT, enviarAlertas);
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
