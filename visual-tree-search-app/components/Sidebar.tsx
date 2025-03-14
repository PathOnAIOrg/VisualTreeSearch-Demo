import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, LayoutDashboard} from 'lucide-react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

const Sidebar = () => {
  const router = useRouter();

  const menuItems = [
    {
      name: 'Home',
      href: '/',
      icon: Home
    },
    {
      name: 'Playground',
      href: '/playground',
      icon: LayoutDashboard
    },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return router.pathname === '/';
    }
    return router.pathname.startsWith(path);
  };
  
  return (
    <div className="h-full min-h-screen w-64 border-r">
      <div className="space-y-4 py-4">
        <div className="px-4 py-2">
          <h2 className="text-xl font-semibold tracking-tight">My Playground</h2>
        </div>
        <ScrollArea className="h-[calc(100vh-8rem)]">
          <nav className="grid gap-1 px-2">
            {menuItems.map((item) => (
              <Button
                key={item.name}
                asChild
                variant={isActive(item.href) ? "secondary" : "ghost"}
                className="w-full justify-start"
              >
                <Link href={item.href}>
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.name}
                </Link>
              </Button>
            ))}
          </nav>
        </ScrollArea>
      </div>
    </div>
  );
};

export default Sidebar;