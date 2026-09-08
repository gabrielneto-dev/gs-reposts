import {
  METRICAS_ATUALIZADAS_EVENT,
  metricasEventBus,
  type MetricasAtualizadasPayload,
} from "@/lib/metricas-event-bus";

export const dynamic = "force-dynamic";

const HEARTBEAT_MS = 25_000;

/**
 * SSE consumido pelo navegador (mesma origem, sem CORS). Repassa cada evento recebido no webhook
 * pra todo cliente conectado, que reage disparando router.refresh() — ver components/live-refresher.tsx.
 */
export async function GET(request: Request) {
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const enviar = (payload: MetricasAtualizadasPayload) => {
        controller.enqueue(
          encoder.encode(`event: ${METRICAS_ATUALIZADAS_EVENT}\ndata: ${JSON.stringify(payload)}\n\n`)
        );
      };

      metricasEventBus.on(METRICAS_ATUALIZADAS_EVENT, enviar);

      const heartbeat = setInterval(() => {
        controller.enqueue(encoder.encode(": heartbeat\n\n"));
      }, HEARTBEAT_MS);

      request.signal.addEventListener("abort", () => {
        clearInterval(heartbeat);
        metricasEventBus.off(METRICAS_ATUALIZADAS_EVENT, enviar);
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
