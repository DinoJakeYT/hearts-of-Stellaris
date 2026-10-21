#!/usr/bin/env python3
"""Build Hearts of Stellaris's art and music from your own Stellaris install.

The mod ships no Stellaris files. This script reads them from the Stellaris folder on this PC and writes
HOI4-sized copies into the mod:

  gfx/event_pictures/hos_*.dds          report events (210x176) and news events (397x153)
  gfx/interface/ideas/hos_*.dds         national spirits (60x68)
  gfx/interface/decisions/hos_*.dds     decision icons (32x32), category icons and pictures
  gfx/leaders/hos/*.dds                 crisis leader portraits (156x210)
  gfx/flags/{,medium/,small/}TAG.tga    crisis flags (82x52, 41x26, 10x7)
  gfx/interface/topbar/musicplayer/     the Stellaris radio station's album art
  music/stellaris/*.ogg + .asset/.txt   the Stellaris soundtrack as a HOI4 radio station
  interface/hos_art.gfx                 the sprites for all of the above

Usage (from anywhere; Python 3.10+ with Pillow):
  python import_stellaris_art.py
  python import_stellaris_art.py --stellaris "D:/SteamLibrary/steamapps/common/Stellaris" --no-music
"""
import argparse
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

MOD = Path(__file__).resolve().parent.parent
DEFAULT_STELLARIS = Path("C:/Program Files (x86)/Steam/steamapps/common/Stellaris")

# key -> Stellaris gfx/event_pictures/<name>.dds. Each key becomes GFX_report_event_hos_<key> and
# GFX_news_event_hos_<key>. The optional number is where to centre the crop (0 = left, 1 = right).
EVENT_PICTURES = {
    "codex": ("ancient_artifact", 0.5),
    "gestalt": ("hive_mind", 0.5),
    "machine": ("machine_sapience", 0.5),
    "galactic_community": ("galactic_community", 0.5),
    "satellite": ("satellite_in_orbit", 0.5),
    "spaceport": ("busy_spaceport", 0.5),
    "science_ship": ("inf_science_ship", 0.5),
    "moon": ("colony_settlement", 0.5),
    "jump_drive": ("wormhole", 0.5),
    "mega_construction": ("megastructure_construction", 0.5),
    "dyson_sphere": ("dyson_sphere", 0.5),
    "ring_world": ("ringworld", 0.5),
    "science_nexus": ("think_tank", 0.5),
    "sentry_array": ("spyorb", 0.5),
    "matter_decompressor": ("matter_decompressor", 0.5),
    "art_installation": ("mega_art_installation", 0.5),
    "coordination_center": ("strategic_coordination_center", 0.5),
    "mega_shipyard": ("megashipyard", 0.5),
    "gateway": ("l-gateway", 0.5),
    "colossus": ("planet_beam", 0.5),
    "world_cracker": ("shattered_planet", 0.5),
    "neutron_sweep": ("dead_city", 0.5),
    "nanobot_diffuser": ("gray_gooed_planet", 0.5),
    "nemesis": ("shroud_eater_of_worlds", 0.5),
    "engine_start": ("inf_crisis_crucible_construction", 0.5),
    "engine_complete": ("supernova", 0.5),
    "anom_whale": ("tiyanki_family", 0.5),
    "anom_cache": ("enigmatic_cache", 0.5),
    "anom_rock": ("crystal_asteroid_sky", 0.5),
    "anom_towel": ("towel", 0.5),
    "anom_goo": ("gray_goo", 0.5),
    "anom_amoeba": ("friendly_amoeba", 0.5),
    "anom_derelict": ("derelict_interior", 0.5),
    "anom_temple": ("ancient_alien_temple", 0.5),
    "anom_signal": ("worrying_signal", 0.5),
    "anom_dragon": ("space_dragon", 0.5),
    "anom_nothing": ("physics_research", 0.5),
    "prethoryn_warning": ("bio_ships_orbiting", 0.5),
    "prethoryn_arrival": ("infested", 0.5),
    "unbidden_warning": ("dimensional_horror", 0.5),
    "unbidden_arrival": ("vortex", 0.5),
    "contingency_warning": ("sapient_AI", 0.5),
    "contingency_arrival": ("contingency_planet", 0.5),
    "crisis_defeated": ("crisis_defeated", 0.5),
    "defender": ("defender_of_the_galaxy", 0.5),
    "synth_betrayal": ("synth_sabotage", 0.5),
    "portal_collapse": ("large_explosion", 0.5),
    "hubs_destroyed": ("machine_space_battle", 0.5),
}

