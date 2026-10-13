<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import container  from '@/di/container';
import useAgreements from '@/presentation/composables/useAgreements';
import AgreementFilters from '@/presentation/components/AgreementFilters.vue';
import AgreementTable from '@/presentation/components/AgreementTable.vue';
import CostDetailsModal from '@/presentation/components/CostDetailsModal.vue';

const {
  filteredAgreements,
  activeFilters,
  loadAgreements,
  toggleFilter,
  clearFilters,
  statusLabel,
  typeLabel,
  STATUS_LABEL,
  TYPE_LABEL,
} = useAgreements();

/* ---------- Modal state ---------- */
const modalVisible = ref(false);
const selectedAgreement = ref(null);
const costDetails = ref([]);

const openCostModal = async (agreementNumber) => {
  selectedAgreement.value =
    filteredAgreements.value.find((a) => a.number === agreementNumber) || null;
  if (!selectedAgreement.value) return;

  costDetails.value = await container.getCostDetailsUseCase.execute();
  modalVisible.value = true;
  document.body.style.overflow = 'hidden';
};

const closeCostModal = () => {
  modalVisible.value = false;
  document.body.style.overflow = 'auto';
};

/* ---------- Formatters ---------- */
const formatDate = (date) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('ar-SA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const formatCost = (cost) => {
  if (cost === null || cost === undefined || cost === 0) return '';
  return new Intl.NumberFormat('ar-SA', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(cost);
};

/* ---------- Result count text ---------- */
const resultCountText = computed(() => {
  const count = filteredAgreements.value.length;
  const { status, type } = activeFilters.value;

  let filterText = '';
  if (status && type) filterText = ` (حالة: ${statusLabel(status)}، نوع: ${typeLabel(type)})`;
  else if (status)    filterText = ` (حالة: ${statusLabel(status)})`;
  else if (type)      filterText = ` (نوع: ${typeLabel(type)})`;

  return `عدد الاتفاقيات: ${count}${filterText}`;
});

/* ---------- Excel export ---------- */
const exportToExcel = async () => {
  if (filteredAgreements.value.length === 0) {
    alert('لا توجد بيانات لتصديرها.');
    return;
  }

  if (costDetails.value.length === 0) {
    costDetails.value = await container.getCostDetailsUseCase.execute();
  }

  const sheets = container.exportAgreementsUseCase.execute(
    filteredAgreements.value,
    costDetails.value,
    { statusArabic: STATUS_LABEL, typeArabic: TYPE_LABEL },
    () => new Date().toLocaleDateString('ar-SA')
  );

  const XLSX = window.XLSX;
  const workbook = XLSX.utils.book_new();

  for (const sheet of sheets) {
    const ws = XLSX.utils.json_to_sheet(sheet.rows);
    ws['!cols'] = sheet.cols;
    XLSX.utils.book_append_sheet(workbook, ws, sheet.name);
  }

  XLSX.writeFile(workbook, 'الاتفاقيات_مع_تفاصيل_التكلفة.xlsx');
};

/* ---------- Keyboard: ESC closes modal ---------- */
const onKeydown = (e) => {
  if (e.key === 'Escape' && modalVisible.value) closeCostModal();
};

onMounted(() => {
  loadAgreements();
  document.addEventListener('keydown', onKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown);
});
</script>

<template>
  <div class="container" dir="rtl">
    <h1>الاتفاقيات</h1>

    <AgreementFilters
      :active-filters="activeFilters"
      @toggle="toggleFilter"
      @clear="clearFilters"
    />

    <div class="result-count">{{ resultCountText }}</div>

    <AgreementTable
      :agreements="filteredAgreements"
      :status-label="statusLabel"
      :type-label="typeLabel"
      :format-date="formatDate"
      :format-cost="formatCost"
      @open-cost-modal="openCostModal"
    />

    <div class="actions">
      <button class="export-btn" @click="exportToExcel">
        <span>📊</span>
        تصدير إلى Excel
      </button>
    </div>

    <CostDetailsModal
      :visible="modalVisible"
      :agreement="selectedAgreement"
      :cost-details="costDetails"
      :format-cost="formatCost"
      @close="closeCostModal"
    />
  </div>
</template>