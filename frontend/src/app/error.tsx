"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-full flex-1 flex-col items-center justify-center gap-4 bg-zinc-50 px-6 text-center">
      <p className="text-xs font-medium uppercase tracking-wide text-rose-500">Erro</p>
      <h1 className="text-xl font-semibold text-zinc-900">Não foi possível carregar os dados</h1>
      <p className="max-w-md text-sm text-zinc-500">
        {error.message || "Verifique se o backend (FastAPI) está rodando em BACKEND_API_URL."}
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-zinc-700"
      >
        Tentar de novo
      </button>
    </div>
  );
}
