import logging
from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

import graphene.test
from rest_framework.test import APIClient

from impact.models.switch_survey_emails import SwitchSurveyEmail
from impact.models.switch_survey import SwitchSurveySubmission
from impact.models.switch_survey_planning import SwitchSurveyPlanning
from impact.utils.mailerlite import subscribe
from impact.utils.turnstile import verify_token
from schema import schema


def setUpModule():
    logging.getLogger("impact.utils").setLevel(logging.CRITICAL)


def tearDownModule():
    logging.getLogger("impact.utils").setLevel(logging.NOTSET)


class SwitchSurveySubmissionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("rest_api:impact_survey")
        self.valid_payload = {
            "moved_from_bank_name": "Barclays",
            "moved_to_bank_name": "Triodos Bank",
            "amount": "5000.00",
            "currency": "GBP",
            "turnstile_token": "test-token",
            "is_agree_privacy": True,
        }
        patcher = patch("api.views.verify_token", return_value=True)
        self.mock_verify_token = patcher.start()
        self.addCleanup(patcher.stop)

    def test_post_valid_submission_returns_201(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, 201)

    def test_post_valid_submission_saves_record(self):
        self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(SwitchSurveySubmission.objects.count(), 1)
        submission = SwitchSurveySubmission.objects.first()
        self.assertEqual(submission.moved_from_bank_name, "Barclays")
        self.assertEqual(submission.moved_to_bank_name, "Triodos Bank")
        self.assertEqual(str(submission.amount), "5000.00")
        self.assertEqual(submission.currency, "GBP")
        self.assertTrue(submission.is_agree_privacy)
        self.assertFalse(submission.is_agree_marketing)

    def test_post_without_is_agree_privacy_and_no_email_returns_201(self):
        payload = self.valid_payload.copy()
        del payload["is_agree_privacy"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(SwitchSurveySubmission.objects.first().is_agree_privacy)

    def test_post_with_email_and_is_agree_privacy_false_returns_400(self):
        payload = {**self.valid_payload, "email": "test@example.com", "is_agree_privacy": False}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_returns_uuid(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertIn("uuid", response.json())

    def test_post_missing_required_field_returns_400(self):
        payload = self.valid_payload.copy()
        del payload["amount"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_amount_below_minimum_returns_400(self):
        for amount in ["-10000.00", "0.00", "0.009"]:
            with self.subTest(amount=amount):
                response = self.client.post(
                    self.url, {**self.valid_payload, "amount": amount}, format="json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(SwitchSurveySubmission.objects.count(), 0)

    def test_post_invalid_currency_returns_400(self):
        payload = {**self.valid_payload, "currency": "JPY"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_with_tags_resolves_brand(self):
        from brand.tests.utils import create_test_brands

        brand1, _ = create_test_brands()
        payload = {
            **self.valid_payload,
            "moved_from_tag": "unmatched-tag",
            "moved_to_tag": brand1.tag,
        }
        self.client.post(self.url, payload, format="json")
        submission = SwitchSurveySubmission.objects.first()
        self.assertIsNone(submission.moved_from_brand)
        self.assertEqual(submission.moved_to_brand, brand1)

    def test_post_with_email_saves_follow_up(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.return_value = MagicMock(ok=True)
            self.client.post(
                self.url,
                {**self.valid_payload, "email": "test@example.com", "is_agree_marketing": True},
                format="json",
            )
        self.assertEqual(SwitchSurveyEmail.objects.count(), 1)
        follow_up = SwitchSurveyEmail.objects.first()
        self.assertEqual(follow_up.email, "test@example.com")
        self.assertEqual(follow_up.submission, SwitchSurveySubmission.objects.first())

    def test_post_with_email_sets_mailerlite_synced(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.return_value = MagicMock(ok=True)
            self.client.post(
                self.url,
                {**self.valid_payload, "email": "test@example.com", "is_agree_marketing": True},
                format="json",
            )
        self.assertTrue(SwitchSurveyEmail.objects.first().mailerlite_synced)

    def test_post_with_marketing_consent_subscribes_to_switched_group(self):
        with (
            patch("impact.utils.mailerlite.requests.request") as mock_request,
            self.settings(
                MAILERLITE_SWITCHED_GROUP_ID="111111111111111111",
                MAILERLITE_PLANNING_TO_SWITCH_GROUP_ID="222222222222222222",
            ),
        ):
            mock_request.return_value = MagicMock(ok=True)
            self.client.post(
                self.url,
                {**self.valid_payload, "email": "test@example.com", "is_agree_marketing": True},
                format="json",
            )
        posts = [c for c in mock_request.call_args_list if c.args[0] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].kwargs["json"]["groups"], [111111111111111111])

    def test_post_with_email_but_no_marketing_consent_retains_address_without_subscribing(self):
        with (
            patch("api.views.subscribe") as mock_subscribe,
            patch("api.views.unsubscribe_from_group"),
        ):
            response = self.client.post(
                self.url, {**self.valid_payload, "email": "test@example.com"}, format="json"
            )
        self.assertEqual(response.status_code, 201)
        follow_up = SwitchSurveyEmail.objects.get()
        self.assertEqual(follow_up.email, "test@example.com")
        self.assertFalse(follow_up.mailerlite_synced)
        mock_subscribe.assert_not_called()
        self.assertFalse(follow_up.submission.is_agree_marketing)

    def test_post_with_invalid_email_returns_400(self):
        payload = {**self.valid_payload, "email": "not-an-email"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_without_email_creates_no_follow_up(self):
        self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(SwitchSurveyEmail.objects.count(), 0)

    def test_post_with_email_removes_from_planning_group(self):
        with (
            patch("impact.utils.mailerlite.requests.request") as mock_request,
            self.settings(MAILERLITE_PLANNING_TO_SWITCH_GROUP_ID="222222222222222222"),
        ):
            mock_request.side_effect = [
                MagicMock(
                    ok=True, status_code=200, json=lambda: {"data": {"id": "31986843064993537"}}
                ),
                MagicMock(ok=True, status_code=204),
            ]
            self.client.post(
                self.url, {**self.valid_payload, "email": "test@example.com"}, format="json"
            )
        lookup, delete = mock_request.call_args_list
        self.assertEqual(lookup.args[0], "GET")
        self.assertEqual(delete.args[0], "DELETE")
        self.assertIn("/subscribers/31986843064993537/groups/222222222222222222", delete.args[1])
        self.assertNotIn("test@example.com", delete.args[1])

    def test_post_with_email_never_subscribed_makes_no_delete_call(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.return_value = MagicMock(ok=False, status_code=404, text="Not Found")
            response = self.client.post(
                self.url, {**self.valid_payload, "email": "test@example.com"}, format="json"
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(mock_request.call_count, 1)
        self.assertEqual(mock_request.call_args.args[0], "GET")

    def test_post_without_email_does_not_call_unsubscribe(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            self.client.post(self.url, self.valid_payload, format="json")
        mock_request.assert_not_called()

    def test_post_mailerlite_4xx_handling(self):
        with (
            patch("impact.utils.mailerlite.requests.request") as mock_request,
            patch("impact.utils.mailerlite.logger") as mock_logger,
        ):
            mock_request.return_value = MagicMock(ok=False, status_code=401, text="Unauthorized")
            response = self.client.post(
                self.url,
                {**self.valid_payload, "email": "test@example.com", "is_agree_marketing": True},
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SwitchSurveySubmission.objects.count(), 1)
        self.assertFalse(SwitchSurveyEmail.objects.first().mailerlite_synced)
        self.assertTrue(SwitchSurveySubmission.objects.first().is_agree_marketing)
        self.assertEqual(mock_logger.error.call_count, 2)

    def test_post_follow_up_create_failure_rolls_back_and_returns_500(self):
        with (
            patch("api.views.SwitchSurveyEmail.objects.create") as mock_create,
            patch("api.views.logger") as mock_logger,
        ):
            mock_create.side_effect = Exception("DB error")
            response = self.client.post(
                self.url,
                {**self.valid_payload, "email": "test@example.com", "is_agree_marketing": True},
                format="json",
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(SwitchSurveySubmission.objects.count(), 0)
        mock_logger.error.assert_called_once()

    def test_post_without_turnstile_token_returns_400(self):
        payload = self.valid_payload.copy()
        del payload["turnstile_token"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_with_failed_turnstile_verification_returns_400_and_creates_nothing(self):
        self.mock_verify_token.return_value = False
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SwitchSurveySubmission.objects.count(), 0)

    def test_post_passes_token_to_verify_token(self):
        self.client.post(self.url, self.valid_payload, format="json")
        self.mock_verify_token.assert_called_once()
        args, kwargs = self.mock_verify_token.call_args
        self.assertEqual(args[0], "test-token")
        self.assertNotIn("remote_ip", kwargs)


class SwitchSurveyPlanningAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("rest_api:impact_survey_planning")
        self.valid_payload = {
            "email": "test@example.com",
            "turnstile_token": "test-token",
            "is_agree_privacy": True,
        }
        patcher = patch("api.views.verify_token", return_value=True)
        self.mock_verify_token = patcher.start()
        self.addCleanup(patcher.stop)

    def test_post_valid_submission_returns_201(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, 201)

    def test_post_valid_submission_saves_record(self):
        self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(SwitchSurveyPlanning.objects.count(), 1)
        planning = SwitchSurveyPlanning.objects.first()
        self.assertEqual(planning.email, "test@example.com")
        self.assertTrue(planning.is_agree_privacy)
        self.assertFalse(planning.is_agree_marketing)

    def test_post_returns_uuid(self):
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertIn("uuid", response.json())

    def test_post_missing_email_returns_400(self):
        payload = self.valid_payload.copy()
        del payload["email"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_invalid_email_returns_400(self):
        payload = {**self.valid_payload, "email": "not-an-email"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_without_is_agree_privacy_returns_400(self):
        payload = self.valid_payload.copy()
        del payload["is_agree_privacy"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_with_is_agree_privacy_false_returns_400(self):
        payload = {**self.valid_payload, "is_agree_privacy": False}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_without_turnstile_token_returns_400(self):
        payload = self.valid_payload.copy()
        del payload["turnstile_token"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_post_with_failed_turnstile_verification_returns_400_and_creates_nothing(self):
        self.mock_verify_token.return_value = False
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SwitchSurveyPlanning.objects.count(), 0)

    def test_post_without_marketing_consent_does_not_call_mailerlite(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            self.client.post(self.url, self.valid_payload, format="json")
            mock_request.assert_not_called()
        self.assertFalse(SwitchSurveyPlanning.objects.first().mailerlite_synced)

    def test_post_with_marketing_consent_subscribes_to_planning_group(self):
        with (
            patch("impact.utils.mailerlite.requests.request") as mock_request,
            self.settings(MAILERLITE_PLANNING_TO_SWITCH_GROUP_ID="222222222222222222"),
        ):
            mock_request.return_value = MagicMock(ok=True)
            self.client.post(
                self.url, {**self.valid_payload, "is_agree_marketing": True}, format="json"
            )
        self.assertTrue(SwitchSurveyPlanning.objects.first().mailerlite_synced)
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"]["groups"], [222222222222222222])

    def test_post_mailerlite_failure_still_returns_201(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.return_value = MagicMock(ok=False, status_code=401, text="Unauthorized")
            response = self.client.post(
                self.url, {**self.valid_payload, "is_agree_marketing": True}, format="json"
            )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(SwitchSurveyPlanning.objects.first().mailerlite_synced)


class TurnstileVerifyTokenTestCase(TestCase):
    def test_verify_token_returns_true_on_success(self):
        with patch("impact.utils.turnstile.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {"success": True})
            self.assertTrue(verify_token("some-token"))

    def test_verify_token_returns_false_when_body_says_failure(self):
        with patch("impact.utils.turnstile.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True, json=lambda: {"success": False, "error-codes": ["invalid-input-response"]}
            )
            self.assertFalse(verify_token("bad-token"))

    def test_verify_token_returns_false_on_missing_token(self):
        self.assertFalse(verify_token(""))
        self.assertFalse(verify_token(None))

    def test_verify_token_returns_false_on_request_exception(self):
        with patch("impact.utils.turnstile.requests.post") as mock_post:
            mock_post.side_effect = Exception("network error")
            self.assertFalse(verify_token("some-token"))

    def test_verify_token_missing_does_not_call_siteverify(self):
        with patch("impact.utils.turnstile.requests.post") as mock_post:
            verify_token("")
        mock_post.assert_not_called()

    def test_verify_token_sends_secret_and_token_only(self):
        with patch("impact.utils.turnstile.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {"success": True})
            verify_token("some-token")
        _, kwargs = mock_post.call_args
        self.assertEqual(set(kwargs["data"]), {"secret", "response"})
        self.assertEqual(kwargs["data"]["response"], "some-token")


class MailerLiteSubscribeTestCase(TestCase):
    def test_subscribe_returns_false_on_request_exception(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.side_effect = Exception("network error")
            self.assertFalse(subscribe("test@example.com"))

    def test_subscribe_uses_explicit_group_id_over_default(self):
        with patch("impact.utils.mailerlite.requests.request") as mock_request:
            mock_request.return_value = MagicMock(ok=True)
            subscribe("test@example.com", group_id="333333333333333333")
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["json"]["groups"], [333333333333333333])


class SwitchSurveyEmailCascadeTestCase(TestCase):
    def setUp(self):
        self.submission = SwitchSurveySubmission.objects.create(
            moved_from_bank_name="Barclays",
            moved_to_bank_name="Triodos Bank",
            amount="5000.00",
            currency="GBP",
        )
        SwitchSurveyEmail.objects.create(submission=self.submission, email="test@example.com")

    def test_deleting_submission_cascades_to_follow_up(self):
        self.submission.delete()
        self.assertEqual(SwitchSurveyEmail.objects.count(), 0)


class SwitchSurveyGraphQLTestCase(TestCase):
    def setUp(self):
        SwitchSurveySubmission.objects.create(
            moved_from_bank_name="Barclays",
            moved_to_bank_name="Triodos Bank",
            amount="5000.00",
            currency="GBP",
        )
        self.gql_client = graphene.test.Client(schema)

    def test_query_returns_submissions(self):
        query = """
        {
            switchSurveySubmissions {
                edges {
                    node {
                        uuid
                        movedFromBankName
                        movedToBankName
                        amount
                        currency
                    }
                }
            }
        }
        """
        res: Any = self.gql_client.execute(query)
        submissions = [edge["node"] for edge in res["data"]["switchSurveySubmissions"]["edges"]]
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0]["movedFromBankName"], "Barclays")
        self.assertEqual(submissions[0]["movedToBankName"], "Triodos Bank")
        self.assertEqual(submissions[0]["currency"], "GBP")
        self.assertIn("uuid", submissions[0])

    def test_query_resolves_moved_to_brand_when_matched(self):
        from brand.tests.utils import create_test_brands

        brand1, _ = create_test_brands()
        SwitchSurveySubmission.objects.create(
            moved_from_bank_name="Barclays",
            moved_to_bank_name=brand1.name,
            moved_to_brand=brand1,
            amount="100.00",
            currency="GBP",
        )
        query = """
        {
            switchSurveySubmissions {
                edges { node { movedToBankName movedToBrand { tag name } } }
            }
        }
        """
        res: Any = self.gql_client.execute(query)
        nodes = [edge["node"] for edge in res["data"]["switchSurveySubmissions"]["edges"]]
        matched = [n for n in nodes if n["movedToBrand"] is not None]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["movedToBrand"], {"tag": brand1.tag, "name": brand1.name})

    def test_query_moved_from_brand_null_when_unmatched(self):
        query = """
        {
            switchSurveySubmissions {
                edges { node { movedFromBankName movedFromBrand { tag } } }
            }
        }
        """
        res: Any = self.gql_client.execute(query)
        nodes = [edge["node"] for edge in res["data"]["switchSurveySubmissions"]["edges"]]
        self.assertEqual(len(nodes), 1)
        self.assertIsNone(nodes[0]["movedFromBrand"])
        self.assertIsNone(res.get("errors"))

    def test_query_filters_by_currency(self):
        SwitchSurveySubmission.objects.create(
            moved_from_bank_name="X", moved_to_bank_name="Y", amount="50.00", currency="USD"
        )
        query = "{ switchSurveySubmissions(currency: GBP) { edges { node { currency } } } }"
        res: Any = self.gql_client.execute(query)
        nodes = [edge["node"] for edge in res["data"]["switchSurveySubmissions"]["edges"]]
        self.assertTrue(all(n["currency"] == "GBP" for n in nodes))
        self.assertTrue(len(nodes) >= 1)

    def test_query_filters_by_created_range_excludes_out_of_range(self):
        query = """
        { switchSurveySubmissions(created_Gte: "2999-01-01T00:00:00") { edges { node { uuid } } } }
        """
        res: Any = self.gql_client.execute(query)
        nodes = [edge["node"] for edge in res["data"]["switchSurveySubmissions"]["edges"]]
        self.assertEqual(len(nodes), 0)

    def test_query_cannot_reach_respondent_emails_or_consent_flags(self):
        for field in ["emailFollowUps { email }", "isAgreePrivacy", "isAgreeMarketing"]:
            with self.subTest(field=field):
                query = "{ switchSurveySubmissions { edges { node { %s } } } }" % field
                res: Any = self.gql_client.execute(query)
                self.assertIsNotNone(res.get("errors"), f"{field} is queryable over public GraphQL")
                self.assertIsNone(res.get("data"))

    def test_query_first_exceeding_max_limit_returns_error(self):
        query = "{ switchSurveySubmissions(first: 5000) { edges { node { uuid } } } }"
        res: Any = self.gql_client.execute(query)
        self.assertIsNotNone(res.get("errors"))
        self.assertIn("1000", res["errors"][0]["message"])
