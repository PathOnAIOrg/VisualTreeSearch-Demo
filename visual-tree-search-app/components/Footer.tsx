const Footer = () => {
  return (
    <footer className="w-full">
      <div className="flex h-12 items-center justify-end px-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>© 2025 VisualTreeSearch</span>
          <span className="hidden md:inline">•</span>
          <span className="hidden md:inline">All rights reserved</span>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

