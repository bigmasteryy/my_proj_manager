<template>
  <div class="page-shell broker-issues-page">
    <section class="compact-toolbar issue-topbar">
      <div>
        <p class="eyebrow">问题与需求</p>
        <h2>统一跟踪线上问题、新需求，以及各券商修复进展。</h2>
      </div>
      <div class="hero-actions compact">
        <el-button @click="downloadIssueCsv">导出 CSV</el-button>
        <el-button type="primary" @click="openCreateDialog">新增事项</el-button>
      </div>
    </section>

    <section class="compact-grid issue-stat-grid">
      <article class="compact-card">
        <small>未解决</small>
        <strong>{{ issueStats.open }}</strong>
      </article>
      <article class="compact-card">
        <small>高优先级</small>
        <strong>{{ issueStats.high }}</strong>
      </article>
      <article class="compact-card">
        <small>本周计划修复</small>
        <strong>{{ issueStats.thisWeek }}</strong>
      </article>
      <article class="compact-card">
        <small>涉及券商</small>
        <strong>{{ issueStats.affectedBrokers }}</strong>
      </article>
    </section>

    <section class="section-card issue-filter-card">
      <el-form :model="filters" class="issue-filter-row">
        <el-input v-model="filters.keyword" clearable placeholder="搜索标题 / 描述 / 方案" @keyup.enter="loadIssues" />
        <el-select v-model="filters.issue_type" clearable placeholder="全部类型">
          <el-option v-for="item in issueTypes" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态">
          <el-option v-for="item in issueStatuses" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.broker_id" clearable filterable placeholder="全部券商">
          <el-option v-for="item in brokers" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-button type="primary" @click="loadIssues">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form>
    </section>

    <section class="section-card" v-loading="loading">
      <div class="section-title">
        <div>
          <h3>事项总表</h3>
          <p>当前共 {{ issues.length }} 条事项，点击详情查看受影响券商修复情况。</p>
        </div>
      </div>

      <el-table v-if="issues.length" :data="issues" stripe>
        <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="issueType" label="类型" min-width="100" sortable />
        <el-table-column prop="priority" label="优先级" min-width="90" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.priority" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="110" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="plannedFixVersion" label="计划修复版本" min-width="130">
          <template #default="{ row }">{{ row.plannedFixVersion || "-" }}</template>
        </el-table-column>
        <el-table-column label="修复进度" min-width="110" sortable :sort-method="sortByFixProgress">
          <template #default="{ row }">
            <span class="progress-text">{{ row.fixedBrokerCount }}/{{ row.affectedBrokerCount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="impactScope" label="影响范围" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.impactScope || "-" }}</template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="最近更新" min-width="140" sortable>
          <template #default="{ row }">{{ row.updatedAt || "-" }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyBlock
        v-else
        title="当前没有问题与需求"
        description="新增一条事项后，这里会展示整体状态、修复进度和影响范围。"
      />
    </section>

    <el-drawer v-model="detailDrawerVisible" size="58%" :with-header="false" append-to-body>
      <div v-if="selectedIssue" class="issue-drawer" v-loading="detailLoading">
        <div class="drawer-head">
          <div>
            <p class="eyebrow">{{ selectedIssue.issueType }}</p>
            <h2>{{ selectedIssue.title }}</h2>
            <div class="drawer-tags">
              <StatusTag :label="selectedIssue.priority" />
              <StatusTag :label="selectedIssue.status" />
              <span>计划版本：{{ selectedIssue.plannedFixVersion || "-" }}</span>
            </div>
          </div>
          <div class="action-row">
            <el-button @click="openEditDialog">编辑事项</el-button>
            <el-button type="danger" plain @click="handleDeleteIssue">删除</el-button>
          </div>
        </div>

        <section class="drawer-section">
          <h3>基本信息</h3>
          <div class="issue-info-grid">
            <article>
              <small>描述信息</small>
              <p>{{ selectedIssue.description || "-" }}</p>
            </article>
            <article>
              <small>影响范围</small>
              <p>{{ selectedIssue.impactScope || "-" }}</p>
            </article>
            <article>
              <small>解决方案</small>
              <p>{{ selectedIssue.solution || "-" }}</p>
            </article>
            <article>
              <small>负责人 / 计划完成</small>
              <p>{{ selectedIssue.ownerName || "-" }} / {{ selectedIssue.plannedFinishDate || "-" }}</p>
            </article>
          </div>
        </section>

        <section class="drawer-section">
          <div class="section-title section-title-tight">
            <div>
              <h3>受影响券商</h3>
              <p>每家券商可单独维护修复状态、修复版本和验证结果。</p>
            </div>
          </div>
          <el-table :data="selectedIssue.affectedBrokers" stripe>
            <el-table-column prop="brokerName" label="券商" min-width="120" />
            <el-table-column label="影响状态" min-width="100">
              <template #default="{ row }">
                <StatusTag :label="row.isAffected ? '受影响' : '无影响'" />
              </template>
            </el-table-column>
            <el-table-column prop="fixStatus" label="修复状态" min-width="110">
              <template #default="{ row }">
                <span class="fix-status-tag" :class="getFixStatusClass(row.isAffected ? row.fixStatus : '不适用')">
                  {{ row.isAffected ? row.fixStatus : "不适用" }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="fixVersion" label="修复版本" min-width="110">
              <template #default="{ row }">{{ row.fixVersion || "-" }}</template>
            </el-table-column>
            <el-table-column prop="releasedAt" label="发版时间" min-width="130">
              <template #default="{ row }">{{ row.releasedAt || "-" }}</template>
            </el-table-column>
            <el-table-column prop="impactDesc" label="影响说明" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">{{ row.isAffected ? (row.impactDesc || "-") : "无影响" }}</template>
            </el-table-column>
            <el-table-column prop="verifiedResult" label="验证结果" min-width="160" show-overflow-tooltip>
              <template #default="{ row }">{{ row.verifiedResult || "-" }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openStatusDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>
    </el-drawer>

    <el-dialog v-model="issueDialogVisible" :title="editingIssueId ? '编辑事项' : '新增事项'" width="820px">
      <el-form ref="issueFormRef" :model="issueForm" :rules="issueRules" label-width="120px">
        <el-form-item label="类型" prop="issue_type">
          <el-select v-model="issueForm.issue_type" style="width: 100%;">
            <el-option v-for="item in issueTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="issueForm.title" />
        </el-form-item>
        <el-form-item label="优先级 / 状态">
          <div class="inline-form-grid">
            <el-select v-model="issueForm.priority">
              <el-option v-for="item in priorities" :key="item" :label="item" :value="item" />
            </el-select>
            <el-select v-model="issueForm.status">
              <el-option v-for="item in issueStatuses" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="受影响券商">
          <div class="broker-picker-panel">
            <div class="broker-picker-toolbar">
              <el-checkbox
                :model-value="isAllBrokersSelected"
                :indeterminate="isBrokerSelectionIndeterminate"
                @change="handleBrokerCheckAll"
              >
                全选
              </el-checkbox>
              <span class="broker-picker-count">已选 {{ issueForm.broker_ids.length }} / {{ brokers.length }}</span>
            </div>
            <el-checkbox-group v-if="brokers.length" v-model="issueForm.broker_ids" class="broker-check-grid">
              <el-checkbox v-for="item in brokers" :key="item.id" class="broker-check-item" :label="item.id">
                {{ item.name }}
              </el-checkbox>
            </el-checkbox-group>
            <p v-else class="broker-picker-empty">暂无券商数据</p>
          </div>
        </el-form-item>
        <el-form-item label="描述信息">
          <el-input v-model="issueForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="影响范围">
          <el-input v-model="issueForm.impact_scope" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="计划修复版本">
          <el-input v-model="issueForm.planned_fix_version" />
        </el-form-item>
        <el-form-item label="解决方案">
          <el-input v-model="issueForm.solution" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="负责人 / 计划">
          <div class="inline-form-grid">
            <el-input v-model="issueForm.owner_name" placeholder="负责人" />
            <el-date-picker v-model="issueForm.planned_finish_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="issueForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="issueDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="saveIssue">保存事项</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="编辑券商修复情况" width="680px">
      <el-form :model="statusForm" label-width="120px">
        <el-form-item label="是否受影响">
          <el-switch v-model="statusForm.is_affected" active-text="受影响" inactive-text="无影响" @change="handleAffectedChange" />
        </el-form-item>
        <el-form-item label="影响说明">
          <el-input v-model="statusForm.impact_desc" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="修复状态">
          <el-select v-model="statusForm.fix_status" style="width: 100%;">
            <el-option v-for="item in fixStatuses" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="修复版本">
          <el-input v-model="statusForm.fix_version" />
        </el-form-item>
        <el-form-item label="实际发版时间">
          <el-date-picker v-model="statusForm.released_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="验证结果">
          <el-input v-model="statusForm.verified_result" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="跟进人">
          <el-input v-model="statusForm.owner_name" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="statusForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="statusSubmitting" @click="saveStatus">保存修复情况</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";

import {
  createBrokerIssue,
  deleteBrokerIssue,
  getBrokerIssueDetail,
  getBrokerIssues,
  updateBrokerIssue,
  updateBrokerIssueStatus
} from "../../api/brokerIssues";
import { getBrokers } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import type {
  BrokerIssueBrokerStatus,
  BrokerIssueDetail,
  BrokerIssuePayload,
  BrokerIssueStatusPayload,
  BrokerIssueSummary,
  BrokerSummary
} from "../../types/models";

const issueTypes = ["线上问题", "新需求", "优化建议"];
const priorities = ["高", "中", "低"];
const issueStatuses = ["待分析", "方案确认", "开发中", "待发版", "验证中", "已解决", "暂缓"];
const fixStatuses = ["未开始", "修复中", "待发版", "已发版", "验证中", "已修复", "不适用"];
const fixStatusClassMap: Record<string, string> = {
  未开始: "is-neutral",
  修复中: "is-processing",
  待发版: "is-release-pending",
  已发版: "is-released",
  验证中: "is-verifying",
  已修复: "is-fixed",
  不适用: "is-neutral"
};

const brokers = ref<BrokerSummary[]>([]);
const issues = ref<BrokerIssueSummary[]>([]);
const selectedIssue = ref<BrokerIssueDetail | null>(null);
const loading = ref(false);
const detailLoading = ref(false);
const detailDrawerVisible = ref(false);
const issueDialogVisible = ref(false);
const statusDialogVisible = ref(false);
const submitting = ref(false);
const statusSubmitting = ref(false);
const editingIssueId = ref<number | null>(null);
const editingStatusId = ref<number | null>(null);
const issueFormRef = ref<FormInstance>();

const filters = reactive({
  issue_type: "",
  status: "",
  priority: "",
  broker_id: undefined as number | undefined,
  keyword: ""
});

const issueForm = reactive({
  issue_type: "线上问题",
  title: "",
  priority: "中",
  status: "待分析",
  description: "",
  impact_scope: "",
  planned_fix_version: "",
  solution: "",
  owner_name: "",
  planned_finish_date: "",
  remark: "",
  broker_ids: [] as number[]
});

const statusForm = reactive({
  is_affected: true,
  impact_desc: "",
  fix_status: "未开始",
  fix_version: "",
  released_at: "",
  verified_result: "",
  owner_name: "",
  remark: ""
});

const issueRules: FormRules = {
  issue_type: [{ required: true, message: "请选择类型", trigger: "change" }],
  title: [{ required: true, message: "请输入标题", trigger: "blur" }]
};

function normalizeDateTimeForPicker(value?: string | null) {
  if (!value) {
    return "";
  }
  const normalized = value.replace(" ", "T");
  if (normalized.length === 16) {
    return `${normalized}:00`;
  }
  return normalized;
}

function normalizeDateTimeForApi(value?: string | null) {
  const normalized = normalizeDateTimeForPicker(value);
  return normalized || undefined;
}

function getFixStatusClass(status: string) {
  return fixStatusClassMap[status] || "is-neutral";
}

const isAllBrokersSelected = computed(() => {
  return brokers.value.length > 0 && issueForm.broker_ids.length === brokers.value.length;
});

const isBrokerSelectionIndeterminate = computed(() => {
  return issueForm.broker_ids.length > 0 && issueForm.broker_ids.length < brokers.value.length;
});

function handleBrokerCheckAll(value: string | number | boolean) {
  issueForm.broker_ids = value ? brokers.value.map((item) => item.id) : [];
}

const issueStats = computed(() => {
  const affectedBrokerIds = new Set<number>();
  issues.value.forEach((item) => {
    if (item.affectedBrokerCount > 0) {
      affectedBrokerIds.add(item.id);
    }
  });
  const today = new Date();
  const weekEnd = new Date();
  weekEnd.setDate(today.getDate() + 7);
  return {
    open: issues.value.filter((item) => item.status !== "已解决").length,
    high: issues.value.filter((item) => item.priority === "高").length,
    affectedBrokers: issues.value.reduce((sum, item) => sum + item.affectedBrokerCount, 0),
    thisWeek: issues.value.filter((item) => {
      if (!item.plannedFinishDate || item.status === "已解决") {
        return false;
      }
      const planned = new Date(item.plannedFinishDate);
      return planned >= today && planned <= weekEnd;
    }).length
  };
});

function sortByFixProgress(a: BrokerIssueSummary, b: BrokerIssueSummary) {
  const aValue = a.affectedBrokerCount ? a.fixedBrokerCount / a.affectedBrokerCount : 0;
  const bValue = b.affectedBrokerCount ? b.fixedBrokerCount / b.affectedBrokerCount : 0;
  return aValue - bValue;
}

function resetIssueForm() {
  editingIssueId.value = null;
  issueForm.issue_type = "线上问题";
  issueForm.title = "";
  issueForm.priority = "中";
  issueForm.status = "待分析";
  issueForm.description = "";
  issueForm.impact_scope = "";
  issueForm.planned_fix_version = "";
  issueForm.solution = "";
  issueForm.owner_name = "";
  issueForm.planned_finish_date = "";
  issueForm.remark = "";
  issueForm.broker_ids = [];
}

function fillIssueForm(issue: BrokerIssueDetail) {
  editingIssueId.value = issue.id;
  issueForm.issue_type = issue.issueType;
  issueForm.title = issue.title;
  issueForm.priority = issue.priority;
  issueForm.status = issue.status;
  issueForm.description = issue.description;
  issueForm.impact_scope = issue.impactScope;
  issueForm.planned_fix_version = issue.plannedFixVersion;
  issueForm.solution = issue.solution;
  issueForm.owner_name = issue.ownerName;
  issueForm.planned_finish_date = issue.plannedFinishDate;
  issueForm.remark = issue.remark;
  issueForm.broker_ids = issue.affectedBrokers.map((item) => item.brokerId);
}

function buildIssuePayload(): BrokerIssuePayload {
  const existing = new Map<number, BrokerIssueBrokerStatus>();
  selectedIssue.value?.affectedBrokers.forEach((item) => existing.set(item.brokerId, item));
  const affected_brokers: BrokerIssueStatusPayload[] = issueForm.broker_ids.map((brokerId) => {
    const previous = existing.get(brokerId);
    return {
      broker_id: brokerId,
      is_affected: previous?.isAffected ?? true,
      impact_desc: previous?.impactDesc || "",
      fix_status: previous?.fixStatus || "未开始",
      fix_version: previous?.fixVersion || "",
      released_at: normalizeDateTimeForApi(previous?.releasedAt),
      verified_result: previous?.verifiedResult || "",
      owner_name: previous?.ownerName || "",
      remark: previous?.remark || ""
    };
  });
  return {
    issue_type: issueForm.issue_type,
    title: issueForm.title,
    priority: issueForm.priority,
    status: issueForm.status,
    description: issueForm.description,
    impact_scope: issueForm.impact_scope,
    planned_fix_version: issueForm.planned_fix_version,
    solution: issueForm.solution,
    owner_name: issueForm.owner_name,
    planned_finish_date: issueForm.planned_finish_date || undefined,
    remark: issueForm.remark,
    affected_brokers
  };
}

async function loadIssues() {
  loading.value = true;
  try {
    issues.value = await getBrokerIssues({
      issue_type: filters.issue_type || undefined,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      broker_id: filters.broker_id || undefined,
      keyword: filters.keyword || undefined
    });
    if (selectedIssue.value && detailDrawerVisible.value) {
      await selectIssue(selectedIssue.value.id);
    }
  } finally {
    loading.value = false;
  }
}

async function selectIssue(issueId: number) {
  detailLoading.value = true;
  try {
    selectedIssue.value = await getBrokerIssueDetail(issueId);
  } finally {
    detailLoading.value = false;
  }
}

async function openDetail(issueId: number) {
  detailDrawerVisible.value = true;
  await selectIssue(issueId);
}

function resetFilters() {
  filters.issue_type = "";
  filters.status = "";
  filters.priority = "";
  filters.broker_id = undefined;
  filters.keyword = "";
  loadIssues();
}

function openCreateDialog() {
  resetIssueForm();
  issueDialogVisible.value = true;
}

function openEditDialog() {
  if (!selectedIssue.value) {
    return;
  }
  fillIssueForm(selectedIssue.value);
  issueDialogVisible.value = true;
}

async function saveIssue() {
  const valid = await issueFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }
  submitting.value = true;
  try {
    const payload = buildIssuePayload();
    if (editingIssueId.value) {
      await updateBrokerIssue(editingIssueId.value, payload);
      ElMessage.success("事项已更新");
      await selectIssue(editingIssueId.value);
    } else {
      const result = await createBrokerIssue(payload);
      editingIssueId.value = result.id;
      ElMessage.success("事项已新增");
      await openDetail(result.id);
    }
    issueDialogVisible.value = false;
    await loadIssues();
  } finally {
    submitting.value = false;
  }
}

