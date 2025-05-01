import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Link from "next/link";

const Home = () => {
  return (
    <div className="relative min-h-[calc(100vh-3.5rem)]">
      <div className="relative container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-32">
        {/* Hero Section */}
        <section className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-accent/10 to-primary/10 dark:from-primary/20 dark:via-accent/20 dark:to-primary/20 blur-3xl" />
          <div className="relative">
            <div className="text-center space-y-8">
              <div className="flex justify-center mb-4">
                <svg className="w-16 h-16 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                VisualTreeSearch Playground
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                Welcome to the playground for <span className="text-primary">VisualTreeSearch</span>, an intuitive interface for understanding web agent decision processes. Explore and interact with the demo presented in the paper.
              </p>
              <div className="flex flex-wrap justify-center gap-4 mt-8">
                <a href="#algorithms" className="inline-flex items-center px-6 py-3 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary transition-colors">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  View Algorithms
                </a>
                <a href="#architecture" className="inline-flex items-center px-6 py-3 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent transition-colors">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                  View Architecture
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Algorithm Cards Section */}
        <section id="algorithms" className="space-y-12 max-w-5xl mx-auto">
          <div className="text-center space-y-4">
            <div className="flex justify-center mb-4">
              <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Available Algorithms
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Explore different <span className="text-primary">tree search algorithms</span> and their applications in <span className="text-accent">web agent decision making</span>
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Link href="/MCTSAgent" className="group">
              <div className="card bg-card hover:bg-card/80 border border-card-border p-8 rounded-xl transition-all duration-300 h-full flex flex-col">
                <div className="flex items-center mb-4">
                  <svg className="w-8 h-8 text-primary mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605" />
                  </svg>
                  <h3 className="text-2xl font-semibold text-primary group-hover:text-primary-hover transition-colors">
                    Monte Carlo Tree Search
                  </h3>
                </div>
                <p className="text-muted-foreground mb-6 leading-relaxed flex-grow">
                  A heuristic search algorithm for decision processes, particularly in games and optimization problems.
                </p>
                <div className="flex items-center text-sm text-primary group-hover:text-primary-hover transition-colors">
                  Try MCTS
                  <svg
                    className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </Link>

            <Link href="/LATSAgent" className="group">
              <div className="card bg-card hover:bg-card/80 border border-card-border p-8 rounded-xl transition-all duration-300 h-full flex flex-col">
                <div className="flex items-center mb-4">
                  <svg className="w-8 h-8 text-accent mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                  </svg>
                  <h3 className="text-2xl font-semibold text-accent group-hover:text-accent-hover transition-colors">
                    Look-Ahead Tree Search
                  </h3>
                </div>
                <p className="text-muted-foreground mb-6 leading-relaxed flex-grow">
                  An advanced tree search algorithm that combines look-ahead strategies with efficient pruning techniques.
                </p>
                <div className="flex items-center text-sm text-accent group-hover:text-accent-hover transition-colors">
                  Try LATS
                  <svg
                    className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </Link>

            <Link href="/SimpleSearchAgent" className="group">
              <div className="card bg-card hover:bg-card/80 border border-card-border p-8 rounded-xl transition-all duration-300 h-full flex flex-col">
                <div className="flex items-center mb-4">
                  <svg className="w-8 h-8 text-success mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                  <h3 className="text-2xl font-semibold text-success group-hover:text-success/80 transition-colors">
                    BFS/DFS
                  </h3>
                </div>
                <p className="text-muted-foreground mb-6 leading-relaxed flex-grow">
                  Classic graph traversal algorithms: Breadth-First Search for level-by-level exploration and Depth-First Search for deep path exploration.
                </p>
                <div className="flex items-center text-sm text-success group-hover:text-success/80 transition-colors">
                  Try BFS/DFS
                  <svg
                    className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </div>
            </Link>
          </div>
        </section>

        {/* Architecture Section */}
        <section id="architecture" className="space-y-12 max-w-5xl mx-auto">
          <div className="text-center space-y-4">
            <div className="flex justify-center mb-4">
              <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Project Architecture
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              A modern stack combining <span className="text-primary">powerful frontend</span> technologies with a <span className="text-accent">robust Python backend</span>
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Frontend Card */}
            <Card className="group relative overflow-hidden hover:shadow-lg transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 dark:from-primary/20 dark:to-accent/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <CardTitle className="text-xl font-semibold">
                    Frontend
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4 text-muted-foreground">
                  <li className="flex items-center justify-between">
                    <span>Framework</span>
                    <span className="font-medium text-foreground">Next.js</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>UI Library</span>
                    <span className="font-medium text-foreground">Tailwind CSS</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>State Management</span>
                    <span className="font-medium text-foreground">React Hooks</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Styling</span>
                    <span className="font-medium text-foreground">CSS Modules</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
            
            {/* Backend Card */}
            <Card className="group relative overflow-hidden hover:shadow-lg transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-accent/10 to-primary/10 dark:from-accent/20 dark:to-primary/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                  </svg>
                  <CardTitle className="text-xl font-semibold">
                    Backend
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4 text-muted-foreground">
                  <li className="flex items-center justify-between">
                    <span>Framework</span>
                    <span className="font-medium text-foreground">FastAPI</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Deployment</span>
                    <span className="font-medium text-foreground">AWS ECS</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Container</span>
                    <span className="font-medium text-foreground">Docker</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Runtime</span>
                    <span className="font-medium text-foreground">Python 3.9+</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
            
            {/* Infrastructure Card */}
            <Card className="group relative overflow-hidden hover:shadow-lg transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-accent/10 dark:from-primary/20 dark:to-accent/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <svg className="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                  </svg>
                  <CardTitle className="text-xl font-semibold">
                    Infrastructure
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4 text-muted-foreground">
                  <li className="flex items-center justify-between">
                    <span>DNS Management</span>
                    <span className="font-medium text-foreground">GoDaddy</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>SSL Certificates</span>
                    <span className="font-medium text-foreground">AWS ACM</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>CDN</span>
                    <span className="font-medium text-foreground">Cloudflare</span>
                  </li>
                  <li className="flex items-center justify-between">
                    <span>Monitoring</span>
                    <span className="font-medium text-foreground">AWS CloudWatch</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
          
          <div className="text-center mt-12">
            <p className="text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              This architecture combines <span className="text-primary">modern frontend technologies</span> with a <span className="text-accent">Python-based backend</span>, using cloud services for deployment and security.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Home;
