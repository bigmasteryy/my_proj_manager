<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">风险与阻塞</p>
        <h2>集中看高风险、阻塞和需要协调的事项。</h2>
        <p>按项目或券商过滤，快速定位哪家卡住、卡在什么环节。</p>
      </div>
    </section>

    <section class="section-card">
      <div class="filter-grid">
        <el-select v-model="filters.projectTemplateId" clearable placeholder="全部项目">
          <el-option v-for="item in projects" :key="item.projectTemplateId" :label="item.projectName" :value="item.projectTemplateId" />
        </el-select>
        <el-select v-model="filters.brokerId" clearable placeholder="全部券商">
          <el-option v-for="item in brokers" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option label="待处理" value="待处理" />
          <el-option label="处理中" value="处理中" />
          <el-option label="持续关注" value="持续关注" />
          <el-option label="已解除" value="已解除" />
        </el-select>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>风险列表</h3>
          <p>当前共 {{ risks.length }} 条风险。</p>
        </div>
        <el-button type="primary" @click="loadRisks">刷新</el-button>
      </div>
      <el-table v-if="risks.length" :data="risks" stripe max-height="560">
        <el-table-column prop="projectName" label="项目" min-width="140" sortable />
        <el-table-column prop="brokerName" label="券商" min-width="110" sortable />
        <el-table-column prop="title" label="风险标题" min-width="180" sortable />
        <el-table-column label="影响说明" min-width="220">
          <template #default="{ row }">
            <div class="table-multiline">{{ row.impactDesc || row.description || "-" }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="ownerName" label="责任人" min-width="90" sortable />
        <el-table-column prop="plannedResolveDate" label="计划解决" min-width="110" sortable />
        <el-table-column prop="status" label="状态" min-width="100" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前没有匹配的风险"
        description="如果项目存在阻塞、依赖或关键节点影响，这里会集中展示。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";

import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getProgressBrokers, getProgressProjects, getProgressRisks } from "../../api/progress";
import type { ProgressBrokerSimple, ProgressProjectSummary, ProgressRiskItem } from "../../types/models";

const projects = ref<ProgressProjectSummary[]>([]);
const brokers = ref<ProgressBrokerSimple[]>([]);
const risks = ref<ProgressRiskItem[]>([]);

const filters = reactive({
  projectTemplateId: undefined as number | undefined,
  brokerId: undefined as number | undefined,
  status: ""
});

async function loadRisks() {
  risks.value = await getProgressRisks({
    project_template_id: filters.projectTemplateId,
    broker_id: filters.brokerId,
    status: filters.status || undefined
  });
}

onMounted(async () => {
  [projects.value, brokers.value] = await Promise.all([getProgressProjects(), getProgressBrokers()]);
  await loadRisks();
});

watch(
  () => ({ ...filters }),
  async () => {
    await loadRisks();
  },
  { deep: true }
);
</script>
