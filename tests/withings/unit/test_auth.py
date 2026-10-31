"""Unit tests for auth module."""

from __future__ import annotations

from unittest.mock import patch

from pace_ai.withings.auth import create_account


class TestCreateAccount:
    @patch("pace_ai.withings.auth.WithingsAccount")
    def test_create_account_default(self, mock_cls):
        mock_cls.return_value = "mock_account"
        result = create_account()
        mock_cls.assert_called_once_with()
        assert result == "mock_account"

    @patch("pace_ai.withings.auth.WithingsAccount")
    def test_create_account_with_folder(self, mock_cls):
        mock_cls.return_value = "mock_account"
        result = create_account("/tmp/withings")
        mock_cls.assert_called_once_with(config_folder="/tmp/withings")
        assert result == "mock_account"

    @patch("pace_ai.withings.auth.WithingsAccount")
    def test_create_account_empty_folder_uses_default(self, mock_cls):
        mock_cls.return_value = "mock_account"
        result = create_account("")
        mock_cls.assert_called_once_with()
        assert result == "mock_account"
