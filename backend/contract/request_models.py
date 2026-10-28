from django.db import models


class ContractRequest(models.Model):
    justification_memo = models.TextField()
    technical_specs = models.CharField(max_length=2000)
    legal_specs = models.CharField(max_length=2000)
    announce_start = models.DateField(null=True, blank=True)
    announce_end = models.DateField(null=True, blank=True)
    reminder_date = models.DateField()
    status = models.CharField(max_length=16, choices=[('success', 'تمت المناقصة بنجاح'), ('failed', 'فشلت المناقصة')])
    wishes = models.JSONField(default=list, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class BidMinute(models.Model):
    contract_request = models.ForeignKey(ContractRequest, on_delete=models.CASCADE, related_name='bids')
    number = models.CharField(max_length=150)
    date = models.DateField()
    subject = models.CharField(max_length=2000)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']
