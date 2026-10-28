from django.db import models

from contract.helper import UploadToPath


class Agreement(models.Model):
    TYPE_CHOICES = [
        ("other-agreements", "Other Agreements"),
        ("memorandum", "Memorandum"),
    ]

    # ---- scalar fields -------------------------------------------------
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default="other-agreements",
    )
    agreement_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()
    reminder_date = models.DateField(null=True, blank=True)

    is_hidden = models.BooleanField(default=False)
    cost_table = models.JSONField(default=list, blank=True)
    payment_method = models.CharField(max_length=16, blank=True, default='')
    payment_text = models.TextField(blank=True, default='')

    # ---- file ----------------------------------------------------------
    file_name = models.CharField(max_length=255, blank=True, default="")
    file = models.FileField(
        upload_to=UploadToPath('other/files'),
        null=True,
        blank=True,
    )

    # ---- timestamps ----------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agreement_number} — {self.name}"


class AgreementRow(models.Model):
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="rows",
    )

    header = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")

    order = models.PositiveIntegerField(default=0)   # keep row order

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.header or f"Row #{self.pk}"
