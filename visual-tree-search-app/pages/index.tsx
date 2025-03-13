import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-100 dark:from-gray-900 dark:to-black p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mt-16 text-center">
          <h3 className="text-xl md:text-2xl font-bold text-gray-800 dark:text-white mb-4">
            VisualTreeSearch Playground
          </h3>
          <p className="text-lg text-gray-700 dark:text-gray-300 max-w-3xl mx-auto">
            Welcome to the playground for <span className="font-semibold">VisualTreeSearch: An Intuitive Interface for Understanding Web Agent Decision Processes</span>. 
            This space allows you to explore and interact with the demo presented in the paper.
          </p>
        </div>

        <div className="mt-16 space-y-8">
          <h2 className="text-2xl md:text-3xl font-bold text-center text-gray-800 dark:text-white mb-8">
            Project Architecture
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-500 dark:text-blue-400">Frontend</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li><span className="font-medium">Framework:</span> Next.js</li>
                  <li><span className="font-medium">UI Components:</span> Shadcn</li>
                  <li><span className="font-medium">Styling:</span> Tailwind CSS</li>
                  <li><span className="font-medium">Deployment:</span> Vercel</li>
                </ul>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-500 dark:text-blue-400">Backend</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li><span className="font-medium">Framework:</span> FastAPI</li>
                  <li><span className="font-medium">Deployment:</span> AWS ECS (Elastic Container Service)</li>
                </ul>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-500 dark:text-blue-400">Infrastructure</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li><span className="font-medium">DNS Management:</span> GoDaddy</li>
                  <li><span className="font-medium">SSL Certificates:</span> AWS Certificate Manager</li>
                </ul>
              </CardContent>
            </Card>
          </div>
          
          <p className="text-center text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mt-6">
            This architecture combines modern frontend technologies with a Python-based backend, 
            using cloud services for deployment and security.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
