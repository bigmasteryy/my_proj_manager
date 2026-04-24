<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">首页驾驶舱</p>
        <h1>先看重点，再推进项目。</h1>
        <p class="compact-muted">{{ overview.summary }}</p>
      </div>
      <div class="hero-actions">
        <el-button @click="openProjectDialog">新建项目</el-button>
        <el-button type="primary" @click="router.push('/risks')">查看风险中心</el-button>
      </div>
    </section>

    <div class="split-grid">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>今日待处理</h3>
            <p>先处理最影响节奏的事项。</p>
          </div>
        </div>
        <div v-if="todayFocusItems.length" class="quick-list">
          <div v-for="item in todayFocusItems" :key="item.key" class="quick-item">
            <div>
              <strong>{{ item.title }}</strong>
              <div class="compact-muted">{{ item.subtitle }}</div>
            </div>
            <el-button link type="primary" @click="item.action()">{{ item.actionLabel }}</el-button>
          </div>
        </div>
        <EmptyBlock
          v-else
          compact
          title="今天没有高优先级待处理项"
          description="当前没有逾期、明显风险或个人高优先级事项，可以直接查看重点项目。"
        >
          <div class="empty-inline-action">
            <el-button type="primary" @click="router.push('/projects')">去项目列表</el-button>
          </div>
        </EmptyBlock>
      </section>

      <section class="compact-grid">
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/brokers')">
          <small>总券商数</small>
          <strong>{{ overview.totalBrokers }}</strong>
        </article>
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/projects')">
          <small>进行中项目</small>
          <strong>{{ overview.activeProjects }}</strong>
        </article>
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/risks')">
          <small>高风险 / 逾期</small>
          <strong>{{ overview.highRiskCount }}/{{ overview.overdueTasks }}</strong>
        </article>
      </section>
    </div>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>我的任务概览</h3>
          <p>首页同时看到个人任务线，不用来回切页面。</p>
        </div>
      </div>
      <div class="compact-grid">
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/personal')">
          <small>每日任务</small>
          <strong>{{ personalSummary.daily }}</strong>
        </article>
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/personal')">
          <small>长期任务</small>
          <strong>{{ personalSummary.longTerm }}</strong>
        </article>
        <article class="compact-card interactive" style="cursor: pointer;" @click="router.push('/personal/risks')">
          <small>个人风险</small>
          <strong>{{ personalSummary.risks }}</strong>
        </article>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>重点项目</h3>
          <p>保留最关键几列，其他信息进详情再看。</p>
        </div>
      </div>
      <el-table v-if="projects.length" :data="projects" stripe>
        <el-table-column prop="brokerName" label="券商" min-width="120" />
        <el-table-column prop="projectName" label="项目" min-width="220" />
        <el-table-column prop="ownerName" label="负责人" min-width="100" />
        <el-table-column prop="plannedDate" label="关键日期" min-width="120" />
        <el-table-column label="进度" min-width="100">
          <template #default="{ row }">
            {{ row.progressPercent }}%
          </template>
        </el-table-column>
        <el-table-column label="风险/逾期" min-width="100">
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
        title="当前没有可展示的重点项目"
        description="可以先创建一个项目，首页会自动展示最需要关注的项目概况。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openProjectDialog">新建项目</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog
      v-model="projectDialogVisible"
      title="新建项目"
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
import { getDashboardOverview, getDashboardProjects } from "../../api/dashboard";
import { getPersonalRisks, getPersonalTasks } from "../../api/personal";
import { createProject } from "../../api/projects";
import type {
  BrokerSummary,
  DashboardOverview,
  DashboardProject,
  PersonalRiskItem,
  PersonalTaskItem,
  ProjectCreatePayload
} from "../../types/models";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const brokers = ref<BrokerSummary[]>([]);
const overview = ref<DashboardOverview>({
  totalBrokers: 0,
  activeProjects: 0,
  pendingTasks: 0,
  overdueTasks: 0,
  highRiskCount: 0,
  summary: ""
});
const projects = ref<DashboardProject[]>([]);
const dailyTasks = ref<PersonalTaskItem[]>([]);
const longTermTasks = ref<PersonalTaskItem[]>([]);
const personalRisks = ref<PersonalRiskItem[]>([]);
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

const projectRules: FormRules<ProjectCreatePayload> = {
  broker_id: [{ required: true, message: "请选择券商", trigger: "change" }],
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
  project_type: [{ required: true, message: "请选择项目类型", trigger: "change" }],
  owner_name: [{ required: true, message: "请输入负责人", trigger: "blur" }],
  planned_date: [{ required: true, message: "请选择关键日期", trigger: "change" }],
  status: [{ required: true, message: "请选择项目状态", trigger: "change" }]
};

function createSnapshot<T>(value: T) {
  return JSON.stringify(value);
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

const personalSummary = computed(() => ({
  daily: dailyTasks.value.length,
  longTerm: longTermTasks.value.length,
  risks: personalRisks.value.length
}));

const todayFocusItems = computed(() => {
  const projectItems = projects.value
    .filter((item) => item.overdueCount > 0 || item.riskCount > 0)
    .sort((a, b) => (b.overdueCount + b.riskCount) - (a.overdueCount + a.riskCount))
    .map((item) => ({
      key: `project-${item.id}`,
      title: item.overdueCount > 0 ? "项目存在逾期事项" : "项目存在风险待跟进",
      subtitle: `${item.brokerName} / ${item.projectName}`,
      actionLabel: "查看项目",
      action: () => router.push(`/projects/${item.id}`)
    }));

  const personalItems = personalRisks.value.map((item) => ({
    key: `personal-${item.id}`,
    title: item.type,
    subtitle: `${item.category} / ${item.title}`,
    actionLabel: "查看任务",
    action: () => router.push("/personal")
  }));

  return [...projectItems, ...personalItems].slice(0, 3);
});

async function loadDashboard() {
  const [overviewData, projectData, dailyData, longTermData, personalRiskData] = await Promise.all([
    getDashboardOverview(),
    getDashboardProjects(),
    getPersonalTasks("每日"),
    getPersonalTasks("长期"),
    getPersonalRisks()
  ]);

  overview.value = overviewData;
  projects.value = projectData;
  dailyTasks.value = dailyData;
  longTermTasks.value = longTermData;
  personalRisks.value = personalRiskData;
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

function openProjectDialog() {
  resetProjectForm();
  projectFormSnapshot.value = createSnapshot(projectForm);
  projectDialogVisible.value = true;
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

async function handleCreateProject() {
  const valid = await projectFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    const created = await createProject(projectForm);
    projectDialogVisible.value = false;
    await loadDashboard();
    ElMessage.success("项目已创建");
    router.push(`/projects/${created.id}`);
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  brokers.value = await getBrokers();
  resetProjectForm();
  await loadDashboard();
});

watch(projectDialogVisible, (visible) => {
  if (!visible) {
    projectFormSnapshot.value = "";
    resetProjectForm();
  }
});
</script>
