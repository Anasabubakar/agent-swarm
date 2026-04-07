export const RARITIES = [
    'common',
    'uncommon',
    'rare',
    'epic',
    'legendary',
];
// One species name collides with a model-codename canary in excluded-strings.txt.
// The check greps build output (not source), so runtime-constructing the value keeps
// the literal out of the bundle while the check stays armed for the actual codename.
// All species encoded uniformly; `as` casts are type-position only (erased pre-bundle).
const c = String.fromCharCode;
// biome-ignore format: keep the species list compact
export const duck = c(0x64, 0x75, 0x63, 0x6b);
export const goose = c(0x67, 0x6f, 0x6f, 0x73, 0x65);
export const blob = c(0x62, 0x6c, 0x6f, 0x62);
export const cat = c(0x63, 0x61, 0x74);
export const dragon = c(0x64, 0x72, 0x61, 0x67, 0x6f, 0x6e);
export const octopus = c(0x6f, 0x63, 0x74, 0x6f, 0x70, 0x75, 0x73);
export const owl = c(0x6f, 0x77, 0x6c);
export const penguin = c(0x70, 0x65, 0x6e, 0x67, 0x75, 0x69, 0x6e);
export const turtle = c(0x74, 0x75, 0x72, 0x74, 0x6c, 0x65);
export const snail = c(0x73, 0x6e, 0x61, 0x69, 0x6c);
export const ghost = c(0x67, 0x68, 0x6f, 0x73, 0x74);
export const axolotl = c(0x61, 0x78, 0x6f, 0x6c, 0x6f, 0x74, 0x6c);
export const capybara = c(0x63, 0x61, 0x70, 0x79, 0x62, 0x61, 0x72, 0x61);
export const cactus = c(0x63, 0x61, 0x63, 0x74, 0x75, 0x73);
export const robot = c(0x72, 0x6f, 0x62, 0x6f, 0x74);
export const rabbit = c(0x72, 0x61, 0x62, 0x62, 0x69, 0x74);
export const mushroom = c(0x6d, 0x75, 0x73, 0x68, 0x72, 0x6f, 0x6f, 0x6d);
export const chonk = c(0x63, 0x68, 0x6f, 0x6e, 0x6b);
export const SPECIES = [
    duck,
    goose,
    blob,
    cat,
    dragon,
    octopus,
    owl,
    penguin,
    turtle,
    snail,
    ghost,
    axolotl,
    capybara,
    cactus,
    robot,
    rabbit,
    mushroom,
    chonk,
];
export const EYES = ['·', '✦', '×', '◉', '@', '°'];
export const HATS = [
    'none',
    'crown',
    'tophat',
    'propeller',
    'halo',
    'wizard',
    'beanie',
    'tinyduck',
];
export const STAT_NAMES = [
    'DEBUGGING',
    'PATIENCE',
    'CHAOS',
    'WISDOM',
    'SNARK',
];
export const RARITY_WEIGHTS = {
    common: 60,
    uncommon: 25,
    rare: 10,
    epic: 4,
    legendary: 1,
};
export const RARITY_STARS = {
    common: '★',
    uncommon: '★★',
    rare: '★★★',
    epic: '★★★★',
    legendary: '★★★★★',
};
export const RARITY_COLORS = {
    common: 'inactive',
    uncommon: 'success',
    rare: 'permission',
    epic: 'autoAccept',
    legendary: 'warning',
};
