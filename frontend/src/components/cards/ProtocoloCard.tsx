import { useState } from "react";
import { Trash2, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusChip } from "@/components/StatusChip";
import { DownloadButton } from "@/components/DownloadButton";
import { api } from "@/lib/api";
import { useAppToast } from "@/context/ToastContext";
import { Protocolo } from "@/types/api";

interface ProtocoloCardProps {
  protocolo: Protocolo;
  onDeleted: () => void;
}

export function ProtocoloCard({ protocolo, onDeleted }: ProtocoloCardProps) {
  const { toast } = useAppToast();
  const [deleting, setDeleting] = useState(false);
  const [txtBase64, setTxtBase64] = useState<string | null>(null);

  async function handleDownload() {
    try {
      const res = await api.consultarProtocolo(protocolo.protocolo);
      if (res.status === "COMPLETED") setTxtBase64(res.resultado);
    } catch {
      toast({ title: "Erro ao buscar TXT", variant: "destructive" });
    }
  }

  async function handleDelete() {
    if (!confirm(`Excluir protocolo ${protocolo.protocolo}?`)) return;
    setDeleting(true);
    try {
      await api.deletarProtocolo(protocolo.protocolo);
      toast({ title: "Protocolo excluído", variant: "success" });
      onDeleted();
    } catch (err) {
      toast({
        title: "Erro ao excluir",
        description: err instanceof Error ? err.message : "",
        variant: "destructive",
      });
    } finally {
      setDeleting(false);
    }
  }

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardContent className="flex items-center justify-between gap-4 py-4">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="truncate font-mono text-sm font-medium">{protocolo.protocolo}</p>
          <p className="text-xs text-muted-foreground">
            {new Date(protocolo.data).toLocaleString("pt-BR")}
          </p>
          {protocolo.status === "ERROR" && protocolo.error_message && (
            <p className="text-xs text-destructive line-clamp-2">{protocolo.error_message}</p>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <StatusChip status={protocolo.status} />

          {protocolo.status === "COMPLETED" && (
            <>
              {txtBase64 ? (
                <DownloadButton
                  base64Content={txtBase64}
                  filename={`${protocolo.protocolo}.txt`}
                />
              ) : (
                <Button size="sm" variant="outline" onClick={() => void handleDownload()}>
                  Ver TXT
                </Button>
              )}
            </>
          )}

          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
            disabled={deleting || protocolo.status === "PENDING"}
            onClick={() => void handleDelete()}
            aria-label="Excluir protocolo"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
