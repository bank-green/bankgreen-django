from rest_framework.response import Response
from rest_framework.views import APIView
from brand.models import BrandSuggestion
from brand.models.contact import Contact
from .serializers import BrandSuggestionSerializer
from rest_framework import permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


class GenerateUserAuthToken(ObtainAuthToken):
    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid(self):
            return Response(
                {"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            username=serializer.data["username"], password=serializer.data["password"]
        )

        if not user:
            return Response(
                {"status": False, "message": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {"status": 200, "message": "Token generated", "token": str(token)},
            status=status.HTTP_201_CREATED,
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
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        brand = request.query_params.get("brand")
        contacts = (
            [contact.email for contact in Contact.objects.filter(brand_tag=brand)]
            if brand
            else [contact.email for contact in Contact.objects.all()]
        )
        return Response(contacts)
