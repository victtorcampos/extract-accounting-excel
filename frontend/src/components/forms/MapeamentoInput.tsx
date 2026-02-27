import { useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface MapeamentoInputProps {
  label: string;
  contaRaw: string;
  tipo: "DEBITO" | "CREDITO";
  protocolo_id: number;
  cnpj_empresa: string;
  onMapear: (contaCliente: string, contaContabilidade: string, tipo: "DEBITO" | "CREDITO") => Promise<void>;
}

export function MapeamentoInput({
  label,
  contaRaw,
  tipo,
  onMapear,
}: MapeamentoInputProps) {
  const [value, setValue] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [done, setDone] = useState(false);

  async function handleMapear() {
    if (!value.trim()) return;
    setIsPending(true);
    try {
      await onMapear(contaRaw, value.trim(), tipo);
      setDone(true);
    } finally {
      setIsPending(false);
    }
  }

  if (done) {
    return (
      <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
        <CheckCircle2 className="h-4 w-4" />
        <span className="font-mono">{contaRaw}</span>
        <span className="text-muted-foreground">→</span>
        <span className="font-medium">{value}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="min-w-[120px] font-mono text-sm text-muted-foreground">{contaRaw}</span>
      <Input
        className="h-8 text-sm"
        placeholder={`Conta ${label}`}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && void handleMapear()}
        aria-label={`Conta contábil para ${contaRaw}`}
      />
      <Button
        size="sm"
        className="h-8 shrink-0"
        disabled={isPending || !value.trim()}
        onClick={() => void handleMapear()}
      >
        {isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "Mapear"}
      </Button>
    </div>
  );
}
