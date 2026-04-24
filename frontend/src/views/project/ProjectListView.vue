<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目列表</p>
        <h2>按券商、状态和负责人筛选项目，再进入详情处理。</h2>
        <p>这页适合作为你日常项目扫描入口，先筛重点，再进详情。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="openCreateProjectDialog">新增项目</el-button>
        <el-button @click="resetFilters">重置筛选</el-button>
        <el-button @click="downloadProjectCsv">导出 CSV</el-button>
        <el-button type="primary" @click="loadProjects">查询项目</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4">
      <article class="compact-card">
        <small>当前项目数</small>
        <strong>{{ projectSummary.total }}</strong>
      </article>
      <article class="compact-card">
        <small>执行中</small>
        <strong>{{ projectSummary.active }}</strong>
      </article>
      <article class="compact-card">
        <small>高风险 / 逾期</small>
        <strong>{{ projectSummary.highRisk }}/{{ projectSummary.overdue }}</strong>
      </article>
      <article class="compact-card">
        <small>平均进度</small>
        <strong>{{ projectSummary.avgProgress }}%</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>筛选条件</h3>
          <p>支持按券商、状态、负责人、关键词快速筛选。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-form-item label="券商" style="margin-bottom: 0;">
          <el-select v-model="filters.broker_id" clearable placeholder="全部券商">
            <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" style="margin-bottom: 0;">
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="规划中" value="规划中" />
            <el-option label="准备中" value="准备中" />
            <el-option label="执行中" value="执行中" />
            <el-option label="待收尾" value="待收尾" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人" style="margin-bottom: 0;">
          <el-input v-model="filters.owner_name" placeholder="按负责人筛选" @keyup.enter="loadProjects" />
        </el-form-item>
        <el-form-item label="关键词" style="margin-bottom: 0;">
          <el-input v-model="filters.keyword" placeholder="项目/类型/说明" @keyup.enter="loadProjects" />
        </el-form-item>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>项目列表</h3>
          <p>当前筛选结果 {{ projects.length }} 个项目。</p>
        </div>
      </div>
      <el-table v-if="projects.length" :data="projects" stripe>
        <el-table-column prop="brokerName" label="券商" min-width="140" />
        <el-table-column prop="projectName" label="项目" min-width="220" />
        <el-table-column prop="projectType" label="类型" min-width="120" />
        <el-table-column prop="ownerName" label="负责人" min-width="100" />
        <el-table-column prop="plannedDate" label="关键日期" min-width="120" />
        <el-table-column label="进度" min-width="100">
          <template #default="{ row }">
            {{ row.progressPercent }}%
          </template>
        </el-table-column>
        <el-table-column label="风险/逾期" min-width="120">
          <template #default="{ row }">
            {{ row.riskCount }}/{{ row.overdueCount }}
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="120">
          <template #default="{ row }">
            <StatusTag :label="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/projects/${row.id}`)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前没有匹配的项目"
        description="可以先放宽筛选条件，或直接回到首页创建项目。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openCreateProjectDialog">新增项目</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog
      v-model="projectDialogVisible"
      title="新增项目"
      width="640px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleProjectDialogBeforeClose"
    >
      <el-form ref="projectFormRef" :model="projectForm" :rules="projectRules" label-width="110px">
        <el-form-item label="所属券商" prop="broker_id">
          <el-select v-model="projectForm.broker_id" placeholder="请选择券商" style="width: 100%;">
            <el-option
              v-for="broker in brokers"
              :key="broker.id"
              :label="broker.name"
              :value="broker.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" placeholder="例如：2026-04-20 版本升级" />
        </el-form-item>
        <el-form-item label="项目类型" prop="project_type">
          <el-select v-model="projectForm.project_type" placeholder="请选择类型" style="width: 100%;">
            <el-option label="版本升级" value="版本升级" />
            <el-option label="接口改造" value="接口改造" />
            <el-option label="常规对接" value="常规对接" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目负责人" prop="owner_name">
          <el-input v-model="projectForm.owner_name" placeholder="填写负责人姓名" />
        </el-form-item>
        <el-form-item label="关键日期" prop="planned_date">
          <el-date-picker
            v-model="projectForm.planned_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择关键计划日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="项目状态" prop="status">
          <el-select v-model="projectForm.status" style="width: 100%;">
            <el-option label="准备中" value="准备中" />
            <el-option label="执行中" value="执行中" />
            <el-option label="规划中" value="规划中" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目说明">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="4"
            placeholder="补充项目背景、交付内容、当前关注点"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="requestCloseProjectDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreateProject">创建项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";
