from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .educational_content.models import EducationalContent, PaymentScheduleItem  # noqa: F401
from .request_models import ContractRequest, BidMinute  # noqa: F401
from .doctoral_models import DoctoralContract  # noqa: F401
from .finance_models import DisbursementOrder  # noqa: F401
from .security_models import AuthSession, DownloadGrant, SecurityPolicy, LoginAttempt  # noqa: F401


class Role(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='permissions',
    )
    feature = models.SlugField(max_length=80)
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_download = models.BooleanField(default=False)

    class Meta:
        ordering = ['role__name', 'feature']
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'feature'],
                name='unique_role_feature_permission',
            ),
        ]

    def __str__(self):
        return f'{self.role.code}: {self.feature}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        related_name='profiles',
        null=True,
        blank=True,
    )
    bio = models.CharField(max_length=255, blank=True)
    must_change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} profile'


@receiver(post_save, sender=User)
def create_profile_and_token(sender, instance, created, **kwargs):
    if created:
        role = Role.objects.filter(code='admin').first() if instance.is_superuser else None
        Profile.objects.create(user=instance, role=role)



class PaymentScheduleRowBase(models.Model):
    label = models.CharField(max_length=250, blank=True, default='')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.pk} — {self.amount} @ {self.due_date}'
