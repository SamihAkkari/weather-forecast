const TZ = 'Europe/Paris'

// "2026-10-30T14:00:00+00:00" -> "15:00" (Paris time, DST handled automatically)
export function formatHourFr(iso) {
  return new Date(iso).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: TZ,
  })
}