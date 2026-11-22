"""Tests for the resource planning of the MANGFALL cards add-on (no Home Assistant needed)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
try:
    import run
except ModuleNotFoundError:  # aiohttp missing locally: stub it, plan() does not need it
    import types

    sys.modules["aiohttp"] = types.SimpleNamespace(
        ClientError=Exception, ClientTimeout=lambda **k: None
    )
    import run

URL = run.URL + "?v=1.5.1"


class PlanTest(unittest.TestCase):
    def test_fresh_install_creates_resource(self):
        self.assertEqual(
            run.plan([], URL), {"action": "create", "url": URL, "drop": []}
        )

    def test_hacs_copy_is_left_alone(self):
        res = [
            {
                "id": "1",
                "url": "/hacsfiles/mangfall-cards/mangfall-cards.js?hacstag=12",
                "type": "module",
            }
        ]
        self.assertEqual(run.plan(res, URL)["action"], "skip")

    def test_haglo_copy_is_taken_over(self):
        res = [
            {
                "id": "7",
                "url": "/local/haglo/mangfall-cards.js?v=1.5.0",
                "type": "module",
            }
        ]
        self.assertEqual(
            run.plan(res, URL), {"action": "update", "id": "7", "url": URL, "drop": []}
        )

    def test_old_version_is_updated_and_duplicates_dropped(self):
        res = [
            {"id": "1", "url": run.URL + "?v=1.4.0", "type": "module"},
            {
                "id": "2",
                "url": "/local/haglo/mangfall-cards.js?v=1.5.0",
                "type": "module",
            },
        ]
        p = run.plan(res, URL)
        self.assertEqual(
            (p["action"], p["id"], [r["id"] for r in p["drop"]]), ("update", "1", ["2"])
        )

    def test_current_version_needs_nothing(self):
        res = [{"id": "1", "url": URL, "type": "module"}]
        self.assertEqual(run.plan(res, URL), {"action": "none", "drop": []})

    def test_other_cards_are_ignored(self):
        res = [{"id": "3", "url": "/hacsfiles/mushroom/mushroom.js", "type": "module"}]
        self.assertEqual(run.plan(res, URL)["action"], "create")


if __name__ == "__main__":
    unittest.main()
