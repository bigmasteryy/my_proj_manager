<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目详情</p>
        <h2>{{ project.brokerName }} / {{ project.name }}</h2>
        <p class="compact-muted">{{ project.description }}</p>
      </div>
      <div class="hero-actions compact">
        <StatusTag :label="project.status" />
        <el-button @click="openSaveTemplateDialog">保存为模板</el-button>
        <el-button type="primary" @click="openEditProjectDialog">编辑项目</el-button>
        <el-button type="danger" @click="handleDeleteProject">删除项目</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>切换项目</h3>
          <p>先切券商，再切项目。</p>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px;">
        <el-form-item label="切换券商" style="margin-bottom: 0;">
          <el-select
            :model-value="selectedBrokerId"
            placeholder="请选择券商"
            style="width: 100%;"
            @change="handleBrokerSwitch"
          >
            <el-option
              v-for="broker in brokers"
              :key="broker.id"
              :label="broker.name"
              :value="broker.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="切换项目" style="margin-bottom: 0;">
          <el-select
            :model-value="selectedProjectId"
            placeholder="请选择项目"
            style="width: 100%;"
            @change="handleProjectSwitch"
          >
            <el-option
              v-for="item in brokerProjects"
              :key="item.id"
              :label="item.projectName"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </div>
    </section>

    <section class="stats-grid">
      <article class="compact-card">
        <small>负责人</small>
        <strong>{{ project.ownerName }}</strong>
      </article>
      <article class="compact-card">
        <small>关键日期</small>
        <strong>{{ project.plannedDate }}</strong>
      </article>
      <article class="compact-card">
        <small>整体进度</small>
        <strong>{{ project.progressPercent }}%</strong>
      </article>
      <article class="compact-card">
        <small>当前逾期</small>
        <strong>{{ project.overdueCount }}</strong>
      </article>
      <article class="compact-card">
        <small>风险事项</small>
        <strong>{{ project.risks.length }}</strong>
      </article>
      <article class="compact-card">
        <small>跟进记录</small>
        <strong>{{ project.logs.length }}</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="progress-block" style="margin-bottom: 16px;">
        <div class="progress-meta">
          <span>项目整体推进进度</span>
          <strong>{{ project.progressPercent }}%</strong>
        </div>
        <el-progress :percentage="project.progressPercent" :stroke-width="10" />
      </div>

      <el-tabs v-model="activeDetailTab">
        <el-tab-pane :label="`任务清单 (${project.tasks.length})`" name="tasks">
          <div class="section-title">
            <div>
              <h3>任务清单</h3>
              <p>把计划时间、负责人和状态更新都集中在这里处理。</p>
            </div>
            <el-button type="primary" @click="openCreateTaskDialog">新增任务</el-button>
          </div>
          <el-table v-if="project.tasks.length" :data="project.tasks" stripe>
            <el-table-column prop="name" label="任务名称" min-width="160" />
            <el-table-column prop="ownerName" label="负责人" min-width="100" />
            <el-table-column prop="plannedDate" label="计划时间" min-width="120" />
            <el-table-column label="完成情况" min-width="220">
              <template #default="{ row }">
                <div class="table-multiline">{{ row.completionResult || row.actualAction || "-" }}</div>
              </template>
            </el-table-column>
            <el-table-column label="状态" min-width="120">
              <template #default="{ row }">
                <StatusTag :label="row.status" />
              </template>
            </el-table-column>
            <el-table-column label="更新状态" min-width="180" fixed="right">
              <template #default="{ row }">
                <div class="action-row">
                  <el-select
                    :model-value="row.status"
                    size="small"
                    style="width: 140px;"
                    @change="(value: string) => handleTaskStatusChange(row, value)"
                  >
                    <el-option label="未开始" value="未开始" />
                    <el-option label="进行中" value="进行中" />
                    <el-option label="待对方反馈" value="待对方反馈" />
                    <el-option label="已完成" value="已完成" />
                    <el-option label="已逾期" value="已逾期" />
                  </el-select>
                  <el-button link type="primary" @click="openEditTaskDialog(row)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteTask(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <EmptyBlock
            v-else
            compact
            title="当前还没有任务"
            description="可以先补充任务清单，后续进度、逾期和周报都会基于这里生成。"
          >
            <div class="empty-inline-action">
              <el-button type="primary" @click="openCreateTaskDialog">新增任务</el-button>
            </div>
          </EmptyBlock>
        </el-tab-pane>

        <el-tab-pane :label="`风险清单 (${project.risks.length})`" name="risks">
          <div class="section-title">
            <div>
              <h3>风险清单</h3>
              <p>只保留关键处理动作，方便你快速判断是否影响节点。</p>
            </div>
            <el-button @click="openCreateRiskDialog">新增风险</el-button>
          </div>
          <div v-if="project.risks.length" class="bullet-panel">
            <div v-for="risk in project.risks" :key="risk.id" class="section-card" style="padding: 16px;">
              <div style="display: flex; justify-content: space-between; gap: 12px; align-items: flex-start;">
                <div>
                  <strong>{{ risk.title }}</strong>
                  <p class="compact-note" style="margin: 8px 0 0;">
                    责任人：{{ risk.ownerName }} / 计划关闭：{{ risk.plannedResolveDate }}
                  </p>
                </div>
                <StatusTag :label="risk.level" />
              </div>
              <div class="note-panel" style="margin-top: 12px;">
                <small>应对措施</small>
                <div class="table-multiline">{{ risk.actionPlan || "当前没有补充措施。" }}</div>
              </div>
              <div style="margin-top: 12px;">
                <div class="action-row">
                  <el-select
                    :model-value="risk.status"
                    size="small"
                    style="width: 160px;"
                    @change="(value: string) => handleRiskStatusChange(risk, value)"
                  >
                    <el-option label="待处理" value="待处理" />
                    <el-option label="处理中" value="处理中" />
                    <el-option label="持续关注" value="持续关注" />
                    <el-option label="已解除" value="已解除" />
                  </el-select>
                  <el-button link type="primary" @click="openEditRiskDialog(risk)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteRisk(risk)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
          <EmptyBlock
            v-else
            compact
            title="当前没有风险项"
            description="如果项目存在阻塞、依赖或关键节点影响，可以在这里补充风险。"
          >
            <div class="empty-inline-action">
              <el-button type="primary" @click="openCreateRiskDialog">新增风险</el-button>
            </div>
          </EmptyBlock>
        </el-tab-pane>

        <el-tab-pane :label="`跟进记录 (${project.logs.length})`" name="logs">
          <div class="section-title">
            <div>
              <h3>跟进记录</h3>
              <p>按时间回看推进过程，也方便后续导出历史。</p>
            </div>
            <el-button @click="openCreateLogDialog">新增记录</el-button>
          </div>
          <ul v-if="project.logs.length" class="bullet-panel">
            <li
              v-for="log in project.logs"
              :key="log.id"
              class="section-card"
              style="list-style: none; padding: 16px;"
            >
              <div class="detail-header">
                <div>
                  <strong>{{ log.logDate }}</strong>
                  <div class="table-multiline" style="margin-top: 8px;">{{ log.content }}</div>
                  <p class="compact-note" style="margin: 8px 0 0;">下一步：{{ log.nextAction }}</p>
                </div>
                <div class="action-row">
                  <el-button link type="primary" @click="openEditLogDialog(log)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteLog(log)">删除</el-button>
                </div>
              </div>
            </li>
          </ul>
          <EmptyBlock
            v-else
            compact
            title="暂时没有跟进记录"
            description="新增一条记录后，这里会按时间沉淀整个项目的推进过程。"
          >
            <div class="empty-inline-action">
              <el-button type="primary" @click="openCreateLogDialog">新增记录</el-button>
            </div>
          </EmptyBlock>
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog
      v-model="projectDialogVisible"
      title="编辑项目"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleProjectDialogBeforeClose"
    >
      <el-form ref="projectFormRef" :model="projectForm" :rules="projectRules" label-width="110px">
        <el-form-item label="所属券商" prop="broker_id">
          <el-select v-model="projectForm.broker_id" style="width: 100%;">
            <el-option
              v-for="broker in brokers"
              :key="broker.id"
              :label="broker.name"
              :value="broker.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" />
        </el-form-item>
        <el-form-item label="项目类型" prop="project_type">
          <el-input v-model="projectForm.project_type" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner_name">
          <el-input v-model="projectForm.owner_name" />
        </el-form-item>
        <el-form-item label="关键日期" prop="planned_date">
          <el-date-picker v-model="projectForm.planned_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="projectForm.status" style="width: 100%;">
            <el-option label="规划中" value="规划中" />
            <el-option label="准备中" value="准备中" />
            <el-option label="执行中" value="执行中" />
            <el-option label="待收尾" value="待收尾" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="projectForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
          <el-button @click="requestCloseProjectDialog">取消</el-button>
        <el-button type="primary" :loading="projectSubmitting" @click="handleSaveProject">保存项目</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="taskDialogVisible"
      :title="editingTaskId ? '编辑任务' : '新增任务'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleTaskDialogBeforeClose"
    >
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="110px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="例如：后台程序包" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner_name">
          <el-input v-model="taskForm.owner_name" placeholder="填写负责人姓名" />
        </el-form-item>
        <el-form-item label="计划内容" prop="planned_content">
          <el-input v-model="taskForm.planned_content" placeholder="填写计划交付内容" />
        </el-form-item>
        <el-form-item label="计划时间" prop="planned_date">
          <el-date-picker
            v-model="taskForm.planned_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择计划时间"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="当前状态" prop="status">
          <el-select v-model="taskForm.status" style="width: 100%;">
            <el-option label="未开始" value="未开始" />
            <el-option label="进行中" value="进行中" />
            <el-option label="待对方反馈" value="待对方反馈" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>
        <el-form-item label="实际执行">
          <el-input v-model="taskForm.actual_action" />
        </el-form-item>
        <el-form-item label="完成情况">
          <el-input v-model="taskForm.completion_result" />
        </el-form-item>
      </el-form>
      <template #footer>
          <el-button @click="requestCloseTaskDialog">取消</el-button>
        <el-button type="primary" :loading="taskSubmitting" @click="handleSaveTask">保存任务</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="riskDialogVisible"
      :title="editingRiskId ? '编辑风险' : '新增风险'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleRiskDialogBeforeClose"
    >
      <el-form ref="riskFormRef" :model="riskForm" :rules="riskRules" label-width="110px">
        <el-form-item label="风险标题" prop="title">
          <el-input v-model="riskForm.title" placeholder="例如：接口验证延迟" />
        </el-form-item>
        <el-form-item label="风险等级" prop="level">
          <el-select v-model="riskForm.level" style="width: 100%;">
            <el-option label="高风险" value="高风险" />
            <el-option label="中风险" value="中风险" />
            <el-option label="低风险" value="低风险" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人" prop="owner_name">
          <el-input v-model="riskForm.owner_name" placeholder="填写责任人姓名" />
        </el-form-item>
        <el-form-item label="计划关闭" prop="planned_resolve_date">
          <el-date-picker
            v-model="riskForm.planned_resolve_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择计划关闭时间"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="风险状态" prop="status">
          <el-select v-model="riskForm.status" style="width: 100%;">
            <el-option label="待处理" value="待处理" />
            <el-option label="处理中" value="处理中" />
            <el-option label="持续关注" value="持续关注" />
            <el-option label="已解除" value="已解除" />
          </el-select>
        </el-form-item>
        <el-form-item label="影响关键节点">
          <el-switch v-model="riskForm.affects_milestone" />
        </el-form-item>
        <el-form-item label="应对措施" prop="action_plan">
          <el-input v-model="riskForm.action_plan" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
          <el-button @click="requestCloseRiskDialog">取消</el-button>
        <el-button type="primary" :loading="riskSubmitting" @click="handleSaveRisk">保存风险</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="logDialogVisible"
      :title="editingLogId ? '编辑跟进记录' : '新增跟进记录'"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleLogDialogBeforeClose"
    >
      <el-form ref="logFormRef" :model="logForm" :rules="logRules" label-width="110px">
        <el-form-item label="跟进内容" prop="content">
          <el-input v-model="logForm.content" type="textarea" :rows="4" placeholder="填写本次推进情况" />
        </el-form-item>
        <el-form-item label="下一步动作" prop="next_action">
          <el-input v-model="logForm.next_action" type="textarea" :rows="3" placeholder="填写下一步动作" />
        </el-form-item>
      </el-form>
      <template #footer>
          <el-button @click="requestCloseLogDialog">取消</el-button>
        <el-button type="primary" :loading="logSubmitting" @click="handleSaveLog">保存记录</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="saveTemplateDialogVisible"
      title="保存为模板"
      width="620px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="handleSaveTemplateDialogBeforeClose"
    >
      <el-form :model="saveTemplateForm" :rules="saveTemplateRules" label-width="110px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="saveTemplateForm.name" />
        </el-form-item>
        <el-form-item label="适用场景" prop="scene">
          <el-input v-model="saveTemplateForm.scene" />
        </el-form-item>
      </el-form>
      <template #footer>
          <el-button @click="requestCloseSaveTemplateDialog">取消</el-button>
        <el-button type="primary" :loading="saveTemplateSubmitting" @click="handleSaveAsTemplate">保存模板</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { getBrokers } from "../../api/brokers";
