from datetime import date
import unittest

from person_scan.core import (
    Source,
    Subject,
    assess_finding,
    extract_page,
    validate_sources,
)


SUBJECT = Subject("Ada Lovelace", date(1815, 12, 10))
SOURCE = Source("Testseite", "https://example.org/ada")


class CoreTests(unittest.TestCase):
    def test_exact_name_and_birth_date_is_match(self) -> None:
        finding = assess_finding(
            SUBJECT,
            SOURCE,
            "Ada",
            "Ada Lovelace, geboren am 10.12.1815",
        )

        self.assertEqual(finding.status, "match")
        self.assertEqual(finding.score, 1.0)
        self.assertEqual(finding.matched_fields, ("name", "birth_date"))

    def test_name_without_birth_date_requires_manual_review(self) -> None:
        finding = assess_finding(
            SUBJECT, SOURCE, "Ada", "Ada Lovelace war Mathematikerin."
        )

        self.assertEqual(finding.status, "manual_review")
        self.assertEqual(finding.score, 0.6)

    def test_script_and_style_content_is_ignored(self) -> None:
        title, text = extract_page(
            "<title>Profil</title><script>Ada Lovelace</script>"
            "<p>Ada</p><style>hidden</style>"
        )

        self.assertEqual(title, "Profil")
        self.assertEqual(text, "Profil Ada")

    def test_sources_must_use_http_or_https(self) -> None:
        with self.assertRaisesRegex(ValueError, r"HTTP\(S\)"):
            validate_sources([Source("lokal", "file:///tmp/profile.html")])


if __name__ == "__main__":
    unittest.main()
