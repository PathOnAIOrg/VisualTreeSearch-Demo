import Link from 'next/link';
import { useRouter } from 'next/router';
import { Home, LayoutDashboard, Network, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState, useEffect } from 'react';

const Sidebar = () => {
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkScreenSize = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      // Only collapse when switching from large to small screen
      if (mobile && !isMobile) {
        setCollapsed(true);
        document.documentElement.style.setProperty('--sidebar-width', '3.5rem');
      }
      // Auto expand when switching from small to large screen
      if (!mobile && isMobile) {
        setCollapsed(false);
        document.documentElement.style.setProperty('--sidebar-width', '14rem');
      }
    };

    // Set initial sidebar width
    document.documentElement.style.setProperty('--sidebar-width', collapsed ? '3.5rem' : '14rem');

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, [isMobile, collapsed]);

  const menuItems = [
    {
      name: 'Home',
      href: '/',
      icon: Home
    },
    {
      name: 'MCTS',
      href: '/MCTSAgent',
      icon: LayoutDashboard
    },
    {
      name: 'LATS',
      href: '/LATSAgent',
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
    document.documentElement.style.setProperty('--sidebar-width', collapsed ? '3.5rem' : '14rem');
  };
  
  return (
    <div className={`fixed top-0 left-0 z-30 h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out ${
      collapsed ? 'w-14' : 'w-56'
    }`}>
      <div className="flex flex-col h-full">
        <div className={`px-3 py-4 flex ${collapsed ? 'justify-center' : 'justify-between'} items-center`}>
          {!collapsed && <h2 className="text-lg font-semibold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">VisualTreeSearch</h2>}
          <Button 
            variant="outline" 
            size="icon" 
            className="absolute -right-3 top-5 rounded-full w-6 h-6 bg-background border-sidebar-border shadow-md flex items-center justify-center p-0 hover:bg-primary/5"
            onClick={toggleSidebar}
          >
            {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
          </Button>
        </div>
        
        <div className="px-2">
          <div className={`h-px w-full bg-gradient-to-r from-transparent via-sidebar-border to-transparent opacity-70`}></div>
        </div>
        
        <ScrollArea className="flex-1 py-3">
          <nav className="grid gap-1 px-2">
            {menuItems.map((item) => {
              const active = isActive(item.href);
              return (
                <Button
                  key={item.name}
                  asChild
                  variant={active ? "secondary" : "ghost"}
                  className={`w-full group relative px-2 py-1.5 hover:bg-sidebar-hover ${
                    collapsed ? 'justify-center' : 'justify-start'
                  } ${
                    active ? 'font-medium' : 'font-normal'
                  } ${
                    active ? 'bg-sidebar-hover text-primary' : 'text-sidebar-foreground'
                  }`}
                  title={collapsed ? item.name : ''}
                >
                  <Link href={item.href} className="flex items-center">
                    <item.icon className={`${collapsed ? 'h-4 w-4' : 'mr-2 h-4 w-4'} ${active ? 'text-primary' : 'text-muted-foreground group-hover:text-sidebar-foreground'}`} />
                    {!collapsed && <span className="text-sm">{item.name}</span>}
                    {active && !collapsed && <span className="absolute right-2 w-1 h-1 rounded-full bg-primary"></span>}
                  </Link>
                </Button>
              );
            })}
          </nav>
        </ScrollArea>
        
        <div className="mt-auto px-2 pb-3">
          <div className={`h-px w-full bg-gradient-to-r from-transparent via-sidebar-border to-transparent opacity-70 mb-2`}></div>
          {!collapsed && (
            <div className="text-xs text-center opacity-70 text-muted-foreground">
              VisualTreeSearch Demo
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;