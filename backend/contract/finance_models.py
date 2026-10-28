from functools import reduce
from operator import or_

from django.conf import settings
from django.db import models

from contract.helper import UploadToPath


ORDER_RELATIONS = ('nafath_agreement', 'lifelong_agreement', 'educational_agreement', 'other_agreement', 'doctoral_contract')

class DisbursementOrder(models.Model):
    doctoral_contract = models.ForeignKey('contract.DoctoralContract', null=True, blank=True, on_delete=models.CASCADE, related_name='disbursement_orders')
    nafath_agreement = models.ForeignKey('contract.NafathCenterAgreement', null=True, blank=True, on_delete=models.CASCADE, related_name='disbursement_orders')
    lifelong_agreement = models.ForeignKey('contract.LifeLongAgreement', null=True, blank=True, on_delete=models.CASCADE, related_name='disbursement_orders')
    educational_agreement = models.ForeignKey('contract.EducationalContent', null=True, blank=True, on_delete=models.CASCADE, related_name='disbursement_orders')
    other_agreement = models.ForeignKey('contract.Agreement', null=True, blank=True, on_delete=models.CASCADE, related_name='disbursement_orders')
    file = models.FileField(upload_to=UploadToPath('private/disbursement-orders'), max_length=512)
    file_name = models.CharField(max_length=512)
    title = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    file_size = models.PositiveBigIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='uploaded_disbursement_orders')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='updated_disbursement_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_removed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.CheckConstraint(
            condition=reduce(or_, [models.Q(**{field + '__isnull': field != selected for field in ORDER_RELATIONS}) for selected in ORDER_RELATIONS]), name='disbursement_order_one_agreement',
        )]
