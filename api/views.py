from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from brand.models import BrandSuggestion
from brand.models.contact import Contact

from .authentication import SingleTokenAuthentication
from .serializers import BrandSuggestionSerializer, ContactSerializer


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
