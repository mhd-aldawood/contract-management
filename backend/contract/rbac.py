from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import RolePermission


FEATURES = [
    {'code': 'contract-requests', 'name': 'Create Contract', 'nameAr': 'إضافة عقد'},
    {'code': 'doctoral-contracts', 'name': 'Doctoral Contracts', 'nameAr': 'عقد الدكتوراه'},
    {'code': 'home', 'name': 'Home', 'nameAr': 'الرئيسية'},
    {'code': 'profile', 'name': 'Profile', 'nameAr': 'الحساب'},
    {'code': 'settings', 'name': 'Settings', 'nameAr': 'الإعدادات'},
    {'code': 'about', 'name': 'About', 'nameAr': 'حول'},
    {'code': 'planning', 'name': 'Planning', 'nameAr': 'التخطيط'},
    {'code': 'finance', 'name': 'Finance and Disbursement Orders', 'nameAr': 'المالية وأوامر الصرف'},
    {'code': 'dean', 'name': 'Dean Agreement Review', 'nameAr': 'العميد ومراجعة الاتفاقيات'},
    {'code': 'nafath-centers', 'name': 'Nafath Centers', 'nameAr': 'مراكز النفاذ'},
    {'code': 'memorandum', 'name': 'Memorandum', 'nameAr': 'مذكرة تفاهم'},
    {'code': 'lifelong-learning', 'name': 'Lifelong Learning', 'nameAr': 'التعلم مدى الحياة'},
    {'code': 'other-agreements', 'name': 'Other Agreements', 'nameAr': 'اتفاقيات أخرى'},
    {'code': 'educational-content', 'name': 'Educational Content', 'nameAr': 'المحتوى التعليمي'},
    {'code': 'access-control', 'name': 'Access Control', 'nameAr': 'إدارة الصلاحيات'},
    {'code': 'user-management', 'name': 'User Management', 'nameAr': 'إدارة المستخدمين'},
    {'code': 'security-settings', 'name': 'Security Settings', 'nameAr': 'إعدادات الأمان'},
]
FEATURE_CODES = {feature['code'] for feature in FEATURES}
DOWNLOAD_FEATURES = {'doctoral-contracts', 'planning', 'finance', 'dean', 'nafath-centers', 'memorandum', 'lifelong-learning', 'other-agreements', 'educational-content'}
for feature in FEATURES:
    feature['supportsDownload'] = feature['code'] in DOWNLOAD_FEATURES


def is_admin_user(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(getattr(user, 'profile', None), 'role', None) is not None and user.profile.role.code == 'admin'


def user_has_feature_permission(user, feature, action='read'):
    if not user or not user.is_authenticated or not user.is_active or feature not in FEATURE_CODES:
        return False
    profile = getattr(user, 'profile', None)
    if profile is None or profile.must_change_password:
        return False
    if is_admin_user(user):
        return True

    role = profile.role
    if role is None:
        return False

    if action not in {'read', 'write', 'download'}:
        return False
    if action == 'download':
        return feature in DOWNLOAD_FEATURES and RolePermission.objects.filter(role=role, feature=feature, can_read=True, can_download=True).exists()
    field = 'can_write' if action == 'write' else 'can_read'
    return RolePermission.objects.filter(
        role=role,
        feature=feature,
        **{field: True},
    ).exists()


class HasFeaturePermission(BasePermission):
    message = 'You do not have permission to use this feature.'

    def has_permission(self, request, view):
        feature = getattr(view, 'feature_code', None)
        if not feature:
            return False
        action = 'read' if request.method in SAFE_METHODS else 'write'
        return user_has_feature_permission(request.user, feature, action)


class IsAdminRole(BasePermission):
    message = 'Only administrators can manage roles and permissions.'

    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(
            profile
            and not profile.must_change_password
            and is_admin_user(request.user)
        )
