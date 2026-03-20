from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.clientes.permissions import IsOwner
from apps.clientes.serializers import (
    ClienteSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpdateClienteSerializer,
)


class RegisterView(APIView):
    """Endpoint para registrar un nuevo cliente."""
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            cliente = serializer.save()
            refresh = RefreshToken.for_user(cliente)
            
            return Response({
                'mensaje': 'Cliente registrado exitosamente.',
                'cliente': ClienteSerializer(cliente).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Endpoint para iniciar sesión."""
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            cliente = serializer.validated_data['cliente']
            refresh = RefreshToken.for_user(cliente)
            
            return Response({
                'mensaje': 'Inicio de sesión exitoso.',
                'cliente': ClienteSerializer(cliente).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class MeView(generics.RetrieveUpdateAPIView):
    """Endpoint para obtener y actualizar datos del cliente autenticado."""
    serializer_class = ClienteSerializer
    permission_classes = [IsOwner]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateClienteSerializer
        return ClienteSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'mensaje': 'Datos actualizados exitosamente.',
                'cliente': ClienteSerializer(instance).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshViewCustom(TokenRefreshView):
    """Endpoint personalizado para renovar el token de acceso."""
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
