from django.db import models
from contract.helper import UploadToPath


class DoctoralContract(models.Model):
    type = models.CharField(max_length=64, default='doctoral-contracts')
    agreement_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, default='')
    subject = models.TextField(blank=True, default='')
    doctor_rank = models.CharField(max_length=150, blank=True, default='')
    duration = models.CharField(max_length=255, blank=True, default='')
    commencement_order = models.TextField(blank=True, default='')
    file = models.FileField(upload_to=UploadToPath('doctoral-contracts/files'), null=True, blank=True, max_length=512)
    file_name = models.CharField(max_length=512, blank=True, default='')
    is_hidden = models.BooleanField(default=False)
    # Optional dates keep circulation and dashboard queries compatible with contracts whose duration is text.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    reminder_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return f'{self.agreement_number} — {self.name}'
