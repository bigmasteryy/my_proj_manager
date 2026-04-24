<template>
  <span class="status-tag" :class="variantClass">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  label: string;
}>();

const variantClass = computed(() => {
  if (["执行中", "进行中", "高风险", "启用"].includes(props.label)) {
    return "active";
  }

  if (["准备中", "临期", "中风险"].includes(props.label)) {
    return "warning";
  }

  if (["已逾期", "逾期", "待处理", "停用"].includes(props.label)) {
    return "danger";
  }

  if (["已完成", "已解除"].includes(props.label)) {
    return "success";
  }

  return "active";
});
</script>
