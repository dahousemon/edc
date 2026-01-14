import { ChatWidget } from '../components/ChatWidget'

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-aurora-50 to-aurora-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-aurora-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Aurora EDC</h1>
                <p className="text-sm text-gray-500">Economic Development Council</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <a href="#" className="text-gray-600 hover:text-aurora-600 transition-colors">
                About Aurora
              </a>
              <a href="#" className="text-gray-600 hover:text-aurora-600 transition-colors">
                Incentives
              </a>
              <a href="#" className="text-gray-600 hover:text-aurora-600 transition-colors">
                Properties
              </a>
              <a href="#" className="text-gray-600 hover:text-aurora-600 transition-colors">
                Contact
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">
            Your AI Business Navigator
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Discover why Aurora, Colorado is the ideal location for your business.
            Ask me about incentives, properties, permits, workforce, and more.
          </p>
        </div>

        {/* Chat widget - embedded full width */}
        <div className="h-[600px]">
          <ChatWidget embedded />
        </div>

        {/* Quick links */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">Tax Incentives</h3>
            <p className="text-sm text-gray-600 mb-3">
              Learn about Enterprise Zone credits, Job Growth incentives, and more.
            </p>
            <a href="#" className="text-sm text-aurora-600 hover:underline">
              Explore incentives →
            </a>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">Available Properties</h3>
            <p className="text-sm text-gray-600 mb-3">
              Browse industrial, office, and retail spaces across Aurora.
            </p>
            <a href="#" className="text-sm text-aurora-600 hover:underline">
              Search properties →
            </a>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">Contact Our Team</h3>
            <p className="text-sm text-gray-600 mb-3">
              Connect directly with Aurora EDC's site selection specialists.
            </p>
            <a href="#" className="text-sm text-aurora-600 hover:underline">
              Get in touch →
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-aurora-600 rounded flex items-center justify-center">
                <span className="text-white font-bold">A</span>
              </div>
              <span className="text-gray-600">
                Aurora Economic Development Council
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span>15151 E. Alameda Parkway, Aurora, CO 80012</span>
              <span>(303) 739-7700</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
