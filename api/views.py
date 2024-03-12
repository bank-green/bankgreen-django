from rest_framework.response import Response
from rest_framework.views import APIView
from brand.models import BrandSuggestion, Brand
from .serializers import BrandSuggestionSerializer
from rest_framework import permissions, status


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


class BrandGetMethod(APIView):
    def get(self,request):
        requested_bank = self.request.query_params.get("bank_name")
        data = Brand.objects.all().filter(name=requested_bank)
        if data:
            data = data[0]
            return Response(data.tag)
        return Response("Bank Tag not available")
   