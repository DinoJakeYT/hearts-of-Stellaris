#!/usr/bin/env python3
"""Static checks for Hearts of Stellaris, run before launching the game.

- braces balance in every script, gfx and gui file
- every GFX_ sprite the scripts use is defined (by the mod or by HOI4)
- every event fired is defined, and every scripted effect/trigger used is defined
- every name the game will look up in localisation has a key
- every key in the scripts is a known HOI4 effect, trigger, modifier or structural word
  (from HOI4's own documentation/*.md), or something this mod defines

Usage: python check_mod.py [--hoi4 "<HOI4 install>"]
"""
import argparse
import re
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent
DEFAULT_HOI4 = Path("C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV")

# Words that are block or parameter names rather than effects, triggers or modifiers.
STRUCTURAL = set("""
add_namespace id title desc picture is_triggered_only hidden major option name trigger ai_chance factor base
modifier immediate limit if else else_if trigger_else NOT OR AND always country ideas allowed allowed_civil_war
removal_cost targeted_modifier tag attack_bonus_against defense_bonus_against icon visible available
fire_only_once cost days_remove days_re_enable complete_effect remove_effect cancel_trigger cancel_effect
ai_will_do state_target on_map_mode target_trigger target_root_trigger priority effect on_actions
on_startup on_monthly on_monthly_PSC on_monthly_UNB on_monthly_CTG on_capitulation enable spriteTypes spriteType
texturefile noOfFrames characters portraits civilian large country_leader ideology traits expire leader_traits
random sprite opinion_modifiers value decay group default text rule flag days hours type amount size
threat target modifier_name start end compare add break do division owner count regiments support x y
is_locked infantry artillery_brigade engineer recon ruling_party elections_allowed democratic fascism communism
neutrality idea category bonus uses state ratio org_damage str_damage level prioritize capital graphical_culture
graphical_culture_2d color set_research_slots guiTypes containerWindowType position size width height iconType
spriteType alwaystransparent instantTextboxType font maxWidth maxHeight format buttonType quadTextureSprite
buttonFont Orientation clicksound pdx_tooltip extendedScrollbarType tileSize maxValue minValue stepSize startValue
horizontal orientation origo setTrackFrameOnChange slider track checkBoxType music_station music song file volume
chance transfer_troops can_create_factions can_join_factions can_send_volunteers can_puppet
value_name display_individual_scopes tooltip controller owner damage
""".split())


def strip_comments(text):
    out = []
    for line in text.splitlines():
        in_str = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_str = not in_str
            elif ch == "#" and not in_str:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def without_strings(text):
    return re.sub(r'"[^"\n]*"', '""', text)


