# Foliage Pass-Through: technical notes

Steam build 25480438 (game.dll SHA-256 `2E2C3B7C...`, EXE `F5FEE03D...`). Addresses are relative to game.dll unless
marked otherwise.

## Why ordnance explodes in trees

Every projectile is simulated by one projectile system (`0x13AB0E0` issues the rays, `0x13AC1F0` reads their hits,
both inside the world update `0xAB5000`). Each step it casts a ray from the projectile's position along its flight,
with the collision check that its settings row names: `ProjectileInfo.raycast_template` (offset `+0xF4`), read from
the row every step.

The checks are created once per mission (`0x175BE60`) from named collision queries of the game's physics settings:

| Template | Query | Used by (vanilla) |
| --- | --- | --- |
| 0 | `damage_query` | almost every projectile: every bomb, shell, rocket, missile, grenade round and bullet |
| 1 | `damage_query`, back faces enabled | 35 types, mostly enemy |
| 2 | `damage_no_foliage_query` | plasma bolts and lasers (20 types) |

In the game's collision layer table (the global `havok_physics_properties`) `damage_query` and
`damage_no_foliage_query` collide with the same layers but one: layer 27, `foliage`. This was read from the resource
and from the live world collision filter (on the ship).

Trees and bushes are built from two kinds of collision shapes (the `physics` resources of the 295 speedtree models
that have collision):

| Material | Layer | Shapes | What |
| --- | --- | --- | --- |
| `foliage_gameplay` | `foliage` | 482 | canopies; bushes are made of these only |
| `wood`, `wood_rift`, `flesh_rift`, `flesh`, `metal`, ... | `default` | 1,488 | trunks and limbs |
| `wood` | `destructible` | 83 | breakable parts |

So a template-0 shot hits a canopy shape and, if it explodes on impact, detonates in the leaves. With template 2 it
ignores the `foliage` layer and still hits trunks, limbs, the ground (`terrain`), buildings and units.

## The change

`src/foliage_pass_through.lua` sets `raycast_template` from 0 to 2 in 99 rows of the loaded projectile settings,
once per game session:

- The rows: the settings loader `0x11EC5A0` keeps the loaded `generated_projectile_settings` buffer at `+0x348E2F8`
  and a pointer per projectile type at `+0x37C7670` (351 slots). The rows are 0x110 bytes in committed, private,
  read-write memory, as the stratagem settings Better Stratagem Bounce changes.
- Which rows (`src/foliage_targets.lua`): every row on template 0 with an impact explosion (`+0x90`) and a
  player-facing name (its name, upper-case name or short name), except enemy rows that reuse a player label (the
  Automaton artillery shell). 23 unnamed rows (acid, Illuminate weapons, bug artillery and similar) and the other
  enemy rows stay vanilla. The list comes from a read of the live game; each entry is `{type, name hash, impact
  explosion, label}`.
- Checks before any write: the EXE and game.dll hashes; for every row, its type field, name hash and impact
  explosion equal the list's and its template is 0 or 2. Anything else refuses the whole change and writes nothing.
- The write: one `write_batch` over the span of all 99 template fields (one page check), then each field is read
  back. If only some writes land, the landed ones are put back before the mod disables itself.
- When the settings are not loaded yet, a self-removing update hook retries (one read per frame) for up to 600 s of
  game time. In every test the settings were already loaded when the loader started the mod.
- At shutdown one read per row logs how many still use template 2.

