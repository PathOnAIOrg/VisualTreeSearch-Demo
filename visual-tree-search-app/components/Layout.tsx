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
        <title>NextJS Project</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex flex-col min-h-screen">
        <Header />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-6">
            {children}
          </main>
        </div>
        <Footer />
      </div>
    </>
  );
};

export default Layout;