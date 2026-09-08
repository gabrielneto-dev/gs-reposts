"use server";

import { revalidatePath } from "next/cache";

import { backendUrl } from "./backend";

/** Marca um alerta como visto. Idempotente — chamar de novo num já visto não faz nada. */
export async function marcarAlertaVisto(alertaId: number): Promise<void> {
  const res = await fetch(backendUrl(`/api/alertas/${alertaId}/marcar-visto`), { method: "POST" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao marcar o alerta ${alertaId} como visto`);
  }
  revalidatePath("/alertas");
  revalidatePath("/");
}

/** Marca todos os alertas não vistos como vistos — de um cliente específico, ou todos se
 * `clienteId` vier vazio. */
export async function marcarTodosVistos(clienteId?: number): Promise<void> {
  const params = new URLSearchParams();
  if (clienteId !== undefined) params.set("cliente_id", String(clienteId));

  const res = await fetch(backendUrl(`/api/alertas/marcar-todos-vistos?${params.toString()}`), { method: "POST" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao marcar todos os alertas como vistos`);
  }
  revalidatePath("/alertas");
  revalidatePath("/");
}
