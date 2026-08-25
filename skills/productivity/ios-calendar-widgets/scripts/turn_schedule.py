#!/usr/bin/env python3
"""Generate an alternating-duty ICS calendar + lettered heatmap PNG widget.

Usage:
  python3 turn_schedule.py [--start YYYY-MM-DD] [--days N] [--names "Seif,Hesham"]
                           [--letters S,H] [--out DIR] [--year YYYY]

Outputs:
  <out>/duty.ics         — N all-day events, alternating owners (CRLF, RFC 5545)
  <out>/heatmap_turns.png — GitHub-style heatmap, initial in each cell,
                            today outlined white
"""
import argparse
import calendar as cal
import datetime as dt
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = "#000000"
GREEN = {0: "#0e4429", 1: "#26a641"}


def build_ics(start: dt.date, days: int, people: list[tuple[str, str]]) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//turnheat//EN", "CALSCALE:GREGORIAN"]
    for i in range(days):
        d = start + dt.timedelta(days=i)
        letter, name = people[i % len(people)]
        lines += [
            "BEGIN:VEVENT",
            f"UID:turn-{d.isoformat()}@turnheat",
            f"DTSTAMP:{start:%Y%m%d}T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
            f"DTEND;VALUE=DATE:{(d + dt.timedelta(days=1)):%Y%m%d}",  # exclusive end
            f"SUMMARY:{letter} \u2014 {name}'s turn",
            "DESCRIPTION:Alternating daily duty",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)  # CRLF required


def draw_heatmap(start: dt.date, days: int, people: list[tuple[str, str]], year: int) -> Image.Image:
    CELL, GAP, PAD = 20, 3, 14
    top_pad = PAD + 14
    jan1 = dt.date(year, 1, 1)
    days_in_year = (dt.date(year, 12, 31) - jan1).days + 1
    weeks = ((jan1.weekday() + days_in_year) // 7) + 1
    W = PAD * 2 + weeks * (CELL + GAP) - GAP
    H = top_pad + 7 * (CELL + GAP) - GAP + PAD
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    try:
        mono = ImageFont.truetype(FONT, CELL - 8)
        head = ImageFont.truetype(FONT, 12)
    except OSError:
        mono = head = None
    for m in range(1, 13):
        first = dt.date(year, m, 1)
        col = first.timetuple().tm_yday // 7
        if head:
            dr.text((PAD + col * (CELL + GAP), PAD - 4), cal.month_abbr[m], font=head, fill="#8b949e")
    offset = jan1.weekday()
    for i in range(days_in_year):
        d = dt.date(year, 1, 1) + dt.timedelta(days=i)
        idx = (d - start).days
        if idx < 0 or idx >= days:
            continue
        letter, _ = people[idx % len(people)]
        col = (offset + i) // 7
        row = (offset + i) % 7
        x = PAD + col * (CELL + GAP)
        y = top_pad + row * (CELL + GAP)
        shade = GREEN[0] if idx == 0 else GREEN[1]
        dr.rectangle([x, y, x + CELL, y + CELL], fill=shade,
                     outline="#f0f6fc" if idx == 0 else None, width=2)
        if mono:
            dr.text((x + CELL // 2, y + CELL // 2), letter, font=mono, fill="white", anchor="mm")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=dt.date.today().isoformat())
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--names", default="Seif,Hesham")
    ap.add_argument("--letters", default="S,H")
    ap.add_argument("--out", default=".")
    ap.add_argument("--year", type=int, default=dt.date.today().year)
    a = ap.parse_args()
    start = dt.date.fromisoformat(a.start)
    people = list(zip(a.letters.split(","), a.names.split(",")))
    ics = build_ics(start, a.days, people)
    with open(f"{a.out}/duty.ics", "w", newline="") as f:
        f.write(ics)
    img = draw_heatmap(start, a.days, people, a.year)
    img.save(f"{a.out}/heatmap_turns.png")
    print(f"duty.ics: {a.days} events from {start} | heatmap_turns.png {img.size}")


if __name__ == "__main__":
    main()
