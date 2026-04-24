<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目推进矩阵</p>
        <h2>{{ matrix?.project.name || "加载中..." }}</h2>
        <p class="compact-muted">{{ matrix?.project.description || "按项目查看所有券商的推进状态和关键进度项。" }}</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedProjectId" style="width: 240px;" placeholder="选择项目" @change="handleProjectChange">
          <el-option
            v-for="item in projectOptions"
            :key="item.projectTemplateId"
            :label="item.projectName"
            :value="item.projectTemplateId"
          />
        </el-select>
        <el-button type="primary" @click="router.push('/progress/overview')">返回总览</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4" v-if="matrix">
      <article class="compact-card">
        <small>覆盖券商</small>
        <strong>{{ matrix.summary.brokerCount }}</strong>
      </article>
      <article class="compact-card">
        <small>已完成 / 推进中</small>
        <strong>{{ matrix.summary.completedCount }}/{{ matrix.summary.inProgressCount }}</strong>
      </article>
      <article class="compact-card">
        <small>未开始</small>
        <strong>{{ matrix.summary.notStartedCount }}</strong>
      </article>
      <article class="compact-card">
        <small>平均进度 / 风险</small>
        <strong>{{ matrix.summary.avgProgress }}% / {{ matrix.summary.riskCount }}</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>推进矩阵</h3>
          <p>固定列看总体状态，动态列看项目特有的推进项。</p>
        </div>
      </div>

      <div v-if="matrix?.rows.length" class="table-scroll-shell">
        <el-table
          :data="matrix.rows"
          stripe
          style="width: 100%;"
          max-height="560"
          class="progress-table"
        >
        <el-table-column prop="brokerName" label="券商" min-width="110" fixed="left" sortable />
        <el-table-column prop="overallConclusion" label="总体结论" min-width="100" sortable />
        <el-table-column prop="progressPercent" label="总进度" min-width="90" sortable>
          <template #default="{ row }">{{ row.progressPercent }}%</template>
        </el-table-column>
        <el-table-column prop="status" label="当前状态" min-width="100" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <template v-for="group in groupedColumns" :key="group.key">
          <el-table-column
            v-if="group.children.length > 1"
            :label="group.label"
            align="center"
          >
            <el-table-column
              v-for="child in group.children"
              :key="child.key"
              :label="child.label"
              min-width="120"
              sortable
              :sort-method="(a, b) => compareDynamicValue(a, b, child.key)"
            >
              <template #default="{ row }">
                <ProgressValueDisplay :value="row.values[child.key]" :input-mode="row.inputMode" />
              </template>
            </el-table-column>
          </el-table-column>
          <el-table-column
            v-else
            :label="group.children[0].label"
            min-width="120"
            sortable
            :sort-method="(a, b) => compareDynamicValue(a, b, group.children[0].key)"
          >
            <template #default="{ row }">
              <ProgressValueDisplay :value="row.values[group.children[0].key]" :input-mode="row.inputMode" />
            </template>
          </el-table-column>
        </template>
        <el-table-column prop="latestUpdateAt" label="最近更新" min-width="110" sortable />
        <el-table-column prop="milestoneCount" label="里程碑" min-width="80" sortable />
        <el-table-column prop="riskCount" label="风险" min-width="70" sortable />
        <el-table-column label="操作" min-width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/progress/instances/${row.instanceId}`)">查看详情</el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>
      <EmptyBlock
        v-else
        title="当前项目还没有券商推进数据"
        description="初始化券商项目实例后，这里会展示完整的推进矩阵。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import EmptyBlock from "../../components/EmptyBlock.vue";
import ProgressValueDisplay from "../../components/ProgressValueDisplay.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getProgressMatrix, getProgressProjects } from "../../api/progress";
import type { ProgressDynamicColumn, ProgressMatrixResponse, ProgressProjectSummary } from "../../types/models";

const route = useRoute();
const router = useRouter();

const projectOptions = ref<ProgressProjectSummary[]>([]);
const selectedProjectId = ref<number | null>(null);
const matrix = ref<ProgressMatrixResponse | null>(null);

const groupedColumns = computed(() => {
  const result: Array<{ key: string; label: string; children: ProgressDynamicColumn[] }> = [];
  for (const column of matrix.value?.dynamicColumns || []) {
    const groupKey = column.groupKey || column.key;
    const groupLabel = column.groupLabel || column.label;
    let group = result.find((item) => item.key === groupKey);
    if (!group) {
      group = { key: groupKey, label: groupLabel, children: [] };
      result.push(group);
    }
    group.children.push(column);
  }
  return result;
});

function compareDynamicValue(a: ProgressMatrixResponse["rows"][number], b: ProgressMatrixResponse["rows"][number], key: string) {
  const valueA = a.values[key];
  const valueB = b.values[key];
  if (!valueA && !valueB) return 0;
  if (!valueA) return -1;
  if (!valueB) return 1;

  if (valueA.type === "status") {
    return (valueA.statusValue || "").localeCompare(valueB.statusValue || "");
  }

  if (valueA.type === "number_progress") {
    return (valueA.calculatedPercent || 0) - (valueB.calculatedPercent || 0);
  }

  return (valueA.remark || "").localeCompare(valueB.remark || "");
}

async function loadMatrix(projectId: number) {
  matrix.value = await getProgressMatrix(projectId);
}

async function handleProjectChange(projectId: number) {
  await router.replace(`/progress/matrix?projectId=${projectId}`);
}

onMounted(async () => {
  projectOptions.value = await getProgressProjects();
  const queryProjectId = Number(route.query.projectId || 0);
  selectedProjectId.value = queryProjectId || projectOptions.value[0]?.projectTemplateId || null;
  if (selectedProjectId.value) {
    await loadMatrix(selectedProjectId.value);
  }
});

watch(
  () => route.query.projectId,
  async (value) => {
    const projectId = Number(value || 0);
    if (!projectId) {
      return;
    }
    selectedProjectId.value = projectId;
    await loadMatrix(projectId);
  }
);
</script>

<style scoped>
.table-scroll-shell {
  width: 100%;
  overflow-x: auto;
}

:deep(.progress-table th.el-table__cell > .cell) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  word-break: keep-all;
  line-height: 1.2;
}

:deep(.progress-table .caret-wrapper) {
  flex: 0 0 auto;
}
</style>
