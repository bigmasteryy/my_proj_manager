<template>
  <div v-if="value.isNa" class="compact-note">不适用</div>
  <div v-else-if="value.type === 'status'">
    <StatusTag :label="value.statusValue || '未开始'" />
  </div>
  <div v-else-if="value.type === 'number_progress'" class="progress-value-inline">
    <strong>{{ displayFraction }}</strong>
    <span v-if="showPercent" class="progress-value-percent">{{ value.calculatedPercent }}%</span>
  </div>
  <div v-else-if="value.type === 'boolean'">
    <StatusTag :label="value.boolValue ? '是' : '否'" />
  </div>
  <div v-else class="table-multiline">{{ value.remark || value.textValue || "-" }}</div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { ProgressCellValue } from "../types/models";
import StatusTag from "./StatusTag.vue";

const props = withDefaults(defineProps<{
  value: ProgressCellValue & { boolValue?: boolean | null; textValue?: string | null };
  inputMode?: string;
  showPercent?: boolean;
}>(), {
  inputMode: "明细",
  showPercent: true
});

const displayFraction = computed(() => {
  if (props.value.currentNum == null && props.value.targetNum == null) {
    return props.value.remark || "-";
  }
  return `${props.value.currentNum ?? 0}/${props.value.targetNum ?? 0}`;
});
</script>
