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
  if (["无影响", "不适用"].includes(props.label)) {
    return "success";
  }

  if (props.label === "受影响") {
    return "warning";
  }

  if (["执行中", "进行中", "高风险", "启用", "已支持", "对接中"].includes(props.label)) {
    return "active";
  }

  if (["准备中", "临期", "中风险", "可开始", "就绪", "待上线", "待对接"].includes(props.label)) {
    return "warning";
  }

  if (["已逾期", "逾期", "待处理", "停用", "不支持", "阻塞", "待下线"].includes(props.label)) {
    return "danger";
  }

  if (["已完成", "已解除", "支持", "里程碑", "已上线"].includes(props.label)) {
    return "success";
  }

  return "active";
});
</script>
