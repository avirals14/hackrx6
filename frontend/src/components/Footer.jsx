export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-16">
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-sm text-gray-600">
            © 2024 PolicyLens. Built with Next.js and FastAPI.
          </div>
          <div className="flex space-x-6 text-sm">
            <a 
              href="#" 
              className="text-gray-600 hover:text-blue-600 transition-colors duration-200"
            >
              Privacy
            </a>
            <a 
              href="#" 
              className="text-gray-600 hover:text-blue-600 transition-colors duration-200"
            >
              Terms
            </a>
            <a 
              href="#" 
              className="text-gray-600 hover:text-blue-600 transition-colors duration-200"
            >
              Support
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
} 