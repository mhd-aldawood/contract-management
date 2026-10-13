import json

from rest_framework import serializers
from .models import Agreement, AgreementRow


class AgreementRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgreementRow
        fields = ["header", "body"]


class AgreementSerializer(serializers.ModelSerializer):
    agreementNumber = serializers.CharField(source="agreement_number")
    startDate       = serializers.DateField(source="start_date")
    endDate         = serializers.DateField(source="end_date")
    isHidden        = serializers.BooleanField(source="is_hidden", required=False)
    fileName        = serializers.CharField(source="file_name", required=False, allow_blank=True)

    rows = AgreementRowSerializer(many=True, required=False)
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Agreement
        fields = [
            "id", "type",
            "agreementNumber", "name",
            "startDate", "endDate", "isHidden",
            "rows", "fileName", "file",
        ]

    # ---------- FIX #1: parse `rows` from the multipart string ----------
    def to_internal_value(self, data):
        # Normalize QueryDict → plain dict so assignment works correctly
        if hasattr(data, "getlist"):
            data = data.dict()          # last value per key, plain dict
        else:
            data = dict(data)

        raw = data.get("rows")
        if isinstance(raw, str):
            try:
                data["rows"] = json.loads(raw or "[]")
            except json.JSONDecodeError:
                raise serializers.ValidationError({"rows": "Invalid JSON."})

        return super().to_internal_value(data)

    def create(self, validated_data):
        rows_data = validated_data.pop("rows", [])
        agreement = Agreement.objects.create(**validated_data)
        self._save_rows(agreement, rows_data)
        return agreement

    def update(self, instance, validated_data):
        rows_data = validated_data.pop("rows", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if rows_data is not None:
            instance.rows.all().delete()
            self._save_rows(instance, rows_data)
        return instance

    # ---------- FIX #2: pick fields explicitly, ignore front-end `id` ----------
    def _save_rows(self, agreement, rows_data):
        if not rows_data:
            return
        AgreementRow.objects.bulk_create([
            AgreementRow(
                agreement=agreement,
                order=i,
                header=r.get("header", ""),
                body=r.get("body", ""),
                # "id" from the front-end is intentionally ignored
            )
            for i, r in enumerate(rows_data)
        ])