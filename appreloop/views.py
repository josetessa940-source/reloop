from rest_framework import generics
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from .serializers import LoginSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status



class RegisterAPI(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            return Response(
                {
                    'message': 'Login successful',
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username,
                    'role': user.role
                },
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()

        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )

class UserDetailsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, status=status.HTTP_200_OK)