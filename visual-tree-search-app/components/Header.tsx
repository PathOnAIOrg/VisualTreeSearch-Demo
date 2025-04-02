import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { HiSun, HiMoon } from "react-icons/hi";

const Header = () => {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header>
      <div className="px-4 py-2 flex justify-end items-center bg-white dark:bg-gray-500 shadow-sm">
        {mounted && (
          theme === "dark" ? (
            <HiSun 
              className="w-6 h-6 text-yellow-500" 
              role="button" 
              onClick={() => setTheme('light')} 
            />
          ) : (
            <HiMoon 
              className="w-6 h-6 text-gray-900" 
              role="button" 
              onClick={() => setTheme('dark')} 
            />
          )
        )}
      </div>
    </header>
  );
};

export default Header;