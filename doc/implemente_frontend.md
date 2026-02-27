# 🎨 Proposta UX/UI Frontend — Contabilidade Sorriso

> **Stack:** React 19.2 + Vite + TypeScript + shadcn/ui + Tailwind  
> **Objetivo:** SPA fluida, acessível, responsiva, com feedback instantâneo  
> **Monorepo:** Backend serve frontend em `/`, Docker unificado

---

## 📁 Estrutura de Pastas (Monorepo)

```
extract-accounting-excel/
├── backend/                    # ✅ Existente (FastAPI SOLID)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui componentes (Button, Input, Table)
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── forms/
│   │   │   │   ├── LoteForm.tsx    # P1
│   │   │   │   └── MapeamentoForm.tsx # P2
│   │   │   └── cards/
│   │   │       ├── PendenciaCard.tsx
│   │   │       └── ProtocoloCard.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx           # P1 + P3 unificado
│   │   │   ├── Pendencias.tsx     # P2
│   │   │   └── Status.tsx         # Polling individual
│   │   ├── hooks/
│   │   │   ├── useApi.ts          # fetch tipado + cache
│   │   │   ├── usePolling.ts      # Status PENDING → COMPLETED
│   │   │   └── useLocalStorage.ts # Cache de mapeamentos
│   │   ├── lib/
│   │   │   ├── api.ts             # Zod schemas + backend types
│   │   │   ├── utils.ts           # cn(), toast
│   │   │   └── constants.ts       # Status, layouts
│   │   ├── types/
│   │   │   └── api.ts             # Protocolo, StagingEntry (gerado de backend)
│   │   └── App.tsx
│   ├── public/
│   │   └── favicon.ico
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── package.json
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🎨 Paletas de Cores (3 opções + Dark Mode)

### **Paleta 1: Corporativo Azul (Padrão)**
```
Primária: #1E40AF (blue-800)
Secundária: #3B82F6 (blue-500)
Sucesso: #10B981 (emerald-500)
Aviso: #F59E0B (amber-500)
Erro: #EF4444 (red-500)
Fundo: #F8FAFC (slate-50)
```

### **Paleta 2: Contábil Verde (Financeiro)**
```
Primária: #15803D (green-700)
Secundária: #22C55E (green-500)
Sucesso: #059669 (emerald-600)
Aviso: #D97706 (amber-700)
Erro: #DC2626 (red-600)
```

### **Paleta 3: Neutro Enterprise (Minimalista)**
```
Primária: #374151 (gray-700)
Secundária: #6B7280 (gray-500)
Sucesso: #059669 (emerald-600)
Aviso: #D97706 (amber-700)
Erro: #DC2626 (red-600)
```

**Theme:** `dark` / `light` / `system` — shadcn/ui nativo com `next-themes`

---

## 🔄 Novo Fluxo Funcional (React v19 + UX Moderna)

```
1. Landing (Home): Form Lote + Lista Protocolos (P1+P3 unificado)
   ↓ POST /lancamento_lote_contabil
2. Toast: "Protocolo 123456 criado — PROCESSANDO"
3. Polling automático: usePolling('/lancamento_lote_contabil?protocolo=123456')
   ↓ Status PENDING → WAITING_MAPPING
4. Toast: "Pendências detectadas" → Sidebar ativa P2
5. Pendencias: Cards com inputs inline + "Mapear" → POST /pendencias/resolver
6. Auto-reprocessa → Toast "COMPLETED" → Download automático TXT
```

**Estados visuais por status (v19 Activity):**
```
PENDING:      Skeleton loader + spinner
WAITING:      Cards expansíveis com inputs
COMPLETED:    <Activity mode="visible">Download Button</Activity>
ERROR:        Card vermelho com error_message
```

---

## 🛠️ Fases de Implementação

### **FASE 1: Setup + Landing (2h)**
```
1. vite create frontend --template react-ts
2. npm i lucide-react @radix-ui/react-*
3. npx shadcn-ui@latest init
4. npx shadcn-ui@latest add button input table card toast form
5. npx shadcn-ui@latest add accordion progress
6. Implementar Home.tsx: LoteForm + ProtocolosTable
7. useApi.ts: fetch tipado com Zod + backend schemas
```
**Resultado:** SPA com P1+P3 funcional, 100% responsivo

### **FASE 2: Pendências + Polling (3h)**
```
1. Pendencias.tsx: PendenciaCard com Accordion (debito/credito)
2. usePolling.ts: React 19 use() + polling inteligente
3. MapeamentoForm.tsx: Inline inputs + real-time feedback
4. Header.tsx + Sidebar.tsx com navegação
```
**Resultado:** Fluxo completo P2 com UX de app moderno

### **FASE 3: Polish + Tema (1h)**
```
1. next-themes: Dark/Light/System toggle
2. Tailwind config: 3 paletas CSS vars
3. Acessibilidade: aria-labels, focus management
4. PWA: vite-plugin-pwa (offline cache)
```
**Resultado:** Produto polido, acessível, multi-tema

### **FASE 4: Docker + Deploy (30min)**
```
Dockerfile:
FROM node:20-alpine AS build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
COPY backend/ /app/backend/
COPY --from=build /frontend/dist /app/backend/frontend/
WORKDIR /app/backend
RUN pip install -r requirements.txt
EXPOSE 8111
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8111"]
```
**docker-compose.yml:** Backend+Frontend unificado

---

## 📱 Componentes Chave (React v19)

### **1. LoteForm.tsx (shadcn Form)**
```tsx
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField name="cnpj">
      <Input placeholder="00.000.000/0000-00" />
      <FormMessage />
    </FormField>
    <Button type="submit" disabled={isPending}>
      {isPending ? <Loader /> : "Enviar"} 
    </Button>
  </form>
</Form>
```

### **2. PendenciaCard.tsx (Activity v19)**
```tsx
<Activity mode={status === 'WAITING_MAPPING' ? 'visible' : 'hidden'}>
  <Card>
    <Accordion>
      <AccordionItem value="debito">
        <AccordionTrigger>Contas Débito Pendentes</AccordionTrigger>
        <AccordionContent>
          {contas.map(conta => (
            <MapeamentoInput 
              key={conta} 
              onMapear={handleMapear}
            />
          ))}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  </Card>
</Activity>
```

### **3. useApi.ts (TanStack Query + Zod)**
```tsx
const api = createTRPCProxyClient<AppRouter>({
  links: [httpBatchLink({ url: '/api/trpc' })]
})

const { data, isPending } = api.protocolos.listar.useQuery({ cnpj })
```

---

## 🎯 Métricas Pós-Implementação

| Métrica | Atual | Proposta |
|---|---|---|
| **Tempo de interação** | 3s+ (fetch + HTML string) | <500ms (cache + optimistic) |
| **Bundle size** | 0 (HTML puro) | ~45KB gzipped |
| **Linhas de código** | 800 JS inline | 200 componentes reutilizáveis |
| **Acessibilidade** | 0/100 Lighthouse | 95+/100 |
| **Responsividade** | Quebra tablets | Mobile-first |
| **Dark Mode** | Não | ✅ 3 temas |

**Tempo total implementação:** 6-8h  
**ROI:** Frontend profissional, escalável para 10+ funcionalidades futuras
