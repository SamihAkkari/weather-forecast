// Thin adapter so the original pages keep their navigation calls on TanStack Router.
import {
  Link as TLink,
  useNavigate as tUseNavigate,
  useParams as tUseParams,
  useLocation as tUseLocation,
  useRouter,
} from '@tanstack/react-router'

export function Link({ to, ...props }) {
  const path = to.startsWith('/') ? to : `/${to}`
  return <TLink to={path} {...props} />
}

export function useNavigate() {
  const navigate = tUseNavigate()
  const router = useRouter()
  return (to, opts = {}) => {
    if (typeof to === 'number') return router.history.go(to)
    return navigate({ to, state: (prev) => ({ ...prev, ...(opts.state || {}) }) })
  }
}

export function useParams() {
  return tUseParams({ strict: false })
}

export function useLocation() {
  return tUseLocation()
}
