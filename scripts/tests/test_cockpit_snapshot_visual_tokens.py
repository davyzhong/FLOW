from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "export_cockpit_snapshot.mjs"


class CockpitSnapshotVisualTokenTests(unittest.TestCase):
    def test_snapshot_css_uses_shared_visual_tokens_without_literal_colors(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        css = source.split("<title>${escapeHtml(title)}</title><style>", 1)[1].split(
            "</style></head>", 1
        )[0]

        for token in (
            "tokens.colors.brand.goldSoft",
            "tokens.colors.text.secondary",
            "tokens.colors.surface.paper",
            "tokens.colors.surface.soft",
            "tokens.shadow.panel",
            "tokens.radius.md",
            "tokens.typography.family.numeric",
        ):
            self.assertIn(token, css)
        self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", css))
        self.assertNotIn("Georgia", css)


if __name__ == "__main__":
    unittest.main()
