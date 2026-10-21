# Hearts of Stellaris

Stellaris, crammed into Hearts of Iron IV. Pick a Stellaris ethic in 1936, build a space program, wrap
the Sun in a Dyson Sphere, crack your enemies' states with a Colossus, and then survive a Stellaris
endgame crisis landing on Earth in the middle of World War II.

Built for HOI4 1.19.3 ("Operation Postern"). It needs no DLC. It uses art and music from **your own
Stellaris install** (4.x), converted on your PC; the mod ships none of it.

## What's in it

**Ethics.** At game start a meteorite drops the *Stellaris Codex* on your capital, and you choose an
ethic: Fanatic Militarist, Pacifist, Materialist, Spiritualist, Xenophobe or Xenophile, or a Gestalt
Consciousness (Machine Intelligence or Hive Mind). Every AI country gets one that suits its ideology
(game rule). Players can change it once a year with *Embrace a New Ethos*.

**The Final Frontier** (decision category):
- Launch a Satellite, build an Orbital Spaceport, Colonise the Moon, research Jump Drives.
- Launch Science Ships to survey anomalies: Gary the Space Whale, a Precursor cache, a sentient asteroid,
  a towel that says DON'T PANIC, grey goo, a friendly amoeba, a derelict warship, a whispering temple,
  the Horizon Signal, an Ether Drake, and a really interesting rock.
- Nine megastructures, one at a time, each using civilian factories while it's built: Dyson Sphere,
  Ring World, Science Nexus (+1 research slot), Sentry Array, Matter Decompressor, Mega Art
  Installation, Strategic Coordination Center, Mega Shipyard, Gateway Network.
- Three megastructures unlock the **Colossus**. Pick its weapon (World Cracker, Neutron Sweep or Nanobot
  Diffuser), then open the decisions map mode and click any enemy-held state to fire. 60-day recharge.
  Everyone hates you for it.
- With a Colossus, a great power can **Become the Crisis**, then build the **Aetherophasic Engine**:
  every AI great power declares war on you, and if you survive 540 days, every country at war with you
  is annexed.

**Endgame crises.** In 1942 (game rule) the world gets a warning, and about 75 days later one of these
arrives as a new country at war with everyone on Earth:
- **The Prethoryn Scourge** lands on three coasts and grows with every state it takes.
- **The Unbidden** come through a portal inside a great power. Retake the portal state to cut off their
  reinforcements and cripple them.
- **The Contingency** seizes four sterilization hubs inside great powers, and every Machine Intelligence
  loses a state to its own robots. Retake every hub to break it.

Every country gets the *Defender of the Galaxy* decision (+50% attack and defence against the crisis).
When the crisis capitulates its land goes back to whoever has cores on it or holds it, and everyone who
fought it gets *We Survived the End of the World*.

**Stellaris radio station.** The Stellaris soundtrack shows up in the HOI4 music player.

## Game rules (Hearts of Stellaris group)

| Rule | Options |
|---|---|
| Endgame Crisis | Random (default), Prethoryn Scourge, Extradimensional Invaders, The Contingency, None |
| Crisis Year | 1938, 1940, 1942 (default), 1945, 1948 |
| Crisis Strength | 0.5x, 1x (default), 2x, 5x, 10x, 25x |
| AI Ethics | Every Country (default), Great Powers Only, None |

With Random, building Jump Drives makes the Unbidden three times as likely, and a great power with a
Machine Intelligence does the same for the Contingency. That's how it works in Stellaris too.

## Install

1. The mod lives in `Documents/Paradox Interactive/Hearts of Iron IV/mod/hearts_of_stellaris`, with
   `hearts_of_stellaris.mod` next to it.
2. Build the art and music from your Stellaris install (Python 3.10+ and Pillow):

   ```
   python tools/import_stellaris_art.py
   ```

   Pass `--stellaris "<path>"` if Stellaris isn't in the default Steam folder, or `--no-music` to skip
   the soundtrack (about 420 MB).
3. In the Paradox launcher, add **Hearts of Stellaris** to a playset and start a new game. Existing
   saves won't get the ethics or the crisis.

## Testing it quickly

Start HOI4 with `-debug` (Steam: right-click, Properties, Launch Options). Two decisions then show up
in The Final Frontier: **[Debug] Summon the Endgame Crisis** and **[Debug] Skip to the Colossus**.

`python tools/check_mod.py` checks braces, sprites, events, localisation and every script keyword
against HOI4's own documentation. It doesn't run the game.

## Credits

Built with AI: written by Claude Code (Anthropic) using the
[universal-modder](https://github.com/rehan-remade/universal-modder) skills. Art, music and names come
from Stellaris by Paradox Development Studio, read from your own copy. Don't redistribute the converted
files in `gfx/` or `music/`; share the mod and the converter instead.
