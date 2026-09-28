"""
Views for the accounts app: registration, login, profile,
password change and password reset.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


def get_tokens_for_user(user):
    """Return a refresh/access JWT pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@extend_schema(request=UserRegistrationSerializer, responses={201: UserSerializer})
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and return their profile plus JWT tokens.

    Example request:
        POST /api/v1/accounts/register/
        {"username": "cait", "email": "cait@example.com",
         "password": "StrongPass123", "password2": "StrongPass123"}
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'user': UserSerializer(user).data, 'tokens': get_tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=LoginSerializer, responses={200: UserSerializer})
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Log in with username and password and return the profile plus JWT tokens.

    Example request:
        POST /api/v1/accounts/login/
        {"username": "cait", "password": "StrongPass123"}
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(
        request=request,
        username=serializer.validated_data['username'],
        password=serializer.validated_data['password'],
    )
    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return Response({'user': UserSerializer(user).data, 'tokens': get_tokens_for_user(user)})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the logged-in user's profile.

    GET /api/v1/accounts/profile/ returns the profile.
    PATCH /api/v1/accounts/profile/ updates any of its fields.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """A user can only ever see and edit their own profile."""
        return self.request.user


class ChangePasswordView(APIView):
    """Change the logged-in user's password."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={200: None})
    def post(self, request):
        """
        Example request:
            POST /api/v1/accounts/password/change/
            {"old_password": "StrongPass123", "new_password": "EvenStronger456"}
        """
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'detail': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Start a password reset by emailing the user a uid and token.

    Always returns the same message whether or not the email exists,
    so attackers cannot use this endpoint to discover registered emails.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    generic_response = Response(
        {'detail': 'If that email is registered, a reset link has been sent.'}
    )
    try:
        user = User.objects.get(email__iexact=serializer.validated_data['email'])
    except User.DoesNotExist:
        return generic_response

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    send_mail(
        subject='Password reset',
        message=f'Use these to reset your password.\nuid: {uid}\ntoken: {token}',
        from_email=None,  # falls back to DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )
    return generic_response


@extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Finish a password reset using the uid and token from the reset email.

    Example request:
        POST /api/v1/accounts/password/reset/confirm/
        {"uid": "MQ", "token": "abc123-xyz", "new_password": "EvenStronger456"}
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    invalid_link = Response(
        {'error': 'Invalid or expired reset link.'},
        status=status.HTTP_400_BAD_REQUEST,
    )
    try:
        user_id = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return invalid_link

    if not default_token_generator.check_token(user, serializer.validated_data['token']):
        return invalid_link

    user.set_password(serializer.validated_data['new_password'])
    user.save()
    return Response({'detail': 'Password has been reset.'})