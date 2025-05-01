import Header from "./Header";
import Sidebar from "./Sidebar";
import Head from "next/head";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <>
      <Head>
        <title>Visual Tree Search</title>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </Head>

      <div className="flex min-h-screen bg-gradient-to-b from-background via-background/98 to-background/95 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0 transition-all duration-300" style={{ marginLeft: 'var(--sidebar-width, 3.5rem)' }}>
          <Header />
          <main className="flex-1 px-4 pt-4 pb-2 lg:px-6 lg:pt-6 lg:pb-3 overflow-auto">
            <div className="h-full w-full max-w-full">
              {children}
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default Layout;