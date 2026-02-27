import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { LAYOUT_NOME } from "@/lib/constants";
import { useAppToast } from "@/context/ToastContext";

const schema = z.object({
  protocolo: z.string().min(1, "Protocolo obrigatório"),
  cnpj: z.string().regex(/^\d{14}$/, "CNPJ deve ter 14 dígitos"),
  codigo_matriz: z.coerce.number().int().min(1).max(10000),
  codigo_filial: z.coerce.number().int().min(1).max(10000).optional(),
  periodo: z.string().regex(/^\d{4}-\d{2}$/, "Use o formato YYYY-MM"),
  lote_inicial: z.coerce.number().int().min(1).default(1),
  email_destinatario: z.string().email("E-mail inválido"),
  layout_nome: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

interface LoteFormProps {
  onSuccess: () => void;
}

const MAX_FILE_MB = 10;

export function LoteForm({ onSuccess }: LoteFormProps) {
  const { toast } = useAppToast();
  const [file, setFile] = useState<File | null>(null);
  const [isPending, setIsPending] = useState(false);

  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      protocolo: String(Date.now()),
      lote_inicial: 1,
      layout_nome: LAYOUT_NOME,
    },
  });

  async function toBase64(f: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(f);
    });
  }

  async function onSubmit(data: FormData) {
    if (!file) {
      toast({ title: "Arquivo obrigatório", variant: "destructive" });
      return;
    }
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      toast({ title: `Arquivo maior que ${MAX_FILE_MB}MB`, variant: "destructive" });
      return;
    }

    setIsPending(true);
    try {
      const arquivo_base64 = await toBase64(file);
      await api.criarLote({ ...data, arquivo_base64 });
      toast({
        title: "Protocolo criado",
        description: `${data.protocolo} — processando em background`,
        variant: "success",
      });
      form.reset({ protocolo: String(Date.now()), lote_inicial: 1, layout_nome: LAYOUT_NOME });
      setFile(null);
      onSuccess();
    } catch (err) {
      toast({
        title: "Erro ao criar protocolo",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsPending(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Novo Lançamento de Lote</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4 sm:grid-cols-2">
          {/* Protocolo */}
          <div className="space-y-1">
            <Label htmlFor="protocolo">Protocolo</Label>
            <Input id="protocolo" {...form.register("protocolo")} />
            {form.formState.errors.protocolo && (
              <p className="text-xs text-destructive">{form.formState.errors.protocolo.message}</p>
            )}
          </div>

          {/* CNPJ */}
          <div className="space-y-1">
            <Label htmlFor="cnpj">CNPJ (14 dígitos)</Label>
            <Input id="cnpj" placeholder="00000000000000" maxLength={14} {...form.register("cnpj")} />
            {form.formState.errors.cnpj && (
              <p className="text-xs text-destructive">{form.formState.errors.cnpj.message}</p>
            )}
          </div>

          {/* Período */}
          <div className="space-y-1">
            <Label htmlFor="periodo">Período</Label>
            <Input id="periodo" placeholder="2026-01" {...form.register("periodo")} />
            {form.formState.errors.periodo && (
              <p className="text-xs text-destructive">{form.formState.errors.periodo.message}</p>
            )}
          </div>

          {/* Email */}
          <div className="space-y-1">
            <Label htmlFor="email_destinatario">E-mail destinatário</Label>
            <Input id="email_destinatario" type="email" {...form.register("email_destinatario")} />
            {form.formState.errors.email_destinatario && (
              <p className="text-xs text-destructive">{form.formState.errors.email_destinatario.message}</p>
            )}
          </div>

          {/* Código Matriz */}
          <div className="space-y-1">
            <Label htmlFor="codigo_matriz">Código Matriz</Label>
            <Input id="codigo_matriz" type="number" min={1} max={10000} {...form.register("codigo_matriz")} />
            {form.formState.errors.codigo_matriz && (
              <p className="text-xs text-destructive">{form.formState.errors.codigo_matriz.message}</p>
            )}
          </div>

          {/* Código Filial */}
          <div className="space-y-1">
            <Label htmlFor="codigo_filial">Código Filial (opcional)</Label>
            <Input id="codigo_filial" type="number" min={1} max={10000} {...form.register("codigo_filial")} />
          </div>

          {/* Lote Inicial */}
          <div className="space-y-1">
            <Label htmlFor="lote_inicial">Lote Inicial</Label>
            <Input id="lote_inicial" type="number" min={1} {...form.register("lote_inicial")} />
          </div>

          {/* Layout */}
          <div className="space-y-1">
            <Label>Layout</Label>
            <Select
              value={form.watch("layout_nome")}
              onValueChange={(v) => form.setValue("layout_nome", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="layout_brastelha_1">layout_brastelha_1</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Arquivo Excel */}
          <div className="space-y-1 sm:col-span-2">
            <Label htmlFor="arquivo">Arquivo Excel (máx. {MAX_FILE_MB}MB)</Label>
            <div className="flex items-center gap-3">
              <label
                htmlFor="arquivo"
                className="flex cursor-pointer items-center gap-2 rounded-md border border-dashed px-4 py-2 text-sm text-muted-foreground hover:border-primary hover:text-primary transition-colors"
              >
                <Upload className="h-4 w-4" />
                {file ? file.name : "Selecionar arquivo .xlsx"}
              </label>
              <input
                id="arquivo"
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file && (
                <span className="text-xs text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </span>
              )}
            </div>
          </div>

          <div className="sm:col-span-2">
            <Button type="submit" disabled={isPending} className="w-full sm:w-auto">
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Enviando...
                </>
              ) : (
                "Enviar Lote"
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
