import unittest
from unittest.mock import Mock, patch

import main


class MainCliTests(unittest.TestCase):
    def test_parse_product_id(self):
        args = main.parse_args(["--product-id", "123456"])

        self.assertEqual(args.product_id, 123456)

    def test_parse_token(self):
        args = main.parse_args(["--token"])

        self.assertTrue(args.token)

    @patch("main.requests.get")
    @patch("main.login_and_load_categories")
    def test_fetch_auth_token_only_logs_in(self, login_mock, get_mock):
        login_mock.return_value = ("secret-token", set())

        result = main.fetch_auth_token()

        login_mock.assert_called_once_with(load_categories=False, verbose=False)
        get_mock.assert_not_called()
        self.assertEqual(result, "secret-token")

    @patch("main.requests.get")
    @patch("main.login_and_load_categories")
    def test_fetch_single_product_uses_authenticated_detail_endpoint(
        self, login_mock, get_mock
    ):
        login_mock.return_value = ("secret-token", set())
        response = Mock(status_code=200)
        response.json.return_value = {"produto_id": 123456}
        get_mock.return_value = response

        result = main.fetch_single_product(123456)

        login_mock.assert_called_once_with(load_categories=False)
        get_mock.assert_called_once_with(
            f"{main.PRODUCTS_URL}/123456",
            headers=main.build_headers("secret-token"),
            timeout=30,
        )
        self.assertEqual(result, {"produto_id": 123456})


if __name__ == "__main__":
    unittest.main()
