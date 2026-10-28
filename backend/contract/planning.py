from datetime import datetime
from zoneinfo import ZoneInfo

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.educational_content.models import EducationalContent
from contract.educational_content.serializers import EducationalContentSerializer
from contract.life_long.models import LifeLongAgreement
from contract.life_long.serializers import LifeLongAgreementSerializer
from contract.nafath_center.models import NafathCenterAgreement
from contract.nafath_center.serializers import NafathCenterAgreementSerializer
from contract.other.models import Agreement
from contract.other.serializers import AgreementSerializer
from contract.rbac import HasFeaturePermission
from contract.doctoral_models import DoctoralContract
from contract.doctoral import DoctoralContractSerializer
from contract.order_counts import with_order_counts


def planning_today():
    return datetime.now(ZoneInfo('Asia/Damascus')).date()


def agreement_phase(start, end, today):
    if not start or not end or start > end:
        return 'unknown'
    if start < today and end < today:
        return 'finish'
    if start > today and end > today:
        return 'future'
    # Agreements starting or ending today remain current for the entire day.
    return 'current'


class PlanningAgreementListView(APIView):
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'planning'

    def get(self, request):
        phase_filter = request.query_params.get('phase', '')
        if phase_filter not in {'', 'finish', 'current', 'future', 'unknown'}:
            raise ValidationError({'phase': ['الحالة غير صالحة']})

        sources = [
            ('doctoral-contracts', 'عقود الدكتوراه', DoctoralContract, DoctoralContractSerializer, {}, None),
            ('nafath-centers', 'اتفاقيات مراكز النفاذ', NafathCenterAgreement, NafathCenterAgreementSerializer, {}, 'payment_schedule'),
            ('memorandum', 'مذكرات التفاهم', Agreement, AgreementSerializer, {'type': 'memorandum'}, 'rows'),
            ('lifelong-learning', 'اتفاقيات التعلم مدى الحياة', LifeLongAgreement, LifeLongAgreementSerializer, {}, 'payment_schedule'),
            ('other-agreements', 'اتفاقيات أخرى', Agreement, AgreementSerializer, {'type': 'other-agreements'}, 'rows'),
            ('educational-content', 'اتفاقيات المحتوى التعليمي', EducationalContent, EducationalContentSerializer, {}, 'payment_schedule'),
        ]
        today = planning_today()
        data = []
        for feature, category, model, serializer_class, filters, relation in sources:
            # Enforce Planning visibility before serialization, for every role.
            records = with_order_counts(model.objects.filter(is_hidden=False, **filters), request).prefetch_related(relation)
            for record in records:
                phase = agreement_phase(record.start_date, record.end_date, today)
                if phase_filter and phase != phase_filter:
                    continue
                item = dict(serializer_class(record, context={'request': request}).data)
                item.update(feature=feature, category=category,
                            key=f'{feature}-{record.pk}', planningPhase=phase)
                data.append(item)

        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))
