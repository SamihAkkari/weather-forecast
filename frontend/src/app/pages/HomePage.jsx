import Navbar from '../components/common/Navbar'
import { Link } from '../router-compat'
import heroImg from '../../assets/hero-sky.jpg'

const FEATURES = [
  {
    to: '/viewer',
    icon: '🌤',
    title: 'Weather viewer',
    text: 'Pick any spot in France and see hourly and daily forecasts   temperature, rain, wind and more.',
    cta: 'Open viewer',
  },
  {
    to: '/analysis',
    icon: '📊',
    title: 'Analysis tool',
    text: 'Compare AROME forecasts against real observations, explore history and export CSV files.',
    cta: 'Open analyser',
  },
  // {
  //   to: '/pv',
  //   icon: '☀️',
  //   title: 'Solar production',
  //   text: 'Estimate the hourly output of your solar panels from the local forecast.',
  //   cta: 'Estimate output',
  // },
]

const STATS = [
  { value: '6 min', label: 'Update interval' },
  { value: 'AROME', label: 'Forecast model' },
  { value: '1 km', label: 'Grid resolution' },
]

function HomePage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero */}
      <header className="relative overflow-hidden">
        <img
          src={heroImg}
          alt="French coastline under dramatic clouds at blue hour"
          width={1920}
          height={1088}
          className="absolute inset-0 h-full w-full object-cover opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/50 to-background" />
        <div className="relative max-w-6xl mx-auto px-6 pt-28 pb-36 text-center">
          <span className="animate-rise inline-flex items-center gap-2 rounded-full border border-border glass px-4 py-1.5 text-xs text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            Live data from Météo-France
          </span>
          <h1 className="animate-rise mt-6 text-5xl sm:text-7xl font-bold leading-[1.05] text-gradient [animation-delay:80ms]">
            French weather,<br />from the source.
          </h1>
          <p className="animate-rise mt-6 text-lg text-muted-foreground max-w-xl mx-auto [animation-delay:160ms]">
            Real observations and AROME forecasts, updated continuously.
          </p>
          <div className="animate-rise mt-10 flex flex-wrap justify-center gap-3 [animation-delay:240ms]">
            <Link to="/viewer" className="rounded-full bg-gradient-primary px-7 py-3 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-glow)] transition-transform hover:scale-105">
              Check the forecast →
            </Link>
            <Link to="/analysis" className="rounded-full border border-border glass px-7 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/50">
              Explore analysis
            </Link>
          </div>
        </div>
      </header>

      {/* Cards */}
      <main className="relative max-w-6xl mx-auto px-6 -mt-20 pb-20">
        <div className="grid gap-5 md:grid-cols-2">
          {FEATURES.map((f, i) => (
            <Link
              key={f.to}
              to={f.to}
              style={{ animationDelay: `${300 + i * 90}ms` }}
              className="animate-rise group glass lift block rounded-3xl border border-border p-7"
            >
              <div className="w-12 h-12 rounded-2xl bg-muted grid place-items-center text-2xl mb-5 transition-transform group-hover:scale-110 group-hover:-rotate-6">
                {f.icon}
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-2">{f.title}</h2>
              <p className="text-sm text-muted-foreground leading-relaxed mb-6">{f.text}</p>
              <span className="text-sm font-semibold text-primary inline-flex items-center gap-1">
                {f.cta}
                <span className="transition-transform group-hover:translate-x-1">→</span>
              </span>
            </Link>
          ))}
        </div>

        {/* <div className="mt-10 grid grid-cols-3 gap-5">
          {STATS.map(s => (
            <div key={s.label} className="text-center rounded-2xl border border-border py-6">
              <p className="font-display text-2xl sm:text-3xl font-semibold text-gradient">{s.value}</p>
              <p className="mt-1 text-xs uppercase tracking-widest text-subtle">{s.label}</p>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-subtle mt-14">
          Data source: Météo-France · Updated every 6 minutes
        </p> */}
      </main>
    </div>
  )
}

export default HomePage
