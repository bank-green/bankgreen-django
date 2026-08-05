import logging

from django.conf import settings
from django.db import transaction

from rest_framework import permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from brand.models import BrandSuggestion
from brand.models.brand import Brand
from brand.models.commentary import Commentary
from brand.models.contact import Contact
from impact.models.switch_survey_emails import SwitchSurveyEmail
from impact.models.switch_survey import SwitchSurveySubmission
from impact.utils.mailerlite import subscribe, unsubscribe_from_group
from impact.utils.turnstile import verify_token

from .authentication import SingleTokenAuthentication
from .serializers import (
    BrandSerializer,
    BrandSuggestionSerializer,
    CommentaryFeatureOverrideSerializer,
    ContactSerializer,
    SwitchSurveySubmissionSerializer,
)


logger = logging.getLogger(__name__)


class BrandSuggestionAPIView(APIView):
    permission = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        This function is being called when user makes GET http call. This function is responsible
        to display the data available in the database.
        return : serialized data
        """
        data = BrandSuggestion.objects.all()
        serializer = BrandSuggestionSerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        This function is being called when user makes POST http call. This function is responsible
        to add the data sent in the POST call into the database.
        return : serialized data if successful
               : error message if not successful.
        """
        serializer = BrandSuggestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    permission_classes = []
    authentication_classes = [SingleTokenAuthentication]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        brand_tag = request.query_params.get("brandTag")
        contacts_qs = (
            Contact.objects.all()
            if not brand_tag
            else Contact.objects.filter(commentary__brand__tag=brand_tag)
        )
        serializer = ContactSerializer(contacts_qs, many=True)
        return Response(serializer.data)


class BrandsView(APIView):
    permission_classes = []
    authentication_classes = [SingleTokenAuthentication]
    renderer_classes = [JSONRenderer]

    def put(self, request):
        # Fetching the tag from request.data, which is used to identify the brand
        tag = request.data.get("tag")
        if not tag:
            return Response(
                {"error": "Tag is required for updating a brand."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to retrieve an existing brand by 'tag'
        brand_instance = Brand.objects.filter(tag=tag).first()

        # Initialize the serializer with the instance (if found) or None (if not found)
        serializer = BrandSerializer(brand_instance, data=request.data, partial=True)

        if serializer.is_valid():
            # Save the brand instance
            brand_instance = serializer.save()

            # Update or create the related commentary if it's provided in the request data
            commentary_data = request.data.get("commentary")
            if commentary_data:
                commentary_instance, _ = Commentary.objects.update_or_create(
                    brand=brand_instance, defaults=commentary_data
                )

            status_code = status.HTTP_200_OK if brand_instance else status.HTTP_201_CREATED
            return Response(serializer.data, status=status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BrandFeatureOverride(APIView):
    permission_classes = []
    authentication_classes = [SingleTokenAuthentication]
    renderer_classes = [JSONRenderer]

    def get(self, request, brand_id):
        if not brand_id:
            return Response(
                {"error": "Brand Id missing in request url."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            commentary_instance = Commentary.objects.get(brand_id=brand_id)
        except:
            return Response(
                {"error": "Brand's Commentary does not exsist"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentaryFeatureOverrideSerializer(commentary_instance)

        return Response(serializer.data.get("feature_override"))

    def put(self, request, brand_id):
        if not brand_id:
            return Response(
                {"error": "Brand Id missing in request url."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            commentary_instance = Commentary.objects.get(brand_id=brand_id)
        except:
            return Response(
                {"error": "Brand's Commentary does not exsist"}, status=status.HTTP_404_NOT_FOUND
            )

        commentary_instance = Commentary.objects.filter(pk=brand_id).first()
        serializer = CommentaryFeatureOverrideSerializer(
            commentary_instance, data={"feature_override": request.data}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data["feature_override"], status=status.HTTP_200_OK)
        return Response(
            {"error": serializer.errors["feature_override"]}, status=status.HTTP_400_BAD_REQUEST
        )


class SwitchSurveyView(APIView):
    permission_classes = []
    authentication_classes = []
    renderer_classes = [JSONRenderer]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = SwitchSurveySubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        turnstile_token = serializer.validated_data.get("turnstile_token")
        if not verify_token(turnstile_token):
            return Response(
                {"error": "Turnstile verification failed"}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data.get("email")
        agree_marketing = serializer.validated_data.get("is_agree_marketing")

        try:
            with transaction.atomic():
                submission = serializer.save()
                follow_up = None
                # Retain the address whenever one is given, even without marketing consent,
                # so we can contact the respondent to clarify their submitted survey data.
                # Marketing consent gates the MailerLite subscription below, nothing else.
                if email:
                    follow_up = SwitchSurveyEmail.objects.create(
                        submission=submission, email=email
                    )
        except Exception as e:
            logger.error(f"Failed to save switch survey submission: {e}")
            return Response(
                {"error": "Could not save submission"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if follow_up and agree_marketing and subscribe(email):
            follow_up.mailerlite_synced = True
            follow_up.save(update_fields=["mailerlite_synced"])

        if email:
            unsubscribe_from_group(email, settings.MAILERLITE_PLANNING_TO_SWITCH_GROUP_ID)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SwitchSurveyPlanningView(APIView):
    permission_classes = []
    authentication_classes = []
    renderer_classes = [JSONRenderer]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = SwitchSurveyPlanningSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        turnstile_token = serializer.validated_data.get("turnstile_token")
        if not verify_token(turnstile_token):
            return Response(
                {"error": "Turnstile verification failed"}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data.get("email")
        agree_marketing = serializer.validated_data.get("is_agree_marketing")

        try:
            planning = serializer.save()
        except Exception as e:
            logger.error(f"Failed to save switch survey planning signup: {e}")
            return Response(
                {"error": "Could not save submission"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if agree_marketing and subscribe(
            email, group_id=settings.MAILERLITE_PLANNING_TO_SWITCH_GROUP_ID
        ):
            planning.mailerlite_synced = True
            planning.save(update_fields=["mailerlite_synced"])

        return Response(serializer.data, status=status.HTTP_201_CREATED)
