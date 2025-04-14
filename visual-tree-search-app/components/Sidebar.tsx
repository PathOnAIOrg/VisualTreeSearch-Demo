import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, LayoutDashboard, Network, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState } from 'react';

const Sidebar = () => {
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

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
    {
      name: 'D3 Playground',
      href: '/d3-playground',
      icon: Network
    },
    {
      name: 'BFS/DFS',
      href: '/SimpleSearchAgent',
      icon: Search
    },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return router.pathname === '/';
    }
    return router.pathname.startsWith(path);
  };

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };
  
  return (
    <div className={`h-full min-h-screen ${collapsed ? 'w-16' : 'w-64'} border-r transition-all duration-300 relative`}>
      <div className="space-y-4 py-4">
        <div className={`px-4 py-2 flex ${collapsed ? 'justify-center' : 'justify-between'} items-center`}>
          {!collapsed && <h2 className="text-xl font-semibold tracking-tight">VisualTreeSearch</h2>}
          <Button 
            variant="ghost" 
            size="icon" 
            className="absolute -right-3 top-5 bg-white dark:bg-gray-800 border shadow-sm z-10"
            onClick={toggleSidebar}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
        <ScrollArea className="h-[calc(100vh-8rem)]">
          <nav className="grid gap-1 px-2">
            {menuItems.map((item) => (
              <Button
                key={item.name}
                asChild
                variant={isActive(item.href) ? "secondary" : "ghost"}
                className={`w-full ${collapsed ? 'justify-center' : 'justify-start'}`}
                title={collapsed ? item.name : ''}
              >
                <Link href={item.href}>
                  <item.icon className={`${collapsed ? '' : 'mr-2'} h-4 w-4`} />
                  {!collapsed && item.name}
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