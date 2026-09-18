from unittest import TestCase

from person_scan.search import validate_request


class SearchValidationTests(TestCase):
    def test_valid_request_keeps_optional_email(self) -> None:
        request = validate_request(
            "Ada Lovelace", "1815-12-10", "Ada@Example.org"
        )

        self.assertEqual(request.subject.name, "Ada Lovelace")
        self.assertEqual(request.email, "ada@example.org")

    def test_invalid_email_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_request(
                "Ada Lovelace", "1815-12-10", "not-an-email"
            )
