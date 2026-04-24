<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">券商推进视图</p>
        <h2>{{ brokerView?.brokerName || "选择券商查看整体推进情况" }}</h2>
        <p>按券商查看三大重点项目的整体推进状态，适合开会或横向比较。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedBrokerId" style="width: 240px;" placeholder="选择券商" @change="handleBrokerChange">
          <el-option v-for="item in brokers" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>券商项目推进</h3>
          <p>看某家券商在多个重点项目上的推进情况。</p>
        </div>
      </div>
      <el-table v-if="brokerView?.projects.length" :data="brokerView.projects" stripe :fit="false">
        <el-table-column prop="projectName" label="项目" min-width="160" sortable />
        <el-table-column prop="progressPercent" label="总进度" min-width="90" sortable>
          <template #default="{ row }">{{ row.progressPercent }}%</template>
        </el-table-column>
        <el-table-column prop="status" label="当前状态" min-width="100" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="latestUpdateAt" label="最近更新" min-width="110" sortable />
        <el-table-column prop="riskCount" label="风险" min-width="70" sortable />
        <el-table-column prop="milestoneCount" label="里程碑" min-width="80" sortable />
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/progress/instances/${row.instanceId}`)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前券商还没有推进项目"
        description="选择一个券商后，这里会展示它在各重点项目上的推进情况。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getBrokerProgressProjects, getProgressBrokers } from "../../api/progress";
import type { ProgressBrokerSimple, ProgressBrokerView } from "../../types/models";

const route = useRoute();
const router = useRouter();

const brokers = ref<ProgressBrokerSimple[]>([]);
const selectedBrokerId = ref<number | null>(null);
const brokerView = ref<ProgressBrokerView | null>(null);

async function loadBrokerView(brokerId: number) {
  brokerView.value = await getBrokerProgressProjects(brokerId);
}

async function handleBrokerChange(brokerId: number) {
  await router.replace(`/progress/brokers?brokerId=${brokerId}`);
}

onMounted(async () => {
  brokers.value = await getProgressBrokers();
  const brokerId = Number(route.query.brokerId || 0) || brokers.value[0]?.id || 0;
  if (brokerId) {
    selectedBrokerId.value = brokerId;
    await loadBrokerView(brokerId);
  }
});

watch(
  () => route.query.brokerId,
  async (value) => {
    const brokerId = Number(value || 0);
    if (!brokerId) {
      return;
    }
    selectedBrokerId.value = brokerId;
    await loadBrokerView(brokerId);
  }
);
</script>
