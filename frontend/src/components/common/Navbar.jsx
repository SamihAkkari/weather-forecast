
import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="border-b border-gray-100 bg-gray-600">
      <div className="max-w-4xl mx-auto px-8 h-13 flex items-center">
        <Link 
            to="/" 
            className="text-base font-medium text-white">
            ⛅ MeteoApp
        </Link>
      </div>
    </nav>
  )
}

export default Navbar