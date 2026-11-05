import { createContext, useContext, useState } from 'react'

const Ctx = createContext({ selectedLocation: null, setSelectedLocation: () => {} })

export function LocationProvider({ children }) {
  const [selectedLocation, setSelectedLocation] = useState(null)
  return <Ctx.Provider value={{ selectedLocation, setSelectedLocation }}>{children}</Ctx.Provider>
}

export const useSelectedLocation = () => useContext(Ctx)
