<template>
  <div class="page-shell">
    <section class="section-card compact-toolbar matrix-toolbar-card">
      <div>
        <p class="eyebrow">项目推进矩阵</p>
        <h3 style="margin: 0;">{{ matrix?.project.name || "项目推进矩阵" }}</h3>
      </div>
      <div class="hero-actions compact">
        <el-button size="small" type="primary" @click="openProjectDialog">新增项目</el-button>
        <el-button size="small" :disabled="!selectedProjectId || matrixLoading" @click="openBrokerDialog">添加券商</el-button>
        <el-select
          v-model="selectedProjectId"
          style="width: 260px;"
          placeholder="选择项目"
          :disabled="matrixLoading"
          @change="handleProjectChange"
        >
          <el-option
            v-for="item in projectOptions"
            :key="item.projectTemplateId"
            :label="buildProjectOptionLabel(item)"
            :value="item.projectTemplateId"
          />
        </el-select>
        <el-button size="small" type="primary" @click="router.push('/progress/overview')">返回总览</el-button>
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

    <section class="section-card" v-loading="matrixLoading">
      <div class="section-title">
        <div>
          <h3>推进矩阵</h3>
          <p>主页面专注横向对比项目和券商，结构化进度项的增删改查放到详情页里维护。</p>
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
          <el-table-column prop="brokerName" fixed="left" min-width="120" sortable>
            <template #header>
              <span class="matrix-header">券商</span>
            </template>
          </el-table-column>

          <template v-for="column in orderedColumns" :key="column.key">
            <el-table-column
              v-if="column.kind === 'group'"
              :label="column.label"
              align="center"
            >
              <template #header>
                <div
                  class="matrix-header draggable"
                  draggable="true"
                  @dragstart="handleDragStart(column.key)"
                  @dragover.prevent
                  @drop="handleDrop(column.key)"
                >
                  {{ column.label }}
                </div>
              </template>
              <el-table-column
                v-for="child in column.children"
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
              v-else-if="column.kind === 'dynamic'"
              :min-width="column.minWidth"
              sortable
              :sort-method="(a, b) => compareDynamicValue(a, b, column.key)"
            >
              <template #header>
                <div
                  class="matrix-header draggable"
                  draggable="true"
                  @dragstart="handleDragStart(column.key)"
                  @dragover.prevent
                  @drop="handleDrop(column.key)"
                >
                  {{ column.label }}
                </div>
              </template>
              <template #default="{ row }">
                <ProgressValueDisplay :value="row.values[column.key]" :input-mode="row.inputMode" />
              </template>
            </el-table-column>

            <el-table-column
              v-else-if="column.kind === 'stage2'"
              min-width="160"
              sortable
              :sort-method="compareStage2Summary"
            >
              <template #header>
                <div
                  class="matrix-header draggable"
                  draggable="true"
                  @dragstart="handleDragStart(column.key)"
                  @dragover.prevent
                  @drop="handleDrop(column.key)"
                >
                  {{ column.label }}
                </div>
              </template>
              <template #default="{ row }">
                <el-tooltip placement="top" :content="buildStage2Tooltip(row)">
                  <div class="stage2-summary">
                    <StatusTag :label="row.stage2?.status || '未开始'" />
                    <span class="compact-note">{{ row.stage2 ? `${row.stage2.completedCount}/${row.stage2.totalCount}` : "0/0" }}</span>
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>

            <el-table-column
              v-else
              :prop="column.key"
              :min-width="column.minWidth"
              sortable
              :sort-method="column.sortMethod"
            >
              <template #header>
                <div
                  class="matrix-header draggable"
                  draggable="true"
                  @dragstart="handleDragStart(column.key)"
                  @dragover.prevent
                  @drop="handleDrop(column.key)"
                >
                  {{ column.label }}
                </div>
              </template>
              <template #default="{ row }">
                <template v-if="column.key === 'progressPercent'">{{ row.progressPercent }}%</template>
                <template v-else-if="column.key === 'status'">
                  <StatusTag :label="row.status" />
                </template>
                <template v-else>{{ row[column.key] }}</template>
              </template>
            </el-table-column>
          </template>

          <el-table-column fixed="right" min-width="110">
            <template #header>
              <span class="matrix-header">操作</span>
            </template>
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push(`/progress/instances/${row.instanceId}`)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <EmptyBlock
        v-else-if="!matrixLoading"
        :title="emptyStateTitle"
        :description="emptyStateDescription"
      >
        <el-button type="primary" @click="openProjectDialog">新增项目</el-button>
      </EmptyBlock>
    </section>

    <el-dialog v-model="projectDialogVisible" title="新增项目" width="620px">
      <el-form :model="projectForm" label-width="110px">
        <el-form-item label="项目名称" required>
          <el-input v-model="projectForm.name" placeholder="例如：交易链路优化" />
        </el-form-item>
        <el-form-item label="项目编码">
          <el-input v-model="projectForm.code" placeholder="可不填，系统会自动生成" />
        </el-form-item>
        <el-form-item label="项目类型">
          <el-input v-model="projectForm.project_type" />
        </el-form-item>
        <el-form-item label="项目说明">
          <el-input v-model="projectForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="projectSubmitting" @click="handleCreateProject">创建项目</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="brokerDialogVisible" title="给当前项目添加券商" width="680px">
      <el-form :model="brokerForm" label-width="110px">
        <el-form-item label="选择券商" required>
          <el-select v-model="brokerForm.broker_ids" multiple filterable style="width: 100%;" placeholder="选择一个或多个券商">
            <el-option
              v-for="broker in availableBrokers"
              :key="broker.id"
              :label="broker.name"
              :value="broker.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="录入模式">
          <el-select v-model="brokerForm.input_mode" style="width: 100%;">
            <el-option label="明细" value="明细" />
            <el-option label="简化" value="简化" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="brokerForm.owner_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="brokerForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brokerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="brokerSubmitting" @click="handleAddBrokers">添加券商</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import EmptyBlock from "../../components/EmptyBlock.vue";
import ProgressValueDisplay from "../../components/ProgressValueDisplay.vue";
import StatusTag from "../../components/StatusTag.vue";
import { addProgressProjectBrokers, createProgressProject, getProgressBrokers, getProgressMatrix, getProgressProjects } from "../../api/progress";
import type {
  ProgressBrokerSimple,
  ProgressDynamicColumn,
  ProgressMatrixResponse,
  ProgressProjectBrokerAddPayload,
  ProgressProjectCreatePayload,
  ProgressProjectSummary
} from "../../types/models";

type OrderedColumnDef =
  | {
      key: string;
      label: string;
      kind: "standard";
      minWidth: number;
      sortMethod?: (a: ProgressMatrixResponse["rows"][number], b: ProgressMatrixResponse["rows"][number]) => number;
    }
  | {
      key: string;
      label: string;
      kind: "dynamic";
      minWidth: number;
    }
  | {
      key: string;
      label: string;
      kind: "group";
      children: ProgressDynamicColumn[];
    }
  | {
      key: string;
      label: string;
      kind: "stage2";
    };

const route = useRoute();
const router = useRouter();

const projectOptions = ref<ProgressProjectSummary[]>([]);
const allBrokers = ref<ProgressBrokerSimple[]>([]);
const selectedProjectId = ref<number | null>(null);
const matrix = ref<ProgressMatrixResponse | null>(null);
const matrixLoading = ref(false);
const columnOrder = ref<string[]>([]);
const draggingColumnKey = ref("");

const projectDialogVisible = ref(false);
const brokerDialogVisible = ref(false);
const projectSubmitting = ref(false);
const brokerSubmitting = ref(false);

const projectForm = reactive<ProgressProjectCreatePayload>({
  code: "",
  name: "",
  project_type: "批量推进",
  description: "",
  status: "active",
  sort_no: null
});

const brokerForm = reactive<ProgressProjectBrokerAddPayload>({
  broker_ids: [],
  input_mode: "明细",
  owner_name: "",
  remark: ""
});

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

const firstProjectWithData = computed(() => projectOptions.value.find((item) => item.brokerCount > 0) || null);
const emptyStateTitle = computed(() => {
  if (!selectedProjectId.value) {
    return "当前还没有推进矩阵数据";
  }
  const selected = projectOptions.value.find((item) => item.projectTemplateId === selectedProjectId.value);
  if (selected && selected.brokerCount === 0) {
    return `“${selected.projectName}” 还是一个空项目`;
  }
  return "当前还没有推进矩阵数据";
});
const emptyStateDescription = computed(() => {
  if (!selectedProjectId.value) {
    return "可以先新增项目，再给项目添加券商。结构化进度项请在详情页里维护。";
  }
  const selected = projectOptions.value.find((item) => item.projectTemplateId === selectedProjectId.value);
  if (selected && selected.brokerCount === 0) {
    return "这个项目模板刚建好，还没加券商。先把券商加进来，再从详情里维护结构化进度项。";
  }
  return "可以先新增项目，再给项目添加券商。结构化进度项请在详情页里维护。";
});

const availableColumns = computed<OrderedColumnDef[]>(() => {
  const baseColumns: OrderedColumnDef[] = [
    { key: "overallConclusion", label: "总体结论", kind: "standard", minWidth: 110 },
    { key: "progressPercent", label: "总进度", kind: "standard", minWidth: 90 },
    { key: "status", label: "当前状态", kind: "standard", minWidth: 100 }
  ];

  const dynamicDefs: OrderedColumnDef[] = groupedColumns.value.map((group) => {
    if (group.children.length > 1) {
      return { key: group.key, label: group.label, kind: "group", children: group.children };
    }
    return { key: group.children[0].key, label: group.children[0].label, kind: "dynamic", minWidth: 120 };
  });

  const stage2Column: OrderedColumnDef[] = matrix.value?.project.code === "local_route_upgrade"
    ? [{ key: "stage2Summary", label: "客户端放开", kind: "stage2" }]
    : [];

  const trailingColumns: OrderedColumnDef[] = [
    { key: "latestUpdateAt", label: "最新更新", kind: "standard", minWidth: 120 },
    { key: "milestoneCount", label: "里程碑", kind: "standard", minWidth: 80 },
    { key: "riskCount", label: "风险", kind: "standard", minWidth: 70 }
  ];

  return [...baseColumns, ...dynamicDefs, ...stage2Column, ...trailingColumns];
});

const orderedColumns = computed(() => {
  const defs = availableColumns.value;
  const map = new Map(defs.map((item) => [item.key, item]));
  const ordered = columnOrder.value.map((key) => map.get(key)).filter(Boolean) as OrderedColumnDef[];
  const missing = defs.filter((item) => !columnOrder.value.includes(item.key));
  return [...ordered, ...missing];
});

const existingBrokerIds = computed(() => new Set((matrix.value?.rows || []).map((row) => row.brokerId)));
const availableBrokers = computed(() => allBrokers.value.filter((item) => !existingBrokerIds.value.has(item.id)));

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

function compareStage2Summary(a: ProgressMatrixResponse["rows"][number], b: ProgressMatrixResponse["rows"][number]) {
  const progressDiff = (a.stage2?.progressPercent || 0) - (b.stage2?.progressPercent || 0);
  if (progressDiff !== 0) {
    return progressDiff;
  }
  return (a.stage2?.status || "").localeCompare(b.stage2?.status || "");
}

function buildStage2Tooltip(row: ProgressMatrixResponse["rows"][number]) {
  const stage2 = row.stage2;
  if (!stage2) {
    return "当前步骤：- | 当前负责人：- | 阻塞步骤：0";
  }
  const step = stage2.currentStepNo ? `当前步骤：${stage2.currentStepNo} ${stage2.currentStepName}` : "当前步骤：-";
  const owner = `当前负责人：${stage2.currentStepOwner || "-"}`;
  const blocked = `阻塞步骤：${stage2.blockedCount}`;
  return [step, owner, blocked].join(" | ");
}

function getStorageKey(projectCode: string) {
  return `progress-matrix-columns-${projectCode}`;
}

function initializeColumnOrder() {
  if (!matrix.value) {
    columnOrder.value = [];
    return;
  }
  const currentKeys = availableColumns.value.map((item) => item.key);
  const stored = window.localStorage.getItem(getStorageKey(matrix.value.project.code));
  if (stored) {
    try {
      const parsed = JSON.parse(stored) as string[];
      columnOrder.value = parsed.filter((key) => currentKeys.includes(key));
    } catch {
      columnOrder.value = [];
    }
  }
  if (!columnOrder.value.length) {
    columnOrder.value = currentKeys;
  }
}

function persistColumnOrder() {
  if (!matrix.value) {
    return;
  }
  window.localStorage.setItem(getStorageKey(matrix.value.project.code), JSON.stringify(columnOrder.value));
}

function handleDragStart(columnKey: string) {
  draggingColumnKey.value = columnKey;
}

function handleDrop(targetKey: string) {
  const sourceKey = draggingColumnKey.value;
  if (!sourceKey || sourceKey === targetKey) {
    draggingColumnKey.value = "";
    return;
  }
  const next = [...columnOrder.value];
  const from = next.indexOf(sourceKey);
  const to = next.indexOf(targetKey);
  if (from < 0 || to < 0) {
    draggingColumnKey.value = "";
    return;
  }
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  columnOrder.value = next;
  persistColumnOrder();
  draggingColumnKey.value = "";
}

async function loadProjectOptions() {
  projectOptions.value = await getProgressProjects();
}

async function loadBrokerOptions() {
  allBrokers.value = await getProgressBrokers();
}

async function loadMatrix(projectId: number) {
  matrixLoading.value = true;
  try {
    matrix.value = await getProgressMatrix(projectId);
    initializeColumnOrder();
  } finally {
    matrixLoading.value = false;
  }
}

async function handleProjectChange(projectId: number) {
  await router.replace(`/progress/matrix?projectId=${projectId}`);
}

function buildProjectOptionLabel(item: ProgressProjectSummary) {
  return item.brokerCount > 0 ? `${item.projectName}（${item.brokerCount}家）` : `${item.projectName}（未配置）`;
}

function openProjectDialog() {
  projectForm.code = "";
  projectForm.name = "";
  projectForm.project_type = "批量推进";
  projectForm.description = "";
  projectForm.status = "active";
  projectForm.sort_no = projectOptions.value.length + 1;
  projectDialogVisible.value = true;
}

function openBrokerDialog() {
  if (!selectedProjectId.value) {
    return;
  }
  brokerForm.broker_ids = [];
  brokerForm.input_mode = "明细";
  brokerForm.owner_name = "";
  brokerForm.remark = "";
  if (!availableBrokers.value.length) {
    ElMessage.warning("当前项目下已包含全部券商");
    return;
  }
  brokerDialogVisible.value = true;
}

async function handleCreateProject() {
  if (!projectForm.name.trim()) {
    ElMessage.warning("请先填写项目名称");
    return;
  }
  projectSubmitting.value = true;
  try {
    const result = await createProgressProject({
      code: projectForm.code?.trim() || undefined,
      name: projectForm.name.trim(),
      project_type: projectForm.project_type.trim() || "批量推进",
      description: projectForm.description?.trim() || undefined,
      status: projectForm.status,
      sort_no: projectForm.sort_no
    });
    projectDialogVisible.value = false;
    await loadProjectOptions();
    ElMessage.success("项目已创建，现在可以继续添加券商");
    await router.replace(`/progress/matrix?projectId=${result.projectTemplateId}`);
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "新增项目失败");
  } finally {
    projectSubmitting.value = false;
  }
}

async function handleAddBrokers() {
  if (!selectedProjectId.value) {
    return;
  }
  if (!brokerForm.broker_ids.length) {
    ElMessage.warning("请至少选择一个券商");
    return;
  }
  brokerSubmitting.value = true;
  try {
    const result = await addProgressProjectBrokers(selectedProjectId.value, {
      broker_ids: brokerForm.broker_ids,
      input_mode: brokerForm.input_mode,
      owner_name: brokerForm.owner_name?.trim() || undefined,
      remark: brokerForm.remark?.trim() || undefined
    });
    brokerDialogVisible.value = false;
    await Promise.all([loadProjectOptions(), loadMatrix(selectedProjectId.value)]);
    ElMessage.success(`已添加 ${result.addedCount} 家券商`);
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "添加券商失败");
  } finally {
    brokerSubmitting.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadProjectOptions(), loadBrokerOptions()]);
  const queryProjectId = Number(route.query.projectId || 0);
  const fallbackProjectId = firstProjectWithData.value?.projectTemplateId || projectOptions.value[0]?.projectTemplateId || null;
  const nextProjectId = queryProjectId || fallbackProjectId;
  selectedProjectId.value = nextProjectId;
  if (nextProjectId) {
    if (queryProjectId !== nextProjectId) {
      await router.replace(`/progress/matrix?projectId=${nextProjectId}`);
    } else {
      await loadMatrix(nextProjectId);
    }
  }
});

watch(
  () => route.query.projectId,
  async (value) => {
    const projectId = Number(value || 0);
    selectedProjectId.value = projectId || null;
    if (projectId) {
      await loadMatrix(projectId);
    } else {
      matrix.value = null;
      columnOrder.value = [];
    }
  }
);
</script>

<style scoped>
.matrix-toolbar-card {
  padding: 10px 16px;
}

.table-scroll-shell {
  width: 100%;
  overflow-x: auto;
}

.stage2-summary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.matrix-header {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.matrix-header.draggable {
  cursor: grab;
  user-select: none;
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