ICONS = "gfx/interface/icons/"

# key -> GFX_idea_hos_<key>. ("pic", event picture) crops the picture; ("icon", icon, event picture)
# draws the icon over a darkened crop of the picture.
IDEAS = {
    "ethic_militarist": ("icon", ICONS + "ethics/ethic_fanatic_militarist.dds", "ground_combat"),
    "ethic_pacifist": ("icon", ICONS + "ethics/ethic_fanatic_pacifist.dds", "alien_nature"),
    "ethic_materialist": ("icon", ICONS + "ethics/ethic_fanatic_materialist.dds", "scientific_experiments"),
    "ethic_spiritualist": ("icon", ICONS + "ethics/ethic_fanatic_spiritualist.dds", "psionics"),
    "ethic_xenophobe": ("icon", ICONS + "ethics/ethic_fanatic_xenophobe.dds", "burning_city"),
    "ethic_xenophile": ("icon", ICONS + "ethics/ethic_fanatic_xenophile.dds", "diplomatic_visit"),
    "ethic_machine": ("icon", ICONS + "governments/authorities/auth_machine_intelligence_35x35.dds", "machine_sapience"),
    "ethic_hive": ("icon", ICONS + "governments/authorities/auth_hive_mind_35x35.dds", "hive_mind"),
    "satellite": ("pic", "satellite_in_orbit"),
    "spaceport": ("pic", "busy_spaceport"),
    "moon": ("pic", "colony_settlement"),
    "jump_drive": ("pic", "wormhole"),
    "dyson_sphere": ("pic", "dyson_sphere"),
    "ring_world": ("pic", "ringworld"),
    "science_nexus": ("pic", "think_tank"),
    "sentry_array": ("pic", "spyorb"),
    "art_installation": ("pic", "mega_art_installation"),
    "coordination_center": ("pic", "strategic_coordination_center"),
    "mega_shipyard": ("pic", "megashipyard"),
    "gateway": ("pic", "l-gateway"),
    "colossus": ("icon", ICONS + "ascension_perks/ap_colossus_project.dds", "planet_beam"),
    "nemesis": ("icon", ICONS + "ascension_perks/ap_become_the_crisis.dds", "shroud_eater_of_worlds"),
    "defender": ("icon", ICONS + "ascension_perks/ap_defender_of_the_galaxy.dds", "defender_of_the_galaxy"),
    "anom_whale": ("pic", "tiyanki_family"),
    "anom_rock": ("pic", "crystal_asteroid_sky"),
    "anom_towel": ("pic", "towel"),
    "anom_amoeba": ("pic", "friendly_amoeba"),
    "anom_temple": ("pic", "ancient_alien_temple"),
    "anom_signal": ("pic", "worrying_signal"),
    "anom_dragon": ("pic", "space_dragon"),
    "crisis_prethoryn": ("icon", ICONS + "relics/r_prethoryn_queen.dds", "infested"),
    "crisis_unbidden": ("icon", ICONS + "relics/r_unbidden_warlock.dds", "dimensional_horror"),
    "crisis_contingency": ("icon", ICONS + "relics/r_contingency_core.dds", "contingency_planet"),
    "crisis_strength": ("icon", ICONS + "ascension_perks/ap_galactic_force_projection.dds", "fleet_evil"),
    "portal_collapsed": ("pic", "large_explosion"),
    "hubs_destroyed": ("pic", "machine_space_battle"),
    "crisis_beaters": ("pic", "crisis_defeated"),
    "synth_betrayal": ("pic", "synth_sabotage"),
}

# key -> GFX_decision_hos_<key>
DECISION_ICONS = {
    "satellite": ICONS + "observation_post_icon.dds",
    "spaceport": ICONS + "new_spaceport.dds",
    "science_ship": ICONS + "research_icon.dds",
    "moon": ICONS + "icon_colony_ship.dds",
    "jump_drive": ICONS + "technologies/tech_jump_drive_1.dds",
    "dyson_sphere": ICONS + "megastructures/dyson_sphere.dds",
    "ring_world": ICONS + "megastructures/ring_world.dds",
    "science_nexus": ICONS + "megastructures/think_tank.dds",
    "sentry_array": ICONS + "megastructures/spy_orb.dds",
    "matter_decompressor": ICONS + "megastructures/matter_decompressor.dds",
    "art_installation": ICONS + "megastructures/mega_art_installation.dds",
    "coordination_center": ICONS + "megastructures/strategic_coordination_center.dds",
    "mega_shipyard": ICONS + "megastructures/mega_shipyard.dds",
    "gateway": ICONS + "megastructures/gateway.dds",
    "colossus": ICONS + "technologies/tech_colossus.dds",
    "colossus_fire": ICONS + "planet_invasion.dds",
    "nemesis": ICONS + "ascension_perks/ap_become_the_crisis.dds",
    "engine": ICONS + "megastructures/crisis_sphere.dds",
    "defender": ICONS + "ascension_perks/ap_defender_of_the_galaxy.dds",
}

