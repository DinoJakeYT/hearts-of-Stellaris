# MODLOG: Hearts of Stellaris

## 2026-10-21: first build

**Idea.** Stellaris mechanics inside HOI4, for laughs: ethics, a space program with megastructures and
a Colossus, and the Stellaris endgame crises landing on 1940s Earth.

**Versions.** HOI4 1.19.3.0 (Operation Postern, checksum c01a). Stellaris 4.5.2 (Cygnus). Windows 10,
Steam installs in `C:/Program Files (x86)/Steam/steamapps/common/`.

**Route.** Data mod (Paradox script), the mashup-mods skill's "port the content" pattern: Stellaris
doesn't run; its mechanics are rebuilt as HOI4 decisions, ideas, events and spawned countries. Art and
music are converted from the user's Stellaris install by `tools/import_stellaris_art.py` and never
committed (`.gitignore`).

**Source of truth.** `Hearts of Iron IV/documentation/*.md` (effects, triggers, modifiers, on_actions)
plus vanilla usage. Things confirmed there before use:
- A tag with no states can be given one with `TAG = { transfer_state = X }` and then filled with
  `division_template` + `create_unit` (vanilla: Karelia, `events/AAT_Finland.txt`).
- `on_monthly` runs for every country (ROOT = that country); `on_monthly_TAG` only while TAG exists.
- `on_capitulation`: ROOT is the capitulated country, FROM the winner.
- Dynamic modifiers can read globals (`army_attack_factor = global.x`), used for crisis strength.
- State-targeted decisions with `on_map_mode = map_only` don't flood the decision list.
- `targeted_modifier = { tag = X attack_bonus_against defense_bonus_against }` for Defender of the Galaxy.
- `damage_units = { state = THIS ratio = yes ... }`, `set_building_level = { type level }`,
  `set_state_category = wasteland`, `promote_character` makes a recruited leader the country leader.

**Sizes HOI4 wants** (from vanilla files): report event 210x176, news event 397x153, idea 60x68,
decision icon 32x32, category icon ~52x40, category picture 114x101, leader 156x210, flags 82x52 / 41x26 /
10x7 TGA, music album art 304x120 (two 152x120 frames). Stellaris event pictures are 450x150, so the
converter scales and centre-crops. Uncompressed 32-bit BGRA DDS is written by hand (vanilla event
pictures use the same format).

**Stellaris sources used.** `gfx/event_pictures/*.dds`, `gfx/interface/icons/{ethics,ascension_perks,
megastructures,relics,technologies,governments/authorities}`, `flags/special/{the_swarm,
extradimensional_01,ai_01}.dds`, `music/*.ogg`. All load with Pillow 12.1.1.

**Verified so far.**
- `tools/check_mod.py`: 25 scripts, 2 gfx/gui, 430 loc keys, 0 errors, 0 warnings. It caught 4 out of
  4 planted mistakes (unknown sprite, unfired event id, missing loc key, misspelled effect).
- `tools/import_stellaris_art.py`: 163 sprites and 30 tracks, nothing missing; contact sheets looked
  right (ideas, decision icons, portraits, flags, event crops).

## 2026-10-22: first runs in HOI4

Enabled only this mod via `dlc_load.json` (backed up and restored afterwards), started `hoi4.exe`
directly, and diffed `logs/error.log` against the previous run's log to separate vanilla noise.
- Run 1 (main menu, history executed): 3 problems, all fixed.
  - `desc` directly inside a game rule is an "Unexpected token" (only name/group/icon/required_dlc and
    options are allowed there; options keep their desc).
  - `recruit_character` outside history files is rejected ("should only happen in game/history
    files"). It's now in each crisis tag's history file, and the spawn effects keep `promote_character`.
- Run 2: main menu clean. A single-player game was then started in that window and ran to
  24 Feb 1936, which showed `on_startup` has **no scope**: calling a scripted effect straight from it
  is "Invalid Scope, provided: None", so the ethics events and crisis setup never ran. Fixed by
  calling it inside `random_country = { }`. `on_monthly` fired on 1 Feb with no errors.
- `tools/check_mod.py` now checks all three of these and catches each when planted.

**Not verified yet.** A new game with the on_startup fix. The game's `error.log`
(`Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`) is the next oracle, then a
`-debug` run with the two debug decisions:
1. ethics event at start; AI countries show an ethic spirit;
2. space program decisions, an anomaly, a megastructure;
3. `[Debug] Skip to the Colossus`, then fire at an enemy state from the map;
4. `[Debug] Summon the Endgame Crisis` for each crisis type (game rule): country appears with its
   flag and leader, declares war, divisions spawn, monthly waves, capitulation cleanup.

**Open questions / risks to check in game.**
- `for_loop_effect` with `end = <temp variable>` (crisis division counts).
- Whether `create_unit` in a state scope spawns in that state or anywhere the owner holds.
- One `declare_war_on` per country makes ~60 separate wars; check the performance and the war UI.
- `add_manpower` with a huge negative value in state scope (World Cracker / Neutron Sweep).
- Major news events fired from one country's scope: every country gets its own copy, so option
  triggers use flags and tags, not event targets.
