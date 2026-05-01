export type Provider = {
  id: string
  name: string
  color: string
  description: string
  permissions: string[]
}

export const PROVIDERS: Provider[] = [
  {
    id: "netflix",
    name: "Netflix",
    color: "#E50914",
    description: "Movies, series, and Netflix originals",
    permissions: [
      "View your watch history",
      "Access your watchlist",
      "Resume playback from any device",
    ],
  },
  {
    id: "hulu",
    name: "Hulu",
    color: "#1CE783",
    description: "Live TV, series, and Hulu originals",
    permissions: [
      "View your watch history",
      "Access live TV schedule",
      "Resume playback from any device",
    ],
  },
  {
    id: "disney_plus",
    name: "Disney+",
    color: "#0063E5",
    description: "Disney, Marvel, Star Wars, and Pixar",
    permissions: [
      "View your watch history",
      "Access your watchlist",
      "Resume playback from any device",
    ],
  },
  {
    id: "prime_video",
    name: "Prime Video",
    color: "#00A8E1",
    description: "Amazon originals, movies, and series",
    permissions: [
      "View your watch history",
      "Access your watchlist",
      "Resume playback from any device",
    ],
  },
  {
    id: "apple_tv_plus",
    name: "Apple TV+",
    color: "#A2AAAD",
    description: "Apple original programming",
    permissions: [
      "View your watch history",
      "Resume playback from any device",
    ],
  },
  {
    id: "max",
    name: "Max",
    color: "#531FFF",
    description: "HBO, DC, and Warner Bros content",
    permissions: [
      "View your watch history",
      "Access your watchlist",
      "Resume playback from any device",
    ],
  },
  {
    id: "peacock",
    name: "Peacock",
    color: "#00A0DC",
    description: "NBC, Bravo, and live sports",
    permissions: [
      "View your watch history",
      "Access live TV schedule",
      "Resume playback from any device",
    ],
  },
  {
    id: "paramount_plus",
    name: "Paramount+",
    color: "#0064FF",
    description: "CBS, MTV, and Nickelodeon",
    permissions: [
      "View your watch history",
      "Access your watchlist",
      "Resume playback from any device",
    ],
  },
]

export function getProvider(id: string): Provider | undefined {
  return PROVIDERS.find((p) => p.id === id)
}
