import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/lancamento_lote_contabil": "http://localhost:8111",
      "/pendencias": "http://localhost:8111",
    },
  },
});
