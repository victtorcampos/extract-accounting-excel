import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Toaster } from "@/components/ui/toaster";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container py-6">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