The 99 types, by their in-game name (type numbers of build 25480438): 100kg Bomb (130, 170); 100kg Bomb Mk2 (338);
100kg Bomb Mk3 (116); 10g Fragmentation (322); 110mm Airburst Cannon Round (158) and Mk2 (26); 110mm E.M.S. Cannon
Round (74), Mk2 (29), Mk3 (208); 110mm Gas Cannon Round (197); 110mm Standard Rocket (82, 146) and Mk2 (6); 120mm HE
Cannon Round (13, 137, 194, 234, 238); 15x100mm High Explosive (40, 206); 15x100mm Standard Rocket (202); 200kg Bomb
(192); 20mm APHET Rounds (115); 20mm Flak Rounds (224, 284, 312); 20mm HE Cannon (175); 23mm HE Cannon (16, 72, 75,
77); 30mm APHE Cannon (261); 380mm HE Cannon Round (80, 84, 93, 100, 216, 266) and Mk2 (182); 40mm APHE Cannon (120);
40mm Flak Cannon (294); 40mm HE Grenade (280, 297); 40mm HE Mortar (346); 40mm HEAT Grenade (85, 263); 40mm
Incendiary (90); 40mm Proximity Grenade (161); 500kg Bomb (239), Mk2 (151), Mk3 (293); 66mm Missile (245) and Mk2
(272); 70mm Laser-Guided Missile (128) and Mk2 (349); 70mm Standard Rocket (304, 320); 75mm HEAT Grenade (31, 110,
132); 85mm HEAT Grenade (153) and Mk2 (231); 85mm High-Explosive Grenade (36) and Mk2 (350); Anti-Air Missile (298);
Cluster Bomb (78, 96, 131, 210, 233); exploding crossbow bolt (249); Homing Anti-Air Missile (336); Homing Ground
Missile (225) and Mk2 (220); Large Plasma Bolt (17); Napalm Bomb (313), Mk2 (141), Mk3 (162); Nuke (66); orbital
illumination shot (190); orbital smoke shell (247); SAM site missile (203); SEAF Artillery shells (10, 71, 92, 99,
145, 339); Shrapnel (11, 187); Small Plasma Bolt (70, 341); and the weapon-mode rounds named Artillery (330), Burst
(43), Guided (152), Non-Guided (127), HE MK2 (214) and STUN (67).

The simulation switches a projectile to a ground-only query (`climbable_query`) when one of its instance flags is
set; that flag probably mirrors the settings' "hit only ground" flag of the cluster bomblets, in which case the
change makes no difference to them. Not verified.

## Proximity fuses

Proximity-fused projectiles (flak, the 40 mm proximity grenade, the Stinger) also check their surroundings with a
named query (`+0xF8`), `damage_query` for most of them. The mod does not change it, so those fuses can still trigger
near leaves.

## Multiplayer

Clients spawn their own copy of a projectile when the shooter's game tells them a shot was fired (see the SEAF
Artillery `rpc_fire_single_round` path), so each game simulates the flight with its own settings. A player without
the mod can see a shot burst in a canopy that passed through it for a player with the mod. Which game applies the
explosion's damage in a mixed squad is not established.

## Cost

| Path | Calls | In-game cost |
| --- | --- | --- |
| Load (once) | 1 index read, 99 row reads, 1 page check, 99 writes, 99 read-backs | unmeasured in game |
| Waiting for the settings (never needed so far) | 1 read per frame | ~1-2 us per frame |
| Every frame after the change | none (no update hook) | 0 |
| Shutdown | 99 reads | once |

The offline suite pins these counts (`tests/test_mod.lua`, `tests/frame_budget.lua`): the load-time change makes 200
reads, one page check and one batch write, and a frame after it makes no call. The change runs once and adds no
compiled code that stays.

## Tests and live checks

- `tests/test_mod.lua` (10 tests, in LuaJIT and in the game's `lua51.dll`, with the shared runtime's hostile-VM
  helpers): the real list; the change and its exact call budget; waiting for the settings; rows already changed;
  every mismatch refusing the whole change; a partial write put back; an unsupported build; the shutdown line.
- `tests/compile_entry.lua`, `tests/test_entry.lua`: the assembled entry compiles and refuses outside the game.
- Live (test harness, 2026-10-16): on the ship the change was made at load; a read from outside the game found all 99
  rows on template 2 and every other row as before; it held to shutdown. In four solo missions it held from load to
  quit, and the mission's query handles were found (`damage_no_foliage_query` is handle `0x80000003`).
- Not tested yet: shots into trees in play, a squad with mixed installs, cost in real play.

## Game updates

The build check refuses any other game.dll or EXE. The row numbers, name hashes and offsets are specific to build
25480438; a new build needs a fresh read of the projectile settings.
