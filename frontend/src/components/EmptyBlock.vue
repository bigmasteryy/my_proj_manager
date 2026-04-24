<template>
  <div class="empty-block" :class="{ compact }">
    <el-empty :description="description" />
    <div class="empty-copy">
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="empty-actions">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
  compact?: boolean;
}>();
</script>

<style scoped>
.empty-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 12px 10px;
}

.empty-block.compact {
  padding-top: 8px;
}

.empty-copy {
  text-align: center;
}

.empty-copy strong {
  display: block;
  font-size: 15px;
}

.empty-copy p {
  margin: 6px 0 0;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.6;
}

.empty-actions {
  margin-top: 6px;
}
</style>
