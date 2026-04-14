export const SWARM_BOOT_PHRASES = [
  'Swarm online. Let’s make moves.',
  'Hive mind synced. Time to build.',
  'Agents assembled. Chaos, but productive.',
  'Swarm warmed up. Targets locked.',
  'Collective brain booted. Let’s cook.',
]

export const SWARM_LOADING_PHRASES = [
  'Scouting the code hive…',
  'Dispatching worker agents…',
  'Routing tasks through the swarm…',
  'Stirring the hive brain…',
  'Collecting signal from the colony…',
]

export const SWARM_EXIT_PHRASES = [
  'Swarm dispersing. Ping me when it’s go time.',
  'Hive powering down. Mission clock paused.',
  'Agents clocking out. We run it back soon.',
  'Swarm sleeping with one eye open.',
  'Session sealed. Colony standing by.',
]

function pickRandom<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)] as T
}

let cachedBootPhrase: string | null = null
export function getBootPhrase(): string {
  if (!cachedBootPhrase) cachedBootPhrase = pickRandom(SWARM_BOOT_PHRASES)
  return cachedBootPhrase
}

export function getLoadingPhrase(): string {
  return pickRandom(SWARM_LOADING_PHRASES)
}

export function getExitPhrase(): string {
  return pickRandom(SWARM_EXIT_PHRASES)
}
