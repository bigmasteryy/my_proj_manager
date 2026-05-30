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

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>涉及问题与需求</h3>
          <p>同步展示“问题与需求”中关联当前券商的受影响事项。</p>
        </div>
      </div>
      <el-table v-if="brokerIssues.length" :data="brokerIssues" stripe>
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="issueType" label="类型" min-width="90" sortable />
        <el-table-column prop="priority" label="优先级" min-width="90" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.priority" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="事项状态" min-width="110" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="fixStatus" label="修复状态" min-width="110" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.fixStatus" />
          </template>
        </el-table-column>
        <el-table-column prop="plannedFixVersion" label="计划版本" min-width="110">
          <template #default="{ row }">{{ row.plannedFixVersion || "-" }}</template>
        </el-table-column>
        <el-table-column prop="plannedFinishDate" label="计划完成" min-width="110" sortable>
          <template #default="{ row }">{{ row.plannedFinishDate || "-" }}</template>
        </el-table-column>
        <el-table-column prop="ownerName" label="跟进人" min-width="100">
          <template #default="{ row }">{{ row.ownerName || "-" }}</template>
        </el-table-column>
        <el-table-column prop="impactDesc" label="影响说明" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.impactDesc || "-" }}</template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="最近更新" min-width="110" sortable>
          <template #default="{ row }">{{ row.updatedAt || "-" }}</template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前券商没有关联的问题与需求"
        description="在“问题与需求”中把事项关联到该券商后，这里会自动展示。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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
const brokerIssues = computed(() => brokerView.value?.issues || []);

function normalizeBrokerView(view: ProgressBrokerView): ProgressBrokerView {
  return {
    ...view,
    issues: view.issues || []
  };
}

async function loadBrokerView(brokerId: number) {
  brokerView.value = normalizeBrokerView(await getBrokerProgressProjects(brokerId));
}

async function handleBrokerChange(brokerId: number) {
  await router.replace(`/progress/brokers?brokerId=${brokerId}`);
}

async function selectDefaultBroker() {
  for (const broker of brokers.value) {
    const view = normalizeBrokerView(await getBrokerProgressProjects(broker.id));
    if (view.projects.length || view.issues.length) {
      selectedBrokerId.value = broker.id;
      brokerView.value = view;
      await router.replace(`/progress/brokers?brokerId=${broker.id}`);
      return;
    }
  }

  const firstBrokerId = brokers.value[0]?.id || 0;
  if (firstBrokerId) {
    selectedBrokerId.value = firstBrokerId;
    await loadBrokerView(firstBrokerId);
  }
}

onMounted(async () => {
  brokers.value = await getProgressBrokers();
  const brokerId = Number(route.query.brokerId || 0);
  if (brokerId) {
    selectedBrokerId.value = brokerId;
    await loadBrokerView(brokerId);
  } else {
    await selectDefaultBroker();
  }
});

watch(
  () => route.query.brokerId,
  async (value) => {
    const brokerId = Number(value || 0);
    if (!brokerId) {
      return;
    }
    if (brokerId === brokerView.value?.brokerId) {
      return;
    }
    selectedBrokerId.value = brokerId;
    await loadBrokerView(brokerId);
  }
);
</script>