# key -> (GFX_decision_category_hos_<key> icon, GFX_decision_cat_picture_hos_<key> picture)
CATEGORIES = {
    "space": (ICONS + "ascension_perks/ap_galactic_wonders.dds", "dyson_sphere"),
    "colossus": (ICONS + "ascension_perks/ap_colossus_project.dds", "planet_beam"),
    "crisis": (ICONS + "ascension_perks/ap_defender_of_the_galaxy.dds", "crisis_declared"),
}

# key -> GFX_portrait_hos_<key>: (relic icon, background event picture)
PORTRAITS = {
    "prethoryn_queen": (ICONS + "relics/r_prethoryn_queen.dds", "infested"),
    "unbidden_warlock": (ICONS + "relics/r_unbidden_warlock.dds", "dimensional_horror"),
    "contingency_core": (ICONS + "relics/r_contingency_core.dds", "contingency_planet"),
}

# HOI4 tag -> (Stellaris flag emblem, background colour, emblem tint or None)
FLAGS = {
    "PSC": ("flags/special/the_swarm.dds", (74, 12, 92), None),
    "UNB": ("flags/special/extradimensional_01.dds", (8, 22, 64), None),
    "CTG": ("flags/special/ai_01.dds", (8, 30, 22), None),
}

ALBUM_ART_SOURCE = "gfx/event_pictures/galactic_community.dds"

# Track names for the radio station; anything not listed is title-cased from its file name.
SONG_TITLES = {
    "alphacentauri": "Alpha Centauri",
    "anewdawn": "A New Dawn",
    "cradleofthegalaxy": "Cradle of the Galaxy",
    "creationandbeyond": "Creation and Beyond",
    "deepspacetravels": "Deep Space Travels",
    "distantnebula": "Distant Nebula",
    "fasterthanlight": "Faster Than Light",
    "genesis": "Genesis",
    "gravitationalconstant": "Gravitational Constant",
    "infinitebeing": "Infinite Being",
    "inmemoryofmercedesromero": "In Memory of Mercedes Romero",
    "inmemoryofmrluminousflux": "In Memory of Mr. Luminous Flux",
    "insearchoflife": "In Search of Life",
    "journeythroughthegalaxy": "Journey Through the Galaxy",
    "luminescence_endcredits": "Luminescence",
    "pillarsofcreation": "Pillars of Creation",
    "ridingthesolarwind": "Riding the Solar Wind",
    "robo_sapiens": "Robo Sapiens",
    "sigmatauri": "Sigma Tauri",
    "spatiallullaby": "Spatial Lullaby",
    "syntheticdawn_maintheme": "Synthetic Dawn",
    "syntheticgod": "Synthetic God",
    "thebirthofastar": "The Birth of a Star",
    "thecelestialcity": "The Celestial City",
    "theimperialfleet": "The Imperial Fleet",
    "theimperialfleetsecondcoming": "The Imperial Fleet: Second Coming",
    "totheendsofthegalaxy": "To the Ends of the Galaxy",
    "towardsutopia": "Towards Utopia",
    "towardsutopianovaflare": "Towards Utopia (Nova Flare)",
    "utopia_maintitle": "Utopia",
}


def write_dds(img, path):
    """Uncompressed 32-bit BGRA DDS, the format HOI4's own event pictures use."""
    img = img.convert("RGBA")
    w, h = img.size
    path.parent.mkdir(parents=True, exist_ok=True)
    caps, height, width, pitch, pixelformat, texture = 0x1, 0x2, 0x4, 0x8, 0x1000, 0x1000
    rgb, alphapixels = 0x40, 0x1
    header = struct.pack(
        "<4s7I44s8I5I",
        b"DDS ", 124, caps | height | width | pitch | pixelformat, h, w, w * 4, 0, 1, b"\0" * 44,
        32, rgb | alphapixels, 0, 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000,
        texture, 0, 0, 0, 0,
    )
    assert len(header) == 128
    r, g, b, a = img.split()
    data = Image.merge("RGBA", (b, g, r, a)).tobytes()
    path.write_bytes(header + data)


