import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, RefreshCw } from "lucide-react";
import { LoteForm } from "@/components/forms/LoteForm";
import { ProtocoloCard } from "@/components/cards/ProtocoloCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { POLLING_INTERVAL_MS } from "@/lib/constants";
import { useLocalStorage } from "@/hooks/useLocalStorage";

export function Home() {
  const [cnpjInput, setCnpjInput] = useState("");
  const [searchCnpj, setSearchCnpj] = useLocalStorage("lastCnpj", "");

  const {
    data,
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["protocolos", searchCnpj],
    queryFn: () => api.listarPorCnpj(searchCnpj),
    enabled: searchCnpj.length === 14,
    refetchInterval: (query) => {
      const protocolos = query.state.data?.protocolos ?? [];
      const hasPending = protocolos.some((p) => p.status === "PENDING");
      return hasPending ? POLLING_INTERVAL_MS : false;
    },
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const digits = cnpjInput.replace(/\D/g, "");
    if (digits.length === 14) setSearchCnpj(digits);
  }

  const protocolos = data?.protocolos ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Lançamento de Lote Contábil</h1>
        <p className="text-muted-foreground">Envie o arquivo Excel para processamento automático.</p>
      </div>

      <LoteForm onSuccess={() => void refetch()} />

      {/* Consulta de Protocolos */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Protocolos por CNPJ</h2>
          {searchCnpj && (
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
          )}
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            placeholder="CNPJ (14 dígitos)"
            value={cnpjInput}
            onChange={(e) => setCnpjInput(e.target.value.replace(/\D/g, "").slice(0, 14))}
            maxLength={14}
            className="max-w-xs"
            aria-label="CNPJ para busca"
          />
          <Button type="submit" variant="outline" size="icon" aria-label="Buscar">
            <Search className="h-4 w-4" />
          </Button>
        </form>

        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg border bg-muted" />
            ))}
          </div>
        )}

        {!isLoading && protocolos.length === 0 && searchCnpj && (
          <p className="text-sm text-muted-foreground">Nenhum protocolo encontrado para este CNPJ.</p>
        )}

        <div className="space-y-2">
          {protocolos.map((p) => (
            <ProtocoloCard
              key={p.protocolo}
              protocolo={p}
              onDeleted={() => void refetch()}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
