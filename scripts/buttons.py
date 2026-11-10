"""Generates the link buttons in assets/ (run once: python scripts/buttons.py)."""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
W, H = 320, 64
BG, BORDER, TEXT = "#161b22", "#30363d", "#e6edf3"

# Simple 28x28 icons drawn with basic shapes; {c} = accent colour, {bg} = button bg.
ICONS = {
    "monitor": """
      <rect x="1" y="3" width="26" height="17" rx="2" fill="none" stroke="{c}" stroke-width="2.2"/>
      <path d="M6 9 l4 3 -4 3 M12 15 h6" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M10 25 h8 M14 20 v5" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>""",
    "linkedin": """
      <rect x="1" y="1" width="26" height="26" rx="4" fill="{c}"/>
      <rect x="6" y="11" width="3.6" height="11" fill="{bg}"/>
      <circle cx="7.8" cy="7" r="2.2" fill="{bg}"/>
      <path d="M12.5 11 h3.4 v1.6 c0.8-1.3 2.2-2 3.8-2 c3 0 4 1.9 4 4.6 V22 h-3.6 v-6.2 c0-1.5-0.4-2.5-1.8-2.5 c-1.5 0-2.2 1-2.2 2.6 V22 h-3.6 z" fill="{bg}"/>""",
    "mail": """
      <rect x="1" y="5" width="26" height="18" rx="2" fill="none" stroke="{c}" stroke-width="2.2"/>
      <path d="M2 7 l12 9 12-9" fill="none" stroke="{c}" stroke-width="2.2" stroke-linejoin="round"/>""",
    "stack": """
      <path d="M3 15 v10 h20 v-10" fill="none" stroke="{c}" stroke-width="2.2"/>
      <path d="M7 21 h12 M7.4 16.8 l11.8 1.4 M8.6 12.6 l11.4 3.4 M10.8 8.4 l10.4 5.6 M14.4 4.4 l8.8 7.6" stroke="{c}" stroke-width="2.2"/>""",
    "x": """
      <path d="M3 3 h6.5 L25 25 h-6.5 z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>
      <path d="M24.5 3 L16 12.6 M3.5 25 L12 15.4" stroke="{c}" stroke-width="2.2" stroke-linecap="round"/>""",
    "instagram": """
      <rect x="2" y="2" width="24" height="24" rx="7" fill="none" stroke="{c}" stroke-width="2.2"/>
      <circle cx="14" cy="14" r="5.5" fill="none" stroke="{c}" stroke-width="2.2"/>
      <circle cx="20.6" cy="7.4" r="1.5" fill="{c}"/>""",
}

BUTTONS = [
    ("behance", "BEHANCE", "monitor", "#ffa657"),
    ("linkedin", "LINKEDIN", "linkedin", "#58a6ff"),
    ("email", "EMAIL", "mail", "#ffa657"),
    ("stackoverflow", "STACK OVERFLOW", "stack", "#f48024"),
    ("x", "X / TWITTER", "x", "#e6edf3"),
    ("instagram", "INSTAGRAM", "instagram", "#e4405f"),
]


def button(label: str, icon: str, accent: str) -> str:
    text_w = len(label) * 10.6  # ~0.59em at 18px
    group_w = 28 + 14 + text_w
    gx = (W - group_w) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="6" fill="{BG}" stroke="{BORDER}" stroke-width="2"/>
  <rect x="1" y="{H - 5}" width="{W - 2}" height="4" fill="{accent}"/>
  <g transform="translate({gx:.1f} {(H - 4 - 28) / 2:.1f})">{ICONS[icon].format(c=accent, bg=BG)}
  </g>
  <text x="{gx + 42:.1f}" y="{(H - 4) / 2 + 6.5:.1f}" fill="{TEXT}" font-family="Consolas, 'DejaVu Sans Mono', Menlo, 'Courier New', monospace" font-size="18" letter-spacing="0.5">{label}</text>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, label, icon, accent in BUTTONS:
        (OUT / f"btn-{name}.svg").write_text(button(label, icon, accent), encoding="utf-8")
        print("wrote", f"assets/btn-{name}.svg")
