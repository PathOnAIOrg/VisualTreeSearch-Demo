import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import Link from "next/link";

const Header = () => {
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-20 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-14 relative">
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <h1 className="text-lg font-semibold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent whitespace-nowrap">
              VisualTreeSearch
            </h1>
          </Link>
        </div>
        <div className="absolute right-0 top-1/2 -translate-y-1/2 pr-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="h-8 w-8"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;