def doc_names(path):
    return set(re.findall(r"^## (\S+)\s*$", path.read_text(encoding="utf-8", errors="replace"), re.M))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hoi4", type=Path, default=DEFAULT_HOI4)
    args = ap.parse_args()
    errors, warnings = [], []

    scripts = [p for p in MOD.rglob("*.txt") if "music" not in p.parts]
    gfx_files = list(MOD.rglob("*.gfx")) + list(MOD.rglob("*.gui"))
    texts = {p: strip_comments(p.read_text(encoding="utf-8-sig")) for p in scripts + gfx_files}

    # 1. braces
    for p, t in texts.items():
        depth = 0
        for n, line in enumerate(without_strings(t).splitlines(), 1):
            depth += line.count("{") - line.count("}")
            if depth < 0:
                errors.append(f"{p.relative_to(MOD)}:{n}: unmatched }}")
                depth = 0
        if depth:
            errors.append(f"{p.relative_to(MOD)}: {depth} unclosed {{")

    all_script = "\n".join(t for p, t in texts.items() if p.suffix == ".txt")

    # 2. sprites
    defined_gfx = set(re.findall(r'name\s*=\s*"?(GFX_\w+)', "\n".join(t for p, t in texts.items() if p.suffix == ".gfx")))
    vanilla_gfx = set()
    for g in (args.hoi4 / "interface").glob("*.gfx"):
        vanilla_gfx |= set(re.findall(r'name\s*=\s*"?(GFX_\w+)', g.read_text(encoding="utf-8", errors="replace")))
    used = set(re.findall(r"\bGFX_\w+", all_script))
    used |= {"GFX_idea_" + m for m in re.findall(r"\bpicture\s*=\s*(hos_\w+)", all_script)}
    used |= {"GFX_decision_category_" + m for m in re.findall(r"^\s*icon\s*=\s*(hos_\w+)", all_script, re.M)}
    for g in sorted(used - defined_gfx - vanilla_gfx):
        errors.append(f"sprite not defined: {g}")
    for name, tex in re.findall(r'name\s*=\s*"(GFX_\w+)"\s*texturefile\s*=\s*"([^"]+)"', texts.get(MOD / "interface" / "hos_art.gfx", "")):
        if not (MOD / tex).exists():
            errors.append(f"{name}: missing texture {tex} (run import_stellaris_art.py)")

    # 3. events
    defined_events = set(re.findall(r"^\s*id\s*=\s*(hos_\w+\.\d+)", all_script, re.M))
    fired = set(re.findall(r"(?:country_event|news_event|state_event)\s*=\s*\{\s*id\s*=\s*(hos_\w+\.\d+)", all_script))
    fired |= set(re.findall(r"(?:country_event|news_event)\s*=\s*(hos_\w+\.\d+)", all_script))
    for e in sorted(fired - defined_events):
        errors.append(f"event fired but not defined: {e}")
    for e in sorted(defined_events - fired):
        warnings.append(f"event defined but never fired: {e}")

    # 4. scripted effects / triggers
    def top_level_names(folder):
        names = set()
        for p, t in texts.items():
            if folder in p.parts:
                names |= set(re.findall(r"^(\w+)\s*=\s*\{", t, re.M))
        return names
    s_effects, s_triggers = top_level_names("scripted_effects"), top_level_names("scripted_triggers")
    for n in sorted(set(re.findall(r"\b(hos_\w+)\s*=\s*(?:yes|no)\b", all_script)) - s_effects - s_triggers):
        errors.append(f"scripted effect/trigger used but not defined: {n}")

    # 5. localisation
    loc = {}
    for y in (MOD / "localisation").rglob("*.yml"):
        raw = y.read_bytes()
        if not raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{y.relative_to(MOD)}: not UTF-8 with BOM")
        for m in re.finditer(r'^\s+([\w.\-]+):\d*\s+"(.*)"\s*$', raw.decode("utf-8-sig"), re.M):
            if m.group(1) in loc:
                errors.append(f"duplicate loc key {m.group(1)}")
            loc[m.group(1)] = m.group(2)
    need = set()
    ideas = set(re.findall(r"^\t\t(hos_\w+)\s*=\s*\{", texts[MOD / "common/ideas/hos_ideas.txt"], re.M))
    need |= ideas | {i + "_desc" for i in ideas if not i.startswith("hos_crisis_strength")}
    for p, t in texts.items():
        if "decisions" in p.parts and "categories" not in p.parts:
            for d in re.findall(r"^\t(hos_\w+)\s*=\s*\{", t, re.M):
                need |= {d, d + "_desc"}
        if "categories" in p.parts:
            for c in re.findall(r"^(hos_\w+)\s*=\s*\{", t, re.M):
                need |= {c, c + "_desc"}
        if "events" in p.parts:
            need |= set(re.findall(r"\b(?:title|desc|name)\s*=\s*(hos_[\w.]+)", t))
    need |= set(re.findall(r"custom_effect_tooltip\s*=\s*(\w[\w.]*)", all_script))
    need |= set(re.findall(r"\b(?:name|text|desc|group)\s*=\s*\"?(RULE_\w+)", all_script))
    need |= set(re.findall(r"add_named_threat\s*=\s*\{[^}]*name\s*=\s*(\w+)", all_script))
    need |= set(re.findall(r"^\t(hos_\w+)\s*=\s*\{", texts[MOD / "common/opinion_modifiers/hos_opinion_modifiers.txt"], re.M))
    need |= set(re.findall(r"^(hos_\w+)\s*=\s*\{", texts[MOD / "common/dynamic_modifiers/hos_dynamic_modifiers.txt"], re.M))
    need |= set(re.findall(r"^\t(hos_\w+)\s*=\s*\{", texts[MOD / "common/country_leader/hos_traits.txt"], re.M))
    need |= set(re.findall(r"^\t(\w+)\s*=\s*\{", texts[MOD / "common/characters/hos_crisis_characters.txt"], re.M))
    need |= set(re.findall(r"set_state_name\s*=\s*(\w+)", all_script))
    need |= {t + s for t in ("PSC", "UNB", "CTG") for s in ("", "_DEF", "_ADJ")}
    for k in sorted(need - set(loc)):
        errors.append(f"missing localisation: {k}")
    for k, v in loc.items():
        if v.count("§") % 2:
            warnings.append(f"loc {k}: odd number of § colour codes")

    # 6. keys against HOI4's documentation
    docs = args.hoi4 / "documentation"
    known = STRUCTURAL | doc_names(docs / "effects_documentation.md") | doc_names(docs / "triggers_documentation.md")
    known |= doc_names(docs / "modifiers_documentation.md")
    known |= {i + "_drift" for i in ("democratic", "fascism", "communism", "neutrality")}
    known |= s_effects | s_triggers | ideas
    for tech in (args.hoi4 / "common" / "technologies").glob("*.txt"):
        known |= set(re.findall(r"^\t(\w+)\s*=\s*\{", tech.read_text(encoding="utf-8", errors="replace"), re.M))
    known |= set(re.findall(r"(?:set|add_to|multiply|check|subtract_from)_(?:temp_)?variable\s*=\s*\{\s*([\w.]+)", all_script))
    known |= set(re.findall(r"\bend\s*=\s*(\w+)", all_script))
    known |= set(re.findall(r"^\s*(\w+)\s*=\s*\{", all_script, re.M)) & {k for k in re.findall(r"\b(hos_\w+|[A-Z]{3}_\w+)", all_script)}
    tags = {"PSC", "UNB", "CTG", "ROOT", "FROM", "PREV", "THIS", "OWNER", "CONTROLLER", "capital_scope"}
    for p, t in texts.items():
        if p.suffix != ".txt" or "game_rules" in p.parts or "country_tags" in p.parts:
            continue
        for n, line in enumerate(without_strings(t).splitlines(), 1):
            for key in re.findall(r"(?:^|[\s{])([A-Za-z_][\w.:]*)\s*[<>=]", line):
                if key in known or key in tags or re.fullmatch(r"\d+", key) or key.startswith(("global.", "var:", "event_target:")):
                    continue
                if p.parent.name == "history" or "history" in p.parts:
                    if key in ("capital", "set_technology", "set_politics", "set_popularities"):
                        continue
                errors.append(f"{p.relative_to(MOD)}:{n}: unknown key '{key}'")

    # 7. rules HOI4 1.19.3 enforced at load (error.log), which the docs don't mention
    for p, t in texts.items():
        if p.suffix != ".txt":
            continue
        rel = p.relative_to(MOD)
        if "history" not in p.parts:
            for n, line in enumerate(t.splitlines(), 1):
                if re.search(r"\brecruit_character\s*=", line):
                    errors.append(f"{rel}:{n}: recruit_character only works in history files (promote_character at runtime)")
        if "on_actions" in p.parts:
            for m in re.finditer(r"\bon_startup\s*=\s*\{\s*effect\s*=\s*\{\s*(\w+)\s*=\s*(?:yes|no)\b", t):
                errors.append(f"{rel}: on_startup has no scope; call {m.group(1)} inside a country scope")
        if "game_rules" in p.parts:
            depth = 0
            for n, line in enumerate(without_strings(t).splitlines(), 1):
                m = re.match(r"\s*(\w+)\s*=", line)
                if depth == 1 and m and m.group(1) not in ("name", "group", "icon", "required_dlc", "option", "default"):
                    errors.append(f"{rel}:{n}: '{m.group(1)}' is not allowed directly in a game rule")
                depth += line.count("{") - line.count("}")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(scripts)} scripts, {len(gfx_files)} gfx/gui, {len(loc)} loc keys: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
