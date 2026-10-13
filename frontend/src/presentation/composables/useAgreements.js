import { ref, computed } from 'vue';
import container from '@/di/container';

const STATUS_LABEL = { finish: 'منتهية', current: 'حالية', future: 'مستقبلية' };
const TYPE_LABEL   = { current: 'جاري',   investment: 'استثماري' };

export default function useAgreements() {
  const agreements    = ref([]);
  const loading       = ref(false);
  const activeFilters = ref({ status: null, type: null });

  const loadAgreements = async () => {
    loading.value = true;
    try {
      agreements.value = await container.getAgreementsUseCase.execute();
    } finally {
      loading.value = false;
    }
  };

  const filteredAgreements = computed(() =>
    container.filterAgreementsUseCase.execute(agreements.value, activeFilters.value)
  );

  const toggleFilter = (category, value) => {
    activeFilters.value = {
      ...activeFilters.value,
      [category]: activeFilters.value[category] === value ? null : value,
    };
  };

  const clearFilters = () => { activeFilters.value = { status: null, type: null }; };

  const statusLabel = (s) => STATUS_LABEL[s] ?? s;
  const typeLabel   = (t) => TYPE_LABEL[t]   ?? t;

  return {
    agreements, filteredAgreements, loading, activeFilters,
    loadAgreements, toggleFilter, clearFilters, statusLabel, typeLabel,
    STATUS_LABEL, TYPE_LABEL,
  };
}