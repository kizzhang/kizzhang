from __future__ import annotations

import argparse
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TIME_ZONE = ZoneInfo("Asia/Taipei")
DAY_START_HOUR = 7
NIGHT_START_HOUR = 19

DAY_IMAGE = "./assets/kizzhang-black-hole-ascii-v3.gif"
NIGHT_IMAGE = (
    "./assets/kizzhang-black-hole-ascii-v6-black-fluorescent-80pct-speed.gif"
)

IMAGE_PATTERN = re.compile(
    rf'(?P<prefix><img src=")(?P<path>{re.escape(DAY_IMAGE)}|'
    rf'{re.escape(NIGHT_IMAGE)})(?P<suffix>")'
)


def selected_period(mode: str, now: datetime | None = None) -> tuple[str, datetime]:
    local_now = (now or datetime.now(TIME_ZONE)).astimezone(TIME_ZONE)
    if mode in {"day", "night"}:
        return mode, local_now
    period = (
        "day"
        if DAY_START_HOUR <= local_now.hour < NIGHT_START_HOUR
        else "night"
    )
    return period, local_now


def update_readme(readme: Path, period: str) -> bool:
    with readme.open("r", encoding="utf-8", newline="") as handle:
        original = handle.read()

    matches = list(IMAGE_PATTERN.finditer(original))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one managed profile image in {readme}; found {len(matches)}"
        )

    target = DAY_IMAGE if period == "day" else NIGHT_IMAGE
    updated, count = IMAGE_PATTERN.subn(
        lambda match: f'{match.group("prefix")}{target}{match.group("suffix")}',
        original,
        count=1,
    )
    if count != 1:
        raise RuntimeError("The managed profile image could not be replaced")

    changed = updated != original
    if changed:
        with readme.open("w", encoding="utf-8", newline="") as handle:
            handle.write(updated)
    return changed


def write_action_outputs(period: str, changed: bool, local_now: datetime) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"period={period}\n")
        handle.write(f"changed={str(changed).lower()}\n")
        handle.write(f"taipei_time={local_now.isoformat()}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Switch the profile animation between day and night assets."
    )
    parser.add_argument("--mode", choices=("auto", "day", "night"), default="auto")
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    args = parser.parse_args()

    period, local_now = selected_period(args.mode)
    changed = update_readme(args.readme, period)
    write_action_outputs(period, changed, local_now)
    target = DAY_IMAGE if period == "day" else NIGHT_IMAGE
    print(
        f"period={period} taipei_time={local_now.isoformat()} "
        f"changed={str(changed).lower()} image={target}"
    )


if __name__ == "__main__":
    main()