import { getDashboardProjects } from "../../api/dashboard";
import { saveProjectAsTemplate } from "../../api/templates";
import {
  createProjectLog,
  createRisk,
  createTask,
  deleteProject,
  deleteProjectLog,
  deleteRisk,
  deleteTask,
  getProjectDetail,
  updateProject,
  updateProjectLog,
  updateRisk,
  updateRiskStatus,
  updateTask,
  updateTaskStatus
} from "../../api/projects";
import type {
  BrokerSummary,
  DashboardProject,
  ProjectDetail,
  ProjectLogCreatePayload,
  ProjectLogUpdatePayload,
  ProjectSaveAsTemplatePayload,
  ProjectUpdatePayload,
  RiskCreatePayload,
  RiskUpdatePayload,
  TaskCreatePayload,
  TaskUpdatePayload
} from "../../types/models";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";

const route = useRoute();
const router = useRouter();
const brokers = ref<BrokerSummary[]>([]);
const projectCatalog = ref<DashboardProject[]>([]);
const project = ref<ProjectDetail>({
  id: 1,
  brokerId: 0,
  brokerName: "",
  name: "",
  projectType: "",
  ownerName: "",
  plannedDate: "",
  status: "",
  progressPercent: 0,
  overdueCount: 0,
  description: "",
  tasks: [],
  risks: [],
  logs: []
});
const projectDialogVisible = ref(false);
const taskDialogVisible = ref(false);
const riskDialogVisible = ref(false);
const logDialogVisible = ref(false);
const saveTemplateDialogVisible = ref(false);
const activeDetailTab = ref("tasks");
const projectSubmitting = ref(false);
const taskSubmitting = ref(false);
const riskSubmitting = ref(false);
const logSubmitting = ref(false);
const saveTemplateSubmitting = ref(false);
const editingTaskId = ref<number | null>(null);
const editingRiskId = ref<number | null>(null);
const editingLogId = ref<number | null>(null);
const projectFormSnapshot = ref("");
const taskFormSnapshot = ref("");
const riskFormSnapshot = ref("");
const logFormSnapshot = ref("");
const saveTemplateSnapshot = ref("");
const projectFormRef = ref<FormInstance>();
const taskFormRef = ref<FormInstance>();
const riskFormRef = ref<FormInstance>();
const logFormRef = ref<FormInstance>();
const projectForm = reactive<ProjectUpdatePayload>({
  broker_id: 1,
  name: "",
  project_type: "",
  owner_name: "",
  planned_date: "",
  status: "准备中",
  description: ""
});
const taskForm = reactive<TaskUpdatePayload>({
  name: "",
  owner_name: "",
  planned_content: "",
  planned_date: "",
  actual_action: "",
  completion_result: "",
  status: "未开始"
});
const riskForm = reactive<RiskUpdatePayload>({
  title: "",
  level: "高风险",
  affects_milestone: false,
  owner_name: "",
  planned_resolve_date: "",
  status: "待处理",
  action_plan: ""
});
const logForm = reactive<ProjectLogUpdatePayload>({
  content: "",
  next_action: ""
});
const saveTemplateForm = reactive<ProjectSaveAsTemplatePayload>({
  name: "",
  scene: ""
});

