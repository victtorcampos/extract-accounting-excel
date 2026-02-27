import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { MapeamentoInput } from "@/components/forms/MapeamentoInput";
import { api } from "@/lib/api";
import { useAppToast } from "@/context/ToastContext";
import { PendenciaGroup } from "@/types/api";
import { formatCurrency } from "@/lib/utils";

interface PendenciaCardProps {
  group: PendenciaGroup;
  onResolved: () => void;
}

export function PendenciaCard({ group, onResolved }: PendenciaCardProps) {
  const { toast } = useAppToast();

  const contasDebito = useMemo(
    () => [...new Set(group.entries.map((e) => e.conta_debito_raw))],
    [group.entries]
  );
  const contasCredito = useMemo(
    () => [...new Set(group.entries.map((e) => e.conta_credito_raw))],
    [group.entries]
  );

  async function handleMapear(
    contaCliente: string,
    contaContabilidade: string,
    tipo: "DEBITO" | "CREDITO"
  ) {
    try {
      const res = await api.resolverPendencia({
        protocolo_id: group.protocolo_id,
        conta_cliente: contaCliente,
        conta_contabilidade: contaContabilidade,
        tipo,
        cnpj_empresa: group.cnpj,
      });
      if (res.reprocessando) {
        toast({
          title: "Todas pendências resolvidas!",
          description: "Reprocessando arquivo...",
          variant: "success",
        });
        onResolved();
      } else {
        toast({
          title: "Mapeamento salvo",
          description: res.mensagem,
          variant: "success",
        });
      }
    } catch (err) {
      toast({
        title: "Erro ao mapear conta",
        description: err instanceof Error ? err.message : "",
        variant: "destructive",
      });
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base font-mono">{group.numero_protocolo}</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">CNPJ: {group.cnpj}</p>
          </div>
          <Badge variant="outline" className="shrink-0">
            {group.entries.length} lançamento{group.entries.length !== 1 ? "s" : ""}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {/* Preview dos lançamentos */}
        <div className="rounded-md border overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-muted">
              <tr>
                <th className="px-3 py-2 text-left font-medium">Data</th>
                <th className="px-3 py-2 text-left font-medium">Débito</th>
                <th className="px-3 py-2 text-left font-medium">Crédito</th>
                <th className="px-3 py-2 text-right font-medium">Valor</th>
              </tr>
            </thead>
            <tbody>
              {group.entries.slice(0, 5).map((e) => (
                <tr key={e.id} className="border-t">
                  <td className="px-3 py-1.5 text-muted-foreground">{e.data_lancamento}</td>
                  <td className="px-3 py-1.5 font-mono">{e.conta_debito_raw}</td>
                  <td className="px-3 py-1.5 font-mono">{e.conta_credito_raw}</td>
                  <td className="px-3 py-1.5 text-right">{formatCurrency(e.valor)}</td>
                </tr>
              ))}
              {group.entries.length > 5 && (
                <tr className="border-t">
                  <td colSpan={4} className="px-3 py-1.5 text-center text-muted-foreground">
                    +{group.entries.length - 5} lançamentos
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mapeamentos */}
        <Accordion type="multiple" className="w-full">
          <AccordionItem value="debito">
            <AccordionTrigger className="text-sm">
              Contas Débito ({contasDebito.length})
            </AccordionTrigger>
            <AccordionContent className="space-y-2">
              {contasDebito.map((conta) => (
                <MapeamentoInput
                  key={conta}
                  label="contábil débito"
                  contaRaw={conta}
                  tipo="DEBITO"
                  protocolo_id={group.protocolo_id}
                  cnpj_empresa={group.cnpj}
                  onMapear={handleMapear}
                />
              ))}
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="credito">
            <AccordionTrigger className="text-sm">
              Contas Crédito ({contasCredito.length})
            </AccordionTrigger>
            <AccordionContent className="space-y-2">
              {contasCredito.map((conta) => (
                <MapeamentoInput
                  key={conta}
                  label="contábil crédito"
                  contaRaw={conta}
                  tipo="CREDITO"
                  protocolo_id={group.protocolo_id}
                  cnpj_empresa={group.cnpj}
                  onMapear={handleMapear}
                />
              ))}
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
