import { useQuery } from "@tanstack/react-query";
import { RefreshCw, CheckCircle2 } from "lucide-react";
import { PendenciaCard } from "@/components/cards/PendenciaCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { api } from "@/lib/api";
import { POLLING_INTERVAL_MS } from "@/lib/constants";

export function Pendencias() {
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["pendencias"],
    queryFn: () => api.listarPendencias(),
    refetchInterval: POLLING_INTERVAL_MS,
  });

  const grupos = data?.pendencias ?? [];
  const total = grupos.reduce((acc, g) => acc + g.entries.length, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pendências de Mapeamento</h1>
          <p className="text-muted-foreground">
            Mapeie as contas do cliente para as contas contábeis.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void refetch()}
          disabled={isFetching}
          className="gap-1"
        >
          <RefreshCw className={`h-3 w-3 ${isFetching ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
      </div>

      {grupos.length > 0 && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{grupos.length} protocolo{grupos.length !== 1 ? "s" : ""} pendente{grupos.length !== 1 ? "s" : ""}</span>
            <span>{total} lançamento{total !== 1 ? "s" : ""}</span>
          </div>
          <Progress value={0} className="h-1.5" />
        </div>
      )}

      {isLoading && (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-lg border bg-muted" />
          ))}
        </div>
      )}

      {!isLoading && grupos.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-12 text-center">
          <CheckCircle2 className="h-12 w-12 text-green-500" />
          <div>
            <p className="font-medium">Nenhuma pendência no momento</p>
            <p className="text-sm text-muted-foreground">
              Todos os lotes foram processados com sucesso.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {grupos.map((g) => (
          <PendenciaCard
            key={g.protocolo_id}
            group={g}
            onResolved={() => void refetch()}
          />
        ))}
      </div>
    </div>
  );
}
