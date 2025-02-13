from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from brand.models import BrandSuggestion
from brand.models.brand import Brand
from brand.models.commentary import Commentary
from brand.models.contact import Contact

from .authentication import SingleTokenAuthentication
from .serializers import (
    BrandSerializer,
    BrandSuggestionSerializer,
    CommentaryFeatureOverrideSerializer,
    ContactSerializer,
)


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


class CommentaryFeatureOverride(APIView):
    permission_classes = []
    authentication_classes = [SingleTokenAuthentication]
    renderer_classes = [JSONRenderer]

    def get(self, request, pk):
        if not pk:
            return Response(
                {"error": "Commentary Id missing in request url."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        commentary_instance = Commentary.objects.filter(pk=pk).first()
        if not commentary_instance:
            return Response(
                {"error": "Commentary does not exsist"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = CommentaryFeatureOverrideSerializer(commentary_instance)

        return Response(serializer.data.get("feature_override"))
