from rest_framework import serializers
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.authentication import policy
from contract.rbac import HasFeaturePermission, IsAdminRole
from contract.security_models import SecurityPolicy


class SecurityPolicySerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['Expected a JSON object.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: ['Unknown setting.'] for key in unknown})
        return super().to_internal_value(data)

    downloadSeconds = serializers.IntegerField(source='download_seconds', min_value=5, max_value=3600)
    accessMinutes = serializers.IntegerField(source='access_minutes', min_value=1, max_value=60)
    sessionHours = serializers.IntegerField(source='session_hours', min_value=1, max_value=168)
    rememberDays = serializers.IntegerField(source='remember_days', min_value=1, max_value=90)
    allowRemember = serializers.BooleanField(source='allow_remember')

    class Meta:
        model = SecurityPolicy
        fields = ['downloadSeconds', 'accessMinutes', 'sessionHours', 'rememberDays', 'allowRemember']


class SecuritySettingsView(APIView):
    permission_classes = [IsAdminRole, HasFeaturePermission]
    feature_code = 'security-settings'

    def get(self, request):
        return success_response(request=request, code='request.success', data=SecurityPolicySerializer(policy()).data)

    def patch(self, request):
        serializer = SecurityPolicySerializer(policy(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(request=request, code='request.success', data=serializer.data)
