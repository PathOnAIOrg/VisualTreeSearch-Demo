const Footer = () => {
  return (
    <footer className="px-4 py-2 bg-white dark:bg-gray-500 border-t flex justify-end items-center">
      <div className="text-sm text-gray-800 dark:text-gray-400">
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

