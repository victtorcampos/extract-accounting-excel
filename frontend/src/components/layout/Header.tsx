import { Link, useLocation } from "react-router-dom";
import { Building2, FileWarning, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Lançamento" },
  { to: "/pendencias", label: "Pendências" },
];

export function Header() {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center gap-6">
        <div className="flex items-center gap-2 font-semibold">
          <Building2 className="h-5 w-5 text-primary" />
          <span className="hidden sm:inline">Contabilidade Sorriso</span>
        </div>

        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                location.pathname === to
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground"
              )}
            >
              {to === "/pendencias" && <FileWarning className="h-4 w-4" />}
              {label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Alternar tema"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </div>
    </header>
  );
}
