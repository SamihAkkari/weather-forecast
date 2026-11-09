import { Link } from '../../router-compat'

function Navbar() {
  return (
    <nav className="sticky top-0 z-[1000] border-b border-border glass">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <span className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-primary text-lg shadow-[var(--shadow-glow)] transition-transform group-hover:rotate-12">
            ⛅
          </span>
          <span className="font-display text-lg font-semibold text-foreground">
            Meteo<span className="text-primary">App</span>
          </span>
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