const projectId = computed(() => Number(route.params.id ?? 1));
const selectedBrokerId = ref<number | null>(null);
const selectedProjectId = ref<number | null>(null);
const brokerProjects = computed(() => {
  const brokerId = selectedBrokerId.value;
  if (!brokerId) {
    return [];
  }
  return projectCatalog.value.filter((item) => item.brokerId === brokerId);
});

const projectRules: FormRules<ProjectUpdatePayload> = {
  broker_id: [{ required: true, message: "请输入券商 ID", trigger: "change" }],
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
  project_type: [{ required: true, message: "请输入项目类型", trigger: "blur" }],
  owner_name: [{ required: true, message: "请输入负责人", trigger: "blur" }],
  planned_date: [{ required: true, message: "请选择关键日期", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

const taskRules: FormRules<TaskCreatePayload> = {
  name: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  owner_name: [{ required: true, message: "请输入负责人", trigger: "blur" }],
  planned_content: [{ required: true, message: "请输入计划内容", trigger: "blur" }],
  planned_date: [{ required: true, message: "请选择计划时间", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

const riskRules: FormRules<RiskCreatePayload> = {
  title: [{ required: true, message: "请输入风险标题", trigger: "blur" }],
  level: [{ required: true, message: "请选择风险等级", trigger: "change" }],
  owner_name: [{ required: true, message: "请输入责任人", trigger: "blur" }],
  planned_resolve_date: [{ required: true, message: "请选择计划关闭时间", trigger: "change" }],
  status: [{ required: true, message: "请选择风险状态", trigger: "change" }],
  action_plan: [{ required: true, message: "请输入应对措施", trigger: "blur" }]
};

const logRules: FormRules<ProjectLogCreatePayload> = {
  content: [{ required: true, message: "请输入跟进内容", trigger: "blur" }],
  next_action: [{ required: true, message: "请输入下一步动作", trigger: "blur" }]
};
const saveTemplateRules: FormRules<ProjectSaveAsTemplatePayload> = {
  name: [{ required: true, message: "请输入模板名称", trigger: "blur" }],
  scene: [{ required: true, message: "请输入适用场景", trigger: "blur" }]
};

function createSnapshot<T>(value: T) {
  return JSON.stringify(value);
}

async function confirmDiscardChanges(label: string, dirty: boolean) {
  if (!dirty) {
    return true;
  }

  try {
    await ElMessageBox.confirm(
      `${label}内容尚未保存，确定要关闭吗？`,
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

function resetTaskForm() {
  editingTaskId.value = null;
  taskForm.name = "";
  taskForm.owner_name = "";
  taskForm.planned_content = "";
  taskForm.planned_date = "";
  taskForm.actual_action = "";
  taskForm.completion_result = "";
  taskForm.status = "未开始";
}

function resetRiskForm() {
  editingRiskId.value = null;
  riskForm.title = "";
  riskForm.level = "高风险";
  riskForm.affects_milestone = false;
  riskForm.owner_name = "";
  riskForm.planned_resolve_date = "";
  riskForm.status = "待处理";
  riskForm.action_plan = "";
}

function resetLogForm() {
  editingLogId.value = null;
  logForm.content = "";
  logForm.next_action = "";
}

function resetSaveTemplateForm() {
  saveTemplateForm.name = `${project.value.name}模板`;
  saveTemplateForm.scene = `${project.value.projectType}沉淀模板`;
}

function fillProjectForm() {
  projectForm.broker_id = project.value.brokerId || selectedBrokerId.value || 1;
  projectForm.name = project.value.name;
  projectForm.project_type = project.value.projectType;
  projectForm.owner_name = project.value.ownerName;
  projectForm.planned_date = project.value.plannedDate;
  projectForm.status = project.value.status;
  projectForm.description = project.value.description;
}

function fillTaskForm(task: ProjectDetail["tasks"][number]) {
  editingTaskId.value = task.id;
  taskForm.name = task.name;
  taskForm.owner_name = task.ownerName;
  taskForm.planned_content = task.plannedContent;
  taskForm.planned_date = task.plannedDate;
  taskForm.actual_action = task.actualAction;
  taskForm.completion_result = task.completionResult;
  taskForm.status = task.status;
}

function fillRiskForm(risk: ProjectDetail["risks"][number]) {
  editingRiskId.value = risk.id;
  riskForm.title = risk.title;
  riskForm.level = risk.level;
  riskForm.affects_milestone = risk.affectsMilestone;
  riskForm.owner_name = risk.ownerName;
  riskForm.planned_resolve_date = risk.plannedResolveDate;
  riskForm.status = risk.status;
  riskForm.action_plan = risk.actionPlan;
}

function fillLogForm(log: ProjectDetail["logs"][number]) {
  editingLogId.value = log.id;
  logForm.content = log.content;
  logForm.next_action = log.nextAction;
}

async function loadProject() {
  project.value = await getProjectDetail(projectId.value);
  const currentCatalogItem = projectCatalog.value.find((item) => item.id === projectId.value);
  if (currentCatalogItem) {
    selectedProjectId.value = currentCatalogItem.id;
    selectedBrokerId.value = currentCatalogItem.brokerId;
  }
}

async function loadProjectCatalog() {
  projectCatalog.value = await getDashboardProjects();
}

async function loadBrokers() {
  brokers.value = await getBrokers();
}

function handleBrokerSwitch(brokerId: number) {
  selectedBrokerId.value = brokerId;
  const availableProjects = brokerProjects.value;
  if (availableProjects.length === 0) {
    ElMessage.warning("当前券商下暂无项目");
    return;
  }

  const targetProject = availableProjects[0];
  selectedProjectId.value = targetProject.id;
  void router.push(`/projects/${targetProject.id}`);
}

function handleProjectSwitch(projectValue: number) {
  selectedProjectId.value = projectValue;
  void router.push(`/projects/${projectValue}`);
}

function openEditProjectDialog() {
  fillProjectForm();
  projectFormSnapshot.value = createSnapshot(projectForm);
  projectDialogVisible.value = true;
}

function openCreateTaskDialog() {
  resetTaskForm();
  taskFormSnapshot.value = createSnapshot(taskForm);
  taskDialogVisible.value = true;
}

function openEditTaskDialog(task: ProjectDetail["tasks"][number]) {
  fillTaskForm(task);
  taskFormSnapshot.value = createSnapshot(taskForm);
  taskDialogVisible.value = true;
}

function openCreateRiskDialog() {
  resetRiskForm();
  riskFormSnapshot.value = createSnapshot(riskForm);
  riskDialogVisible.value = true;
}

function openEditRiskDialog(risk: ProjectDetail["risks"][number]) {
  fillRiskForm(risk);
  riskFormSnapshot.value = createSnapshot(riskForm);
  riskDialogVisible.value = true;
}

function openCreateLogDialog() {
  resetLogForm();
  logFormSnapshot.value = createSnapshot(logForm);
  logDialogVisible.value = true;
}

function openEditLogDialog(log: ProjectDetail["logs"][number]) {
  fillLogForm(log);
  logFormSnapshot.value = createSnapshot(logForm);
  logDialogVisible.value = true;
}

function openSaveTemplateDialog() {
  resetSaveTemplateForm();
  saveTemplateSnapshot.value = createSnapshot(saveTemplateForm);
  saveTemplateDialogVisible.value = true;
}

async function requestCloseProjectDialog() {
  const shouldClose = await confirmDiscardChanges(
    "项目表单",
    createSnapshot(projectForm) !== projectFormSnapshot.value
  );
  if (!shouldClose) {
    return;
  }
  projectDialogVisible.value = false;
}

async function requestCloseTaskDialog() {
  const shouldClose = await confirmDiscardChanges(
    "任务表单",
    createSnapshot(taskForm) !== taskFormSnapshot.value
  );
  if (!shouldClose) {
    return;
  }
  taskDialogVisible.value = false;
}

async function requestCloseRiskDialog() {
  const shouldClose = await confirmDiscardChanges(
    "风险表单",
    createSnapshot(riskForm) !== riskFormSnapshot.value
  );
  if (!shouldClose) {
    return;
  }
  riskDialogVisible.value = false;
}

async function requestCloseLogDialog() {
  const shouldClose = await confirmDiscardChanges(
    "跟进记录",
    createSnapshot(logForm) !== logFormSnapshot.value
  );
  if (!shouldClose) {
    return;
  }
  logDialogVisible.value = false;
}

async function requestCloseSaveTemplateDialog() {
  const shouldClose = await confirmDiscardChanges(
    "模板表单",
    createSnapshot(saveTemplateForm) !== saveTemplateSnapshot.value
  );
  if (!shouldClose) {
    return;
  }
  saveTemplateDialogVisible.value = false;
}

async function handleProjectDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "项目表单",
    createSnapshot(projectForm) !== projectFormSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleTaskDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "任务表单",
    createSnapshot(taskForm) !== taskFormSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleRiskDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "风险表单",
    createSnapshot(riskForm) !== riskFormSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleLogDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "跟进记录",
    createSnapshot(logForm) !== logFormSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleSaveTemplateDialogBeforeClose(done: () => void) {
  const shouldClose = await confirmDiscardChanges(
    "模板表单",
    createSnapshot(saveTemplateForm) !== saveTemplateSnapshot.value
  );
  if (shouldClose) {
    done();
  }
}

async function handleSaveProject() {
  const valid = await projectFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  projectSubmitting.value = true;
  try {
    await updateProject(projectId.value, projectForm);
    projectDialogVisible.value = false;
    await loadProject();
    ElMessage.success("项目已更新");
  } finally {
    projectSubmitting.value = false;
  }
}

async function handleDeleteProject() {
  await ElMessageBox.confirm(`确认删除项目“${project.value.name}”？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteProject(projectId.value);
  ElMessage.success("项目已删除");
  router.push("/dashboard");
}

async function handleSaveAsTemplate() {
  saveTemplateSubmitting.value = true;
  try {
    await saveProjectAsTemplate(projectId.value, saveTemplateForm);
    saveTemplateDialogVisible.value = false;
    ElMessage.success("项目已沉淀为模板");
  } finally {
    saveTemplateSubmitting.value = false;
  }
}

async function handleSaveTask() {
  const valid = await taskFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  taskSubmitting.value = true;
  try {
    if (editingTaskId.value) {
      await updateTask(editingTaskId.value, taskForm);
      ElMessage.success("任务已更新");
    } else {
      await createTask(projectId.value, taskForm);
      ElMessage.success("任务已新增");
    }
    taskDialogVisible.value = false;
    resetTaskForm();
    await loadProject();
  } finally {
    taskSubmitting.value = false;
  }
}

async function handleDeleteTask(task: ProjectDetail["tasks"][number]) {
  await ElMessageBox.confirm(`确认删除任务“${task.name}”？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteTask(task.id);
  ElMessage.success("任务已删除");
  await loadProject();
}

async function handleSaveRisk() {
  const valid = await riskFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  riskSubmitting.value = true;
  try {
    if (editingRiskId.value) {
      await updateRisk(editingRiskId.value, riskForm);
      ElMessage.success("风险已更新");
    } else {
      await createRisk(projectId.value, riskForm);
      ElMessage.success("风险已新增");
    }
    riskDialogVisible.value = false;
    resetRiskForm();
    await loadProject();
  } finally {
    riskSubmitting.value = false;
  }
}

async function handleDeleteRisk(risk: ProjectDetail["risks"][number]) {
  await ElMessageBox.confirm(`确认删除风险“${risk.title}”？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteRisk(risk.id);
  ElMessage.success("风险已删除");
  await loadProject();
}

async function handleTaskStatusChange(
  task: ProjectDetail["tasks"][number],
  status: string
) {
  await updateTaskStatus(task.id, {
    status,
    actual_action: task.actualAction,
    completion_result: task.completionResult
  });
  await loadProject();
  ElMessage.success("任务状态已更新");
}

async function handleRiskStatusChange(
  risk: ProjectDetail["risks"][number],
  status: string
) {
  await updateRiskStatus(risk.id, {
    status,
    action_plan: risk.actionPlan
  });
  await loadProject();
  ElMessage.success("风险状态已更新");
}

async function handleSaveLog() {
  const valid = await logFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  logSubmitting.value = true;
  try {
    if (editingLogId.value) {
      await updateProjectLog(editingLogId.value, logForm);
      ElMessage.success("跟进记录已更新");
    } else {
      await createProjectLog(projectId.value, logForm);
      ElMessage.success("跟进记录已新增");
    }
    logDialogVisible.value = false;
    resetLogForm();
    await loadProject();
  } finally {
    logSubmitting.value = false;
  }
}

async function handleDeleteLog(log: ProjectDetail["logs"][number]) {
  await ElMessageBox.confirm("确认删除这条跟进记录？", "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteProjectLog(log.id);
  ElMessage.success("跟进记录已删除");
  await loadProject();
}

watch(taskDialogVisible, (visible) => {
  if (!visible) {
    resetTaskForm();
    taskFormSnapshot.value = "";
  }
});

watch(riskDialogVisible, (visible) => {
  if (!visible) {
    resetRiskForm();
    riskFormSnapshot.value = "";
  }
});

watch(logDialogVisible, (visible) => {
  if (!visible) {
    resetLogForm();
    logFormSnapshot.value = "";
  }
});

watch(projectDialogVisible, (visible) => {
  if (!visible) {
    projectFormSnapshot.value = "";
  }
});

watch(saveTemplateDialogVisible, (visible) => {
  if (!visible) {
    saveTemplateSnapshot.value = "";
  }
});

watch(projectId, async () => {
  await loadProjectCatalog();
  await loadBrokers();
  await loadProject();
}, { immediate: true });
</script>