def write_tga(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGBA").save(path, format="TGA", rle=False)


def cover(img, size, focus=0.5):
    """Scale to fill size, then crop around focus (horizontal) and the vertical centre."""
    tw, th = size
    w, h = img.size
    scale = max(tw / w, th / h)
    img = img.resize((max(tw, round(w * scale)), max(th, round(h * scale))), Image.LANCZOS)
    w, h = img.size
    left = min(max(0, round(focus * w - tw / 2)), w - tw)
    top = (h - th) // 2
    return img.crop((left, top, left + tw, top + th))


def fit(img, size):
    """Scale to fit inside size, keeping aspect, centred on a transparent canvas."""
    tw, th = size
    w, h = img.size
    scale = min(tw / w, th / h)
    img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(img, ((tw - img.width) // 2, (th - img.height) // 2))
    return canvas


def frame(img, colour=(96, 200, 220, 255), width=2):
    """Stellaris-style thin teal border."""
    img = img.copy()
    d = ImageDraw.Draw(img)
    w, h = img.size
    for i in range(width):
        d.rectangle((i, i, w - 1 - i, h - 1 - i), outline=colour)
    return img


class Builder:
    def __init__(self, stellaris, mod):
        self.s = stellaris
        self.mod = mod
        self.sprites = []  # (name, texturefile, frames)
        self.missing = []

    def load(self, rel):
        p = self.s / rel
        if not p.exists():
            self.missing.append(rel)
            return None
        img = Image.open(p)
        img.load()
        return img.convert("RGBA")

    def event_pic(self, name):
        return self.load(f"gfx/event_pictures/{name}.dds")

    def sprite(self, name, rel, frames=1):
        self.sprites.append((name, rel, frames))

    def build_event_pictures(self):
        for key, (src, focus) in EVENT_PICTURES.items():
            img = self.event_pic(src)
            if img is None:
                continue
            report = f"gfx/event_pictures/hos_{key}.dds"
            news = f"gfx/event_pictures/hos_news_{key}.dds"
            write_dds(cover(img, (210, 176), focus), self.mod / report)
            write_dds(cover(img, (397, 153), focus), self.mod / news)
            self.sprite(f"GFX_report_event_hos_{key}", report)
            self.sprite(f"GFX_news_event_hos_{key}", news)

    def build_ideas(self):
        for key, spec in IDEAS.items():
            if spec[0] == "pic":
                bg = self.event_pic(spec[1])
                if bg is None:
                    continue
                out = frame(cover(bg, (60, 68)))
            else:
                icon, bg = self.load(spec[1]), self.event_pic(spec[2])
                if icon is None or bg is None:
                    continue
                base = ImageEnhance.Brightness(cover(bg, (60, 68))).enhance(0.45)
                base.alpha_composite(fit(icon, (52, 56)), (4, 6))
                out = frame(base)
            rel = f"gfx/interface/ideas/hos_{key}.dds"
            write_dds(out, self.mod / rel)
            self.sprite(f"GFX_idea_hos_{key}", rel)

    def build_decisions(self):
        for key, src in DECISION_ICONS.items():
            icon = self.load(src)
            if icon is None:
                continue
            rel = f"gfx/interface/decisions/hos_{key}.dds"
            write_dds(fit(icon, (32, 32)), self.mod / rel)
            self.sprite(f"GFX_decision_hos_{key}", rel)
        for key, (icon_src, pic_src) in CATEGORIES.items():
            icon, pic = self.load(icon_src), self.load(f"gfx/event_pictures/{pic_src}.dds")
            if icon is not None:
                rel = f"gfx/interface/decisions/hos_category_{key}.dds"
                write_dds(fit(icon, (52, 40)), self.mod / rel)
                self.sprite(f"GFX_decision_category_hos_{key}", rel)
            if pic is not None:
                rel = f"gfx/interface/decisions/hos_cat_picture_{key}.dds"
                write_dds(frame(cover(pic, (114, 101))), self.mod / rel)
                self.sprite(f"GFX_decision_cat_picture_hos_{key}", rel)

    def build_portraits(self):
        for key, (relic_src, bg_src) in PORTRAITS.items():
            relic, bg = self.load(relic_src), self.event_pic(bg_src)
            if relic is None or bg is None:
                continue
            base = ImageEnhance.Brightness(cover(bg, (156, 210))).enhance(0.55)
            base.alpha_composite(fit(relic, (150, 150)), (3, 50))
            rel = f"gfx/leaders/hos/{key}.dds"
            write_dds(base, self.mod / rel)
            self.sprite(f"GFX_portrait_hos_{key}", rel)

    def build_flags(self):
        for tag, (emblem_src, colour, _tint) in FLAGS.items():
            emblem = self.load(emblem_src)
            if emblem is None:
                continue
            big = Image.new("RGBA", (82, 52), colour + (255,))
            big.alpha_composite(fit(emblem, (48, 48)), (17, 2))
            write_tga(big, self.mod / f"gfx/flags/{tag}.tga")
            write_tga(big.resize((41, 26), Image.LANCZOS), self.mod / f"gfx/flags/medium/{tag}.tga")
            write_tga(big.resize((10, 7), Image.LANCZOS), self.mod / f"gfx/flags/small/{tag}.tga")

    def build_album_art(self):
        src = self.load(ALBUM_ART_SOURCE)
        if src is None:
            return
        face = cover(src, (152, 120))
        dim = ImageEnhance.Brightness(face).enhance(0.6)
        lit = frame(face, (255, 210, 120, 255), 3)
        art = Image.new("RGBA", (304, 120))
        art.paste(dim, (0, 0))
        art.paste(lit, (152, 0))
        rel = "gfx/interface/topbar/musicplayer/hos_stellaris_album_art.dds"
        write_dds(art, self.mod / rel)
        self.sprite("GFX_stellaris_album_art", rel, frames=2)

    def build_music(self):
        songs = sorted((self.s / "music").glob("*.ogg"))
        if not songs:
            self.missing.append("music/*.ogg")
            return
        out = self.mod / "music" / "stellaris"
        out.mkdir(parents=True, exist_ok=True)
        asset, station = [], ['music_station = "stellaris"', ""]
        loc = ["l_english:", ' stellaris_TITLE: "Stellaris"']
        for song in songs:
            shutil.copy2(song, out / song.name)
            name = "hos_" + song.stem
            title = SONG_TITLES.get(song.stem, song.stem.replace("_", " ").title())
            asset += ["music = {", f'\tname = "{name}"', f'\tfile = "{song.name}"', "\tvolume = 0.65", "}", ""]
            station += ["music = {", f'\tsong = "{name}"', "}", ""]
            loc.append(f' {name}: "{title}"')
        (out / "stellaris_music.asset").write_text("\n".join(asset), encoding="utf-8")
        (out / "stellaris_soundtrack.txt").write_text("\n".join(station), encoding="utf-8")
        loc_file = self.mod / "localisation" / "english" / "hos_music_l_english.yml"
        loc_file.parent.mkdir(parents=True, exist_ok=True)
        loc_file.write_text("\n".join(loc) + "\n", encoding="utf-8-sig")
        print(f"music: {len(songs)} tracks")

    def write_gfx(self):
        lines = ["# Written by tools/import_stellaris_art.py. Rerun it rather than editing this file.", "spriteTypes = {"]
        for name, rel, frames in self.sprites:
            lines += ["\tspriteType = {", f'\t\tname = "{name}"', f'\t\ttexturefile = "{rel}"']
            if frames > 1:
                lines.append(f"\t\tnoOfFrames = {frames}")
            lines.append("\t}")
        lines.append("}")
        (self.mod / "interface" / "hos_art.gfx").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stellaris", type=Path, default=DEFAULT_STELLARIS, help="Stellaris install folder")
    ap.add_argument("--mod", type=Path, default=MOD, help="the hearts_of_stellaris mod folder")
    ap.add_argument("--no-music", action="store_true", help="skip copying the soundtrack")
    args = ap.parse_args()
    if not (args.stellaris / "stellaris.exe").exists():
        sys.exit(f"Stellaris not found at {args.stellaris} (pass --stellaris)")
    b = Builder(args.stellaris, args.mod)
    b.build_event_pictures()
    b.build_ideas()
    b.build_decisions()
    b.build_portraits()
    b.build_flags()
    b.build_album_art()
    if not args.no_music:
        b.build_music()
    b.write_gfx()
    print(f"sprites: {len(b.sprites)}")
    if b.missing:
        print("missing from this Stellaris version (those sprites were skipped):")
        for m in sorted(set(b.missing)):
            print("  " + m)


if __name__ == "__main__":
    main()