import { getBrokers } from "../../api/brokers";
import { createProject, getProjects } from "../../api/projects";
import type { BrokerSummary, DashboardProject, ProjectCreatePayload } from "../../types/models";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const brokers = ref<BrokerSummary[]>([]);
const projects = ref<DashboardProject[]>([]);
const projectDialogVisible = ref(false);
const submitting = ref(false);
const projectFormSnapshot = ref("");
const projectFormRef = ref<FormInstance>();

const projectForm = reactive<ProjectCreatePayload>({
  broker_id: 0,
  name: "",
  project_type: "版本升级",
  owner_name: "",
  planned_date: "",
  status: "准备中",
  description: ""
});

const filters = reactive<{
  broker_id?: number;
  status: string;
  owner_name: string;
  keyword: string;
}>({
  broker_id: undefined,
  status: "",
  owner_name: "",
  keyword: ""
});

const projectRules: FormRules<ProjectCreatePayload> = {
  broker_id: [{ required: true, message: "请选择券商", trigger: "change" }],
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
  project_type: [{ required: true, message: "请选择项目类型", trigger: "change" }],
  owner_name: [{ required: true, message: "请输入负责人", trigger: "blur" }],
  planned_date: [{ required: true, message: "请选择关键日期", trigger: "change" }],
  status: [{ required: true, message: "请选择项目状态", trigger: "change" }]
};

const projectSummary = computed(() => {
  const total = projects.value.length;
  const active = projects.value.filter((item) => item.status === "执行中").length;
  const highRisk = projects.value.filter((item) => item.riskCount > 0).length;
  const overdue = projects.value.reduce((sum, item) => sum + item.overdueCount, 0);
  const avgProgress = total
    ? Math.round(projects.value.reduce((sum, item) => sum + item.progressPercent, 0) / total)
    : 0;

  return {
    total,
    active,
    highRisk,
    overdue,
    avgProgress
  };
});

function createSnapshot<T>(value: T) {
  return JSON.stringify(value);
}

function resetProjectForm() {
  projectForm.broker_id = brokers.value[0]?.id ?? 0;
  projectForm.name = "";
  projectForm.project_type = "版本升级";
  projectForm.owner_name = "";
  projectForm.planned_date = "";
  projectForm.status = "准备中";
  projectForm.description = "";
}

function openCreateProjectDialog() {
  resetProjectForm();
  projectFormSnapshot.value = createSnapshot(projectForm);
  projectDialogVisible.value = true;
}

async function confirmDiscardProjectForm() {
  const dirty = createSnapshot(projectForm) !== projectFormSnapshot.value;
  if (!dirty) {
    return true;
  }

  try {
    await ElMessageBox.confirm(
      "项目内容尚未保存，确定要关闭吗？",
      "放弃未保存内容",
      {
        type: "warning",
        confirmButtonText: "放弃并关闭",
        cancelButtonText: "继续编辑"
      }
    );
    return true;
  } catch {
    return false;
  }
}

async function requestCloseProjectDialog() {
  const shouldClose = await confirmDiscardProjectForm();
  if (!shouldClose) {
    return;
  }
  projectDialogVisible.value = false;
}

async function handleProjectDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardProjectForm();
  if (shouldClose) {
    done();
  }
}

function resetFilters() {
  filters.broker_id = undefined;
  filters.status = "";
  filters.owner_name = "";
  filters.keyword = "";
  void loadProjects();
}

async function loadProjects() {
  projects.value = await getProjects({
    broker_id: filters.broker_id,
    status: filters.status,
    owner_name: filters.owner_name,
    keyword: filters.keyword
  });
}

async function handleCreateProject() {
  const valid = await projectFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    const created = await createProject(projectForm);
    projectDialogVisible.value = false;
    await loadProjects();
    ElMessage.success("项目已创建");
    router.push(`/projects/${created.id}`);
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  brokers.value = await getBrokers();
  resetProjectForm();
  await loadProjects();
});

watch(projectDialogVisible, (visible) => {
  if (!visible) {
    projectFormSnapshot.value = "";
    resetProjectForm();
  }
});

function downloadProjectCsv() {
  const header = ["券商", "项目", "类型", "负责人", "关键日期", "进度", "风险数", "逾期数", "状态"];
  const rows = projects.value.map((item) => [
    item.brokerName,
    item.projectName,
    item.projectType,
    item.ownerName,
    item.plannedDate,
    `${item.progressPercent}%`,
    item.riskCount,
    item.overdueCount,
    item.status
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "项目列表.csv";
  link.click();
  URL.revokeObjectURL(url);
}
</script>