function openStatusDialog(row: BrokerIssueBrokerStatus) {
  editingStatusId.value = row.id;
  statusForm.is_affected = row.isAffected;
  statusForm.impact_desc = row.isAffected ? row.impactDesc : "";
  statusForm.fix_status = row.isAffected ? row.fixStatus : "不适用";
  statusForm.fix_version = row.fixVersion;
  statusForm.released_at = normalizeDateTimeForPicker(row.releasedAt);
  statusForm.verified_result = row.verifiedResult;
  statusForm.owner_name = row.ownerName;
  statusForm.remark = row.remark;
  statusDialogVisible.value = true;
}

function handleAffectedChange(value: string | number | boolean) {
  if (value === false) {
    statusForm.impact_desc = "";
    statusForm.fix_status = "不适用";
    return;
  }

  if (statusForm.fix_status === "不适用") {
    statusForm.fix_status = "未开始";
  }
}

async function saveStatus() {
  if (!selectedIssue.value || !editingStatusId.value) {
    return;
  }
  statusSubmitting.value = true;
  try {
    const isAffected = statusForm.is_affected;
    await updateBrokerIssueStatus(selectedIssue.value.id, editingStatusId.value, {
      is_affected: isAffected,
      impact_desc: isAffected ? statusForm.impact_desc : "",
      fix_status: isAffected ? statusForm.fix_status : "不适用",
      fix_version: statusForm.fix_version,
      released_at: normalizeDateTimeForApi(statusForm.released_at),
      verified_result: statusForm.verified_result,
      owner_name: statusForm.owner_name,
      remark: statusForm.remark
    });
    statusDialogVisible.value = false;
    ElMessage.success("修复情况已更新");
    await selectIssue(selectedIssue.value.id);
    await loadIssues();
  } finally {
    statusSubmitting.value = false;
  }
}

