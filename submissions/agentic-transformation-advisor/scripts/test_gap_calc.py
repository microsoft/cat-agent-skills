import unittest

import gap_calc


class UnknownPillarTests(unittest.TestCase):
    def profile(self, levels):
        return {
            "current": dict(zip(gap_calc.PILLAR_KEYS, levels)),
            "patterns": ["employee_ai_enablement"],
        }

    def test_all_unknown_cannot_establish_readiness_or_ceiling(self):
        result = gap_calc.run(self.profile([None] * 5))
        self.assertIsNone(result["weakest_pillar"])
        for analysis in [*result["per_pattern"].values(), result["combined"]]:
            self.assertIn("Readiness undetermined", analysis["verdict"])
            self.assertEqual(len(analysis["unknown_pillars"]), 5)
        self.assertIn("ceiling): undetermined", gap_calc.to_markdown(result))

    def test_one_unknown_prevents_definitive_ceiling(self):
        result = gap_calc.run(self.profile([500, 500, 500, 500, None]))
        self.assertIsNone(result["weakest_pillar"])
        self.assertIn("Readiness undetermined", result["combined"]["verdict"])
        markdown = gap_calc.to_markdown(result)
        self.assertIn("ceiling): undetermined", markdown)
        self.assertNotIn("ceiling): Organization", markdown)

    def test_complete_profile_preserves_weakest_pillars_and_readiness(self):
        result = gap_calc.run(self.profile([400, 300, 400, 300, 500]))
        self.assertEqual(result["weakest_pillar"], {
            "level": 300,
            "pillars": ["Business strategy", "Technology and data"],
        })
        self.assertIn("Meets or exceeds target", result["combined"]["verdict"])
        self.assertIn(
            "Weakest pillar (ceiling): Business strategy, Technology and data at 300",
            gap_calc.to_markdown(result),
        )


if __name__ == "__main__":
    unittest.main()
