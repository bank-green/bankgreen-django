import copy
import io
import json
from datetime import timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

import requests

from brand.models import Brand
from brand.models.commentary import Commentary
from brand.tests.test_data.feature_json import dummy_all_features
from brand.utils.harvest_data import HARVEST_REQUIRED_SECTIONS, update_commentary_feature_data

HARVEST_GET = "brand.utils.harvest_data.requests.get"
HARVEST_LOGGER = "brand.utils.harvest_data"


def make_harvest_response(status_code, body):
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode()
    response.url = "https://harvest.bank.green/harvest"
    return response


def make_valid_harvest_data():
    data = copy.deepcopy(dummy_all_features)
    data["institutional_information"] = {
        "year_founded": {"founded": 1990, "additional_details": ""},
        "location": {
            "licensed_to_operate_in": [],
            "physical_branches": [],
            "additional_details": "",
        },
    }
    data["policies"] = {
        "environmental_policy": {"offered": True, "additional_details": "", "urls": []},
        "deposit_protection": {
            "offered": True,
            "additional_details": "",
            "urls": [],
            "insuring_institution": "FDIC",
        },
    }
    return data


def make_error_response():
    return make_harvest_response(500, {"error": "Error communicating with external API"})


class HarvestFeatureDataTestCase(TestCase):
    def setUp(self):
        self.original_feature_json = {"existing": "data"}
        self.original_refresh_date = timezone.now() - timedelta(days=30)
        brand = Brand.objects.create(name="Harvest Bank", tag="harvest_bank")
        self.commentary = Commentary.objects.create(
            brand=brand,
            feature_json=self.original_feature_json,
            feature_refresh_date=self.original_refresh_date,
            show_on_sustainable_banks_page=True,
        )

    def assert_commentary_unchanged(self):
        self.commentary.refresh_from_db()
        self.assertEqual(self.commentary.feature_json, self.original_feature_json)
        self.assertEqual(self.commentary.feature_refresh_date, self.original_refresh_date)

    def assert_rejected(self, response):
        with (
            patch(HARVEST_GET, return_value=response),
            self.assertLogs(HARVEST_LOGGER, level="ERROR") as logs,
        ):
            result = update_commentary_feature_data(self.commentary, overwrite=True)
        self.assertIsNone(result)
        self.assertEqual(len(logs.output), 1)
        self.assert_commentary_unchanged()
        return logs.output[0]

    def test_http_500_is_not_saved(self):
        message = self.assert_rejected(make_error_response())
        self.assertIn("HTTP 500", message)
        self.assertIn("Error communicating with external API", message)

    def test_http_401_is_not_saved(self):
        message = self.assert_rejected(make_harvest_response(401, {"detail": "Invalid token"}))
        self.assertIn("HTTP 401", message)
        self.assertIn("Invalid token", message)

    def test_missing_section_is_not_saved(self):
        data = make_valid_harvest_data()
        del data["policies"]
        message = self.assert_rejected(make_harvest_response(200, data))
        self.assertIn("policies", message)

    def test_empty_sections_are_not_saved(self):
        data = {section: {} for section in HARVEST_REQUIRED_SECTIONS}
        self.assert_rejected(make_harvest_response(200, data))

    def test_valid_data_is_saved(self):
        data = make_valid_harvest_data()
        with patch(HARVEST_GET, return_value=make_harvest_response(200, data)):
            result = update_commentary_feature_data(self.commentary, overwrite=True)
        self.assertEqual(result, self.commentary)
        self.commentary.refresh_from_db()
        self.assertEqual(self.commentary.feature_json, data)
        self.assertGreater(self.commentary.feature_refresh_date, self.original_refresh_date)

    def test_extra_top_level_keys_are_saved(self):
        data = make_valid_harvest_data()
        data["interest_rates"] = {"rates": []}
        with patch(HARVEST_GET, return_value=make_harvest_response(200, data)):
            result = update_commentary_feature_data(self.commentary, overwrite=True)
        self.assertEqual(result, self.commentary)
        self.commentary.refresh_from_db()
        self.assertEqual(self.commentary.feature_json, data)


class RefreshSfiHarvestDataCommandTestCase(TestCase):
    def setUp(self):
        self.commentaries = [
            Commentary.objects.create(
                brand=Brand.objects.create(name=f"Bank {i}", tag=f"bank_{i}"),
                show_on_sustainable_banks_page=True,
            )
            for i in range(12)
        ]

    def run_command(self, stdout=None):
        call_command(
            "refresh_sfi_harvest_data", stdout=stdout or io.StringIO(), stderr=io.StringIO()
        )

    def test_raises_on_failure(self):
        responses = [make_harvest_response(200, make_valid_harvest_data())] * 11
        responses.append(make_error_response())
        with (
            patch(HARVEST_GET, side_effect=responses),
            self.assertLogs(HARVEST_LOGGER, level="ERROR"),
        ):
            with self.assertRaisesMessage(CommandError, "Done. Success: 11, Failed: 1"):
                self.run_command()

    def test_succeeds_when_all_saved(self):
        stdout = io.StringIO()
        response = make_harvest_response(200, make_valid_harvest_data())
        with patch(HARVEST_GET, return_value=response):
            self.run_command(stdout)
        self.assertIn("Done. Success: 12, Failed: 0", stdout.getvalue())

    def test_aborts_when_first_banks_fail(self):
        with (
            patch(HARVEST_GET, return_value=make_error_response()) as mock_get,
            self.assertLogs(HARVEST_LOGGER, level="ERROR"),
        ):
            with self.assertRaisesMessage(CommandError, "Aborted: 10 banks failed in a row"):
                self.run_command()
        self.assertEqual(mock_get.call_count, 10)

    def test_aborts_when_harvest_fails_mid_run(self):
        responses = [make_harvest_response(200, make_valid_harvest_data())] * 2
        responses += [make_error_response()] * 10
        with (
            patch(HARVEST_GET, side_effect=responses),
            self.assertLogs(HARVEST_LOGGER, level="ERROR"),
        ):
            with self.assertRaisesMessage(
                CommandError, "Aborted: 10 banks failed in a row. Success: 2, Failed: 10"
            ):
                self.run_command()

    def test_success_resets_consecutive_failures(self):
        valid = make_harvest_response(200, make_valid_harvest_data())
        responses = [make_error_response()] * 9 + [valid] + [make_error_response()] * 2
        with (
            patch(HARVEST_GET, side_effect=responses),
            self.assertLogs(HARVEST_LOGGER, level="ERROR"),
        ):
            with self.assertRaisesMessage(CommandError, "Done. Success: 1, Failed: 11"):
                self.run_command()
