"""
Serializers for the accounts app: registration, login, profile,
password change and password reset.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """Shared base with the identity fields every user serializer exposes."""

    full_name = serializers.ReadOnlyField(
        help_text="First and last name combined, or the username if no name is set."
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']


class UserSerializer(BaseUserSerializer):
    """Full profile serializer, used to view and update the current user."""

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + [
            'phone', 'date_of_birth', 'bio', 'profile_picture',
            'travel_preferences', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'phone': {'help_text': 'Contact phone number.'},
            'bio': {'help_text': 'Short traveler bio (max 500 characters).'},
            'travel_preferences': {
                'help_text': "Preferences used for recommendations, e.g. {'climate': 'tropical'}."
            },
        }

    def validate_email(self, value):
        """Emails must be unique, ignoring case and the user's own current email."""
        value = value.lower()
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_travel_preferences(self, value):
        """Preferences must be a JSON object, not a list or string."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Travel preferences must be a JSON object.')
        return value

    def update(self, instance, validated_data):
        """Delete the old profile picture from disk when it is replaced."""
        new_picture = validated_data.get('profile_picture')
        if new_picture and instance.profile_picture:
            instance.profile_picture.delete(save=False)
        return super().update(instance, validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Creates a new user. Passwords are write-only and never returned."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Must pass Django password validation (min 8 chars, not too common).',
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Repeat the password to confirm it.',
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2']
        read_only_fields = ['id']

    def validate_email(self, value):
        """Reject emails already registered, ignoring case."""
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        """Make sure both password fields match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        """Create the user with a properly hashed password."""
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validates login credentials. Authentication happens in the view."""

    username = serializers.CharField(help_text='Your username.')
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Your password.',
    )


class ChangePasswordSerializer(serializers.Serializer):
    """Lets a logged-in user change their password."""

    old_password = serializers.CharField(write_only=True, help_text='Your current password.')
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text='Your new password.',
    )

    def validate_old_password(self, value):
        """The old password must match the logged-in user's password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Step 1 of password reset: the email to send the reset link to."""

    email = serializers.EmailField(help_text='Email address of the account.')


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Step 2 of password reset: the emailed uid and token plus a new password."""

    uid = serializers.CharField(help_text='User id from the reset email.')
    token = serializers.CharField(help_text='Reset token from the reset email.')
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text='The new password.',
    )