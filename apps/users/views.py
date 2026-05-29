from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from drf_yasg.utils import swagger_auto_schema

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Mening profilim")
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)