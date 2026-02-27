# 🚀 Roadmap Desenvolvimento Frontend — Contabilidade Sorriso

> **Stack Final:** React 19.2 + Vite + TypeScript + shadcn/ui + Tailwind + next-themes  
> **Tempo Total Estimado:** 8h (1 dia desenvolvedor)  
> **Monorepo Docker:** Backend serve frontend em `/`  
> **Git Commits:** Ignorar — foco em milestones funcionais

---

## 📋 Visão Geral das Fases

```
Fase 1: Setup + Landing (2h)  → MVP funcional (P1+P3)
Fase 2: Pendências + UX (3h)  → Fluxo completo
Fase 3: Polish + Tema (1.5h)  → Produto polido
Fase 4: Docker + Deploy (1h)  → Produção
Fase 5: Testes + Otimização (0.5h) → QA
```

---

## 🗺️ Roadmap Detalhado

### **FASE 1: SETUP + LANDING PAGE (2h)**
**Objetivo:** SPA com formulário Lote + lista Protocolos funcionando  
**Milestone:** `npm run dev` → Home completa

```
[ ] 1.1 Frontend Setup (20min)
    npm create vite@latest frontend -- --template react-ts
    cd frontend && npm i
    npm i lucide-react @radix-ui/react-*
    npm i @tanstack/react-query class-variance-authority clsx tailwind-merge
    npm i next-themes @radix-ui/react-toast
    npx shadcn-ui@latest init
    npx shadcn-ui add button input form card table toast accordion progress badge

[ ] 1.2 Tipagem Backend (15min)
    src/types/api.ts ← Zod schemas de backend/schemas/*.py
    src/lib/api.ts ← TanStack Query client

[ ] 1.3 Home.tsx (1h)
    src/pages/Home.tsx ← LoteForm + ProtocolosTable
    src/components/forms/LoteForm.tsx ← shadcn Form + Zod
    src/hooks/useApi.ts ← POST /lancamento_lote_contabil
    src/hooks/useQueryProtocolos.ts ← GET /lancamento_lote_contabil?cnpj=*

[ ] 1.4 Teste E2E
    npm run dev → Form submit → Toast sucesso → Lista atualiza
```

**Critério de aceitação:** Form envia → Toast "Protocolo criado" → Lista popula

---

### **FASE 2: PENDÊNCIAS + FLUXO COMPLETO (3h)**
**Objetivo:** Mapeamento + polling automático funcionando  
**Milestone:** Upload → Pendências → Mapear → Download TXT

```
[ ] 2.1 Navegação (30min)
    src/components/layout/AppLayout.tsx ← Header + Sidebar
    src/App.tsx ← React Router + TanStack QueryProvider

[ ] 2.2 Pendencias Page (1.5h)
    src/pages/Pendencias.tsx ← PendenciaCard list
    src/components/cards/PendenciaCard.tsx ← Accordion (deb/cred)
    src/components/forms/MapeamentoInput.tsx ← Inline input + Mapear button
    src/hooks/usePolling.ts ← GET /pendencias + POST /pendencias/resolver

[ ] 2.3 Status Flow (30min)
    src/hooks/useProtocoloStatus.ts ← Polling individual /lancamento_lote_contabil?protocolo=*
    src/components/StatusChip.tsx ← PENDING/WAITING/COMPLETED/ERROR

[ ] 2.4 Download (15min)
    src/hooks/useDownloadTXT.ts ← GET + Blob download
    src/components/DownloadButton.tsx ← <Activity mode={status === 'COMPLETED'}>
```

**Critério de aceitação:** Upload → Auto-detect pendências → Mapear todas → Auto-download TXT

---

### **FASE 3: POLISH + TEMA (1.5h)**
**Objetivo:** Produto visualmente polido e acessível  
**Milestone:** Dark mode + mobile perfeito

```
[ ] 3.1 Tema (30min)
    next-themes setup
    tailwind.config.ts ← 3 paletas CSS vars (--primary, --secondary)
    src/components/ThemeToggle.tsx

[ ] 3.2 Acessibilidade (20min)
    aria-labels em todos inputs/buttons
    keyboard navigation (Tab entre forms)
    screen reader announcements (toast + status)

[ ] 3.3 Mobile/Responsivo (20min)
    shadcn responsive breakpoints
    Drawer para sidebar mobile
    Table → Cards em mobile

[ ] 3.4 Feedback Visual (20min)
    Skeleton loaders (PENDING)
    Progress bar (mapeamento parcial)
    Toast dismissível
```

**Critério de aceitação:** Lighthouse 95+ (Performance/Accessibility/Best Practices)

---

### **FASE 4: DOCKER + DEPLOY (1h)**
**Objetivo:** Monorepo rodando em container único  
**Milestone:** `docker-compose up` → localhost:8111

```
[ ] 4.1 Dockerfile Multi-stage (30min)
    # Stage 1: Build React
    FROM node:20-alpine AS frontend-build
    WORKDIR /frontend
    COPY frontend/package*.json ./
    RUN npm ci --only=production
    COPY frontend/ ./
    RUN npm run build

    # Stage 2: Backend + Frontend
    FROM python:3.12-slim AS runtime
    COPY backend/ /app/
    COPY --from=frontend-build /frontend/dist /app/frontend/
    WORKDIR /app
    RUN pip install -r requirements.txt
    EXPOSE 8111
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8111"]

[ ] 4.2 docker-compose.yml (15min)
    services:
      app:
        build: .
        ports: ["8111:8111"]
        volumes: ['./data:/app/data']

[ ] 4.3 Backend ajustes (15min)
    main.py: serve frontend/dist em /
    staticfiles: app.mount("/", StaticFiles(directory="frontend"))

[ ] 4.4 Teste Deploy
    docker-compose up --build → SPA completa em localhost:8111
```

**Critério de aceitação:** Docker roda → Todas features funcionais

---

### **FASE 5: TESTES + OTIMIZAÇÃO (30min)**
**Objetivo:** Código robusto e performático  
**Milestone:** Testes passando + bundle otimizado

```
[ ] 5.1 Testes Unitários (15min)
    npm i -D vitest @testing-library/react
    src/hooks/useApi.test.ts
    src/components/LoteForm.test.tsx

[ ] 5.2 Bundle Analysis (10min)
    vite-bundle-visualizer → <60KB gzipped
    vite-plugin-pwa → Offline cache

[ ] 5.3 QA Manual (5min)
    Mobile Chrome DevTools
    Dark mode toggle
    A11y Lighthouse
```

---

## 📈 Métricas de Sucesso

| Métrica | Meta |
|---|---|
| **Tempo Total** | <8h |
| **Lighthouse Score** | 95+ (todas categorias) |
| **Bundle Size** | <60KB gzipped |
| **Tempo de Interação** | <500ms (upload → feedback) |
| **Mobile Responsivo** | 100% (iPhone SE → iPad) |
| **Acessibilidade** | WCAG 2.1 AA |

---

## ⚠️ Dependências Backend (Confirmadas)
```
✅ POST /lancamento_lote_contabil → Protocolo criado
✅ GET /lancamento_lote_contabil?protocolo= → Status + TXT
✅ GET /lancamento_lote_contabil?cnpj= → Lista
✅ GET /pendencias → Cards com entries
✅ POST /pendencias/resolver → Mapear + reprocessar
✅ DELETE /lancamento_lote_contabil/{protocolo} → Cleanup
```

---

## 🎯 Checklist Final Pré-Deploy

```
[x] [FASE 1] Home + Form + Lista funcionando
[x] [FASE 2] Pendências + mapeamento + download
[x] [FASE 3] Dark mode + mobile + a11y
[x] [FASE 4] Docker-compose up → localhost:8111
[x] [FASE 5] Lighthouse 95+ + testes passando
```
