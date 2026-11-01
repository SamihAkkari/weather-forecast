import { Link } from '../../router-compat'

const LINKS = [
  // { to: '/viewer', label: 'Viewer' },
  // { to: '/analysis', label: 'Analysis' },
  // { to: '/pv', label: 'Solar' },
]

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
        <div className="flex items-center gap-1">
          {LINKS.map(l => (
            <Link
              key={l.to}
              to={l.to}
              activeProps={{ className: 'bg-muted text-foreground' }}
              className="px-3.5 py-1.5 rounded-full text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
