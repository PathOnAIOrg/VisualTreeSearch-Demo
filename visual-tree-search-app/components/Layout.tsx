import Header from "./Header";
import Footer from "./Footer"; 
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
        <div className="flex flex-col flex-1 min-w-0 ml-14 lg:ml-56 transition-all duration-300">
          <Header />
          <main className="flex-1 p-4 lg:p-6 overflow-auto">
            <div className="h-full w-full max-w-full">
              {children}
            </div>
          </main>
          <Footer />
        </div>
      </div>
    </>
  );
};

export default Layout;