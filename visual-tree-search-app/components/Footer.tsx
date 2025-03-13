const Footer = () => {
  return (
    <footer className="relative px-4 py-6 bg-white dark:bg-gray-500 overflow-hidden">
      {/* Background Text */}
      <div
        className="absolute inset-0 flex items-center justify-center text-6xl font-bold text-gray-200 dark:text-gray-700"
        style={{
          zIndex: -1,
          opacity: 0.1, // Subtle background text
          whiteSpace: "nowrap", // Prevent text wrapping
        }}
      >
        © {new Date().getFullYear()} - Built with NextJS
      </div>

      {/* Foreground Content */}
      <div
        className="text-center text-sm text-gray-800 dark:text-gray-400"
        style={{
          marginTop: `1.3rem`,
          marginRight: `2.2rem`,
          paddingBottom: "0.3rem",
          float: "right",
        }}
      >
        © {new Date().getFullYear()}, Built with
        {` `}
        <a
          href="https://nextjs.org/"
          className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-600"
        >
          NextJS
        </a>
      </div>
    </footer>
  );
};

export default Footer;