async function handleDeleteIssue() {
  if (!selectedIssue.value) {
    return;
  }
  await ElMessageBox.confirm(`确认删除事项“${selectedIssue.value.title}”吗？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteBrokerIssue(selectedIssue.value.id);
  ElMessage.success("事项已删除");
  selectedIssue.value = null;
  detailDrawerVisible.value = false;
  await loadIssues();
}

function downloadIssueCsv() {
  const header = ["标题", "类型", "优先级", "状态", "计划修复版本", "修复进度", "影响范围", "最近更新"];
  const rows = issues.value.map((item) => [
    item.title,
    item.issueType,
    item.priority,
    item.status,
    item.plannedFixVersion,
    `${item.fixedBrokerCount}/${item.affectedBrokerCount}`,
    item.impactScope,
    item.updatedAt
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell || "").replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "问题与需求.csv";
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("问题与需求 CSV 已导出");
}

onMounted(async () => {
  brokers.value = await getBrokers();
  await loadIssues();
});
</script>

<style scoped>
.issue-topbar h2 {
  margin: 0;
  font-size: 20px;
}

.issue-stat-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.issue-filter-card {
  padding: 14px 16px;
}

.issue-filter-row {
  display: grid;
  grid-template-columns: minmax(260px, 1.5fr) minmax(130px, 0.7fr) minmax(130px, 0.7fr) minmax(160px, 0.9fr) auto auto;
  gap: 10px;
  align-items: center;
}

.progress-text {
  font-weight: 700;
  color: var(--brand);
  font-variant-numeric: tabular-nums;
}

.fix-status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 58px;
  padding: 4px 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
}

.fix-status-tag.is-neutral {
  color: #5f6b7a;
  background: #f3f5f8;
  border-color: #e1e6ee;
}

.fix-status-tag.is-processing {
  color: #1d5fd1;
  background: #eaf2ff;
  border-color: #cfe0ff;
}

.fix-status-tag.is-release-pending {
  color: #b45309;
  background: #fff4e5;
  border-color: #fed7aa;
}

.fix-status-tag.is-released {
  color: #087f8c;
  background: #e6f7f9;
  border-color: #bdebef;
}

.fix-status-tag.is-verifying {
  color: #5b4bc4;
  background: #f0eeff;
  border-color: #d8d2ff;
}

.fix-status-tag.is-fixed {
  color: #15803d;
  background: #e8f7ee;
  border-color: #bbebcc;
}

.issue-drawer {
  padding: 24px;
}

.drawer-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border);
}

.drawer-head h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.25;
}

.drawer-tags {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 10px;
  color: var(--text-subtle);
  font-size: 13px;
}

.drawer-section {
  padding-top: 18px;
}

.drawer-section h3 {
  margin: 0 0 12px;
}

.issue-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.issue-info-grid article {
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-muted);
}

.issue-info-grid small {
  display: block;
  margin-bottom: 6px;
  color: var(--text-subtle);
}

.issue-info-grid p {
  margin: 0;
  color: var(--text-main);
  line-height: 1.65;
  white-space: pre-wrap;
}

.inline-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.broker-picker-panel {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  overflow: hidden;
}

.broker-picker-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 38px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(247, 250, 252, 0.58);
}

.broker-picker-count,
.broker-picker-empty {
  color: var(--text-subtle);
  font-size: 13px;
}

.broker-check-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 190px;
  overflow: auto;
  padding: 10px 12px 12px;
}

.broker-picker-empty {
  margin: 0;
  padding: 18px 12px;
}

:deep(.broker-check-item) {
  align-items: center;
  min-height: 30px;
  margin-right: 0;
  padding: 5px 9px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: none;
  transition: border-color 0.15s ease, background 0.15s ease;
}

:deep(.broker-check-item .el-checkbox__input) {
  display: none;
}

:deep(.broker-check-item:hover) {
  border-color: #b9cbd4;
  background: rgba(247, 250, 252, 0.96);
}

:deep(.broker-check-item.is-checked) {
  border-color: #b9d3d8;
  background: rgba(231, 243, 244, 0.58);
  box-shadow: none;
}

:deep(.broker-check-item .el-checkbox__label) {
  position: relative;
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 400;
  color: var(--text-main);
  padding-left: 12px;
}

:deep(.broker-check-item .el-checkbox__label::before) {
  position: absolute;
  left: 0;
  top: 50%;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #c8d3df;
  content: "";
  transform: translateY(-50%);
}

:deep(.broker-check-item.is-checked .el-checkbox__label) {
  color: var(--text-main);
}

:deep(.broker-check-item.is-checked .el-checkbox__label::before) {
  background: #6f9fa8;
  box-shadow: none;
}

:deep(.broker-picker-toolbar .el-checkbox) {
  margin-right: 0;
  height: 24px;
  font-weight: 500;
}

:deep(.broker-picker-toolbar .el-checkbox__label) {
  color: var(--text-main);
  font-size: 13px;
}

:deep(.broker-picker-toolbar .el-checkbox__inner) {
  width: 14px;
  height: 14px;
}

@media (max-width: 1180px) {
  .issue-filter-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .issue-stat-grid,
  .issue-info-grid,
  .inline-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
