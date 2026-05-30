<template>
  <div class="page-shell">
    <section class="compact-toolbar">
      <div>
        <p class="eyebrow">新券商接入</p>
        <h2>长流程项目独立管理，推进矩阵只保留摘要视角。</h2>
        <p class="compact-muted">每个券商接入项目相互独立，阶段、任务、问题风险和推进日志都在详情内维护。</p>
      </div>
      <div class="hero-actions compact">
        <el-button @click="router.push('/workday-calendar')">工作日历</el-button>
        <el-button>导出计划</el-button>
        <el-button type="primary" @click="router.push('/new-brokers/create')">新建新券商</el-button>
      </div>
    </section>

    <section class="compact-grid new-broker-stat-grid">
      <article v-for="item in summaryCards" :key="item.label" class="compact-card">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
        <span>{{ item.note }}</span>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>接入项目总览</h3>
          <p>快速识别哪家券商卡住、谁负责、下一节点是什么。</p>
        </div>
        <div class="compact-toolbar-group">
          <el-select v-model="statusFilter" size="small" style="width: 130px;">
            <el-option label="全部状态" value="全部" />
            <el-option label="WIP" value="WIP" />
            <el-option label="阻塞" value="阻塞" />
            <el-option label="未开始" value="未开始" />
          </el-select>
          <el-switch v-model="onlyDelayed" size="small" active-text="只看延期" />
        </div>
      </div>
      <el-table :data="filteredProjects" stripe>
        <el-table-column prop="brokerName" label="券商" min-width="150" sortable>
          <template #default="{ row }">
            <div class="broker-cell">
              <strong>{{ row.brokerName }}</strong>
              <small>{{ row.projectName }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="currentStage" label="当前阶段" min-width="180" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.currentStageStatus" />
            <span class="stage-name">{{ row.currentStage }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="总进度" min-width="150" sortable>
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress :percentage="row.progress" :stroke-width="8" />
              <strong>{{ row.progress }}%</strong>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="nextNode" label="下一节点" min-width="180" sortable />
        <el-table-column prop="plannedGoLive" label="计划上线" min-width="120" sortable />
        <el-table-column prop="delayDays" label="偏差" min-width="90" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.delayDays > 0 ? `+${row.delayDays}d` : '0d'" />
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" min-width="100" sortable />
        <el-table-column label="任务/问题" min-width="130" sortable :sort-method="compareIssueLoad">
          <template #default="{ row }">
            {{ row.overdueTasks }} 逾期 / {{ row.openIssues }} 问题/风险
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default>
            <el-button link type="primary">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="new-broker-detail-grid">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>东莞证券 / 阶段计划</h3>
            <p>自动排期按平台工作日历计算，周末和法定节假日不计入工期。</p>
          </div>
          <div class="hero-actions compact">
            <el-button size="small">查看基线</el-button>
            <el-button size="small" type="primary">延期重算</el-button>
          </div>
        </div>

        <section class="compact-grid compact-grid-4 detail-summary-grid">
          <article class="compact-card">
            <small>计划周期</small>
            <strong>2026-02-18 至 2026-08-28</strong>
          </article>
          <article class="compact-card">
            <small>工作日</small>
            <strong>135d</strong>
          </article>
          <article class="compact-card">
            <small>当前阶段</small>
            <strong>生产资源申请</strong>
          </article>
          <article class="compact-card">
            <small>未关闭问题/风险</small>
            <strong>6</strong>
          </article>
        </section>

        <div class="phase-list">
          <article
            v-for="phase in phases"
            :key="phase.no"
            :class="['phase-row', phase.statusClass]"
          >
            <div class="phase-index">{{ phase.no }}</div>
            <div class="phase-content">
              <div class="phase-title">
                <strong>{{ phase.name }}</strong>
                <StatusTag :label="phase.status" />
              </div>
              <div class="phase-meta">
                <span>开始：{{ phase.start }}</span>
                <span>工期：{{ phase.workDays }}d</span>
                <span>完成：{{ phase.due }}</span>
                <span>实际：{{ phase.finish || "-" }}</span>
                <span>任务：{{ phase.taskDone }}/{{ phase.taskTotal }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>阶段工作台</h3>
            <p>选中阶段后，在这里处理任务、问题、风险和推进记录。</p>
          </div>
        </div>

        <el-tabs v-model="activeWorkbenchTab">
          <el-tab-pane label="任务 14" name="tasks">
            <div class="workbench-list">
              <article v-for="task in stageTasks" :key="task.title" class="workbench-item">
                <div>
                  <strong>{{ task.title }}</strong>
                  <p>{{ task.desc }}</p>
                </div>
                <StatusTag :label="task.status" />
              </article>
            </div>
          </el-tab-pane>
          <el-tab-pane label="问题/风险 6" name="issues">
            <div class="workbench-list">
              <article v-for="issue in stageIssues" :key="issue.title" class="workbench-item issue-item">
                <div>
                  <strong>{{ issue.title }}</strong>
                  <p>{{ issue.desc }}</p>
                </div>
                <StatusTag :label="issue.level" />
              </article>
            </div>
          </el-tab-pane>
          <el-tab-pane label="日志 11" name="logs">
            <div class="workbench-list">
              <article v-for="log in stageLogs" :key="log.date" class="workbench-item">
                <div>
                  <strong>{{ log.date }}</strong>
                  <p>{{ log.content }}</p>
                </div>
                <StatusTag :label="log.type" />
              </article>
            </div>
          </el-tab-pane>
        </el-tabs>
        <p class="table-note">阶段进度可由任务完成率自动汇总，也允许项目经理手动修正。问题和风险可以挂到阶段，也可以挂到具体任务。</p>
      </section>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>全局工作日历引用</h3>
          <p>新券商接入只选择日历规则，具体节假日维护放到平台级页面。</p>
        </div>
        <el-button type="primary" plain @click="router.push('/workday-calendar')">打开日历</el-button>
      </div>
      <section class="compact-grid compact-grid-4">
        <article class="compact-card">
          <small>适用范围</small>
          <strong>多模块复用</strong>
          <span>新券商接入、普通项目任务、风险关闭、周报统计</span>
        </article>
        <article class="compact-card">
          <small>默认规则</small>
          <strong>工作日制</strong>
          <span>周六、周日、法定节假日不算工作日</span>
        </article>
        <article class="compact-card">
          <small>当前日历</small>
          <strong>中国大陆 2026</strong>
          <span>含手工修正 3 条</span>
        </article>
        <article class="compact-card">
          <small>排期影响</small>
          <strong>实时读取</strong>
          <span>计划生成和延期重算读取统一日历</span>
        </article>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import StatusTag from "../../components/StatusTag.vue";

type OnboardingProject = {
  brokerName: string;
  projectName: string;
  currentStage: string;
  currentStageStatus: string;
  progress: number;
  nextNode: string;
  plannedGoLive: string;
  delayDays: number;
  owner: string;
  overdueTasks: number;
  openIssues: number;
};

const router = useRouter();
const statusFilter = ref("全部");
const onlyDelayed = ref(false);
const activeWorkbenchTab = ref("tasks");

const summaryCards = [
  { label: "接入项目", value: "8", note: "WIP 5 / Hold 2 / Done 1" },
  { label: "本周到期阶段", value: "7", note: "含 2 个关键里程碑" },
  { label: "逾期任务", value: "12", note: "接口 4 / 测试 3 / 后台 2" },
  { label: "未关闭问题", value: "19", note: "高优先级 5 个" },
  { label: "平均偏差", value: "+6d", note: "相对基线计划" }
];

const projects: OnboardingProject[] = [
  {
    brokerName: "东莞证券",
    projectName: "订单系统对接",
    currentStage: "生产资源申请",
    currentStageStatus: "WIP",
    progress: 62,
    nextNode: "2026-07-02 系统安装部署",
    plannedGoLive: "2026-08-28",
    delayDays: 9,
    owner: "戴洪添",
    overdueTasks: 6,
    openIssues: 6
  },
  {
    brokerName: "华福证券",
    projectName: "订单系统对接",
    currentStage: "接口功能适配",
    currentStageStatus: "推进中",
    progress: 38,
    nextNode: "2026-06-10 内部验收测试",
    plannedGoLive: "2026-09-15",
    delayDays: 3,
    owner: "蒋张飞",
    overdueTasks: 3,
    openIssues: 4
  },
  {
    brokerName: "财信证券",
    projectName: "订单系统对接",
    currentStage: "测试环境部署",
    currentStageStatus: "已完成",
    progress: 28,
    nextNode: "2026-06-01 信创环境适配",
    plannedGoLive: "2026-10-12",
    delayDays: 0,
    owner: "陈良海",
    overdueTasks: 1,
    openIssues: 2
  },
  {
    brokerName: "国联民生",
    projectName: "订单系统对接",
    currentStage: "产品方案沟通",
    currentStageStatus: "未开始",
    progress: 8,
    nextNode: "2026-05-27 合规方案通过",
    plannedGoLive: "2026-11-06",
    delayDays: 0,
    owner: "易勇",
    overdueTasks: 0,
    openIssues: 1
  }
];

const phases = [
  { no: 1, name: "产品方案沟通", status: "Done", statusClass: "done", start: "2026-02-18", workDays: 5, due: "2026-02-24", finish: "2026-02-24", taskDone: 4, taskTotal: 4 },
  { no: 2, name: "券商信息技术、合规部门产品方案通过", status: "Done", statusClass: "done", start: "2026-02-25", workDays: 25, due: "2026-04-01", finish: "2026-04-03", taskDone: 6, taskTotal: 6 },
  { no: 3, name: "测试环境部署", status: "Done", statusClass: "done", start: "2026-04-10", workDays: 10, due: "2026-04-23", finish: "2026-04-25", taskDone: 8, taskTotal: 8 },
  { no: 4, name: "接口和订单系统功能适配", status: "阻塞", statusClass: "blocked", start: "2026-05-12", workDays: 15, due: "2026-06-02", finish: "", taskDone: 9, taskTotal: 14 },
  { no: 5, name: "生产机器资源和周边依赖申请", status: "WIP", statusClass: "active", start: "2026-06-03", workDays: 5, due: "2026-06-10", finish: "", taskDone: 2, taskTotal: 7 },
  { no: 6, name: "系统安装部署 / 空转 / 灰度 / 冷启动 / 通关测试 / 上线", status: "未开始", statusClass: "", start: "2026-06-11", workDays: 32, due: "2026-08-28", finish: "", taskDone: 0, taskTotal: 31 }
];

const stageTasks = [
  { title: "接口适配：委托、撤单、查询链路字段确认", desc: "负责人：戴洪添 / 计划完成：2026-05-22 / 当前卡点：券商返回字段缺少交易类别。", status: "逾期" },
  { title: "客户端适配：PC 与 APP 交易入口联调", desc: "负责人：林坚恒 / 计划完成：2026-05-27 / 已完成 APP，PC DLL 待发包。", status: "WIP" },
  { title: "H5 适配：开户后跳转参数与交易首页透传", desc: "负责人：蒋张飞 / 计划完成：2026-05-28 / 需补充券商白名单。", status: "WIP" },
  { title: "测试：回归用例与异常单覆盖", desc: "负责人：测试组 / 计划完成：2026-05-30 / 用例 38/52，通过率 81%。", status: "推进中" }
];

const stageIssues = [
  { title: "问题：测试环境柜台返回超时", desc: "影响：接口适配和测试进度 / 责任人：券商技术 / 计划解决：2026-05-24。", level: "高" },
  { title: "风险：生产资源申请未确认，可能影响系统安装窗口", desc: "影响：后续系统安装部署和空转阶段 / 责任人：运维协调 / 计划关闭：2026-06-05。", level: "风险" }
];

const stageLogs = [
  { date: "2026-05-19", content: "已向券商技术确认柜台超时问题，等待环境侧复核。", type: "普通记录" },
  { date: "2026-05-18", content: "接口字段差异已同步开发，预计 5/21 给出修复包。", type: "里程碑" }
];

const filteredProjects = computed(() => projects.filter((item) => {
  const statusMatched = statusFilter.value === "全部" || item.currentStageStatus === statusFilter.value;
  const delayMatched = !onlyDelayed.value || item.delayDays > 0;
  return statusMatched && delayMatched;
}));

function compareIssueLoad(a: OnboardingProject, b: OnboardingProject) {
  return (a.overdueTasks + a.openIssues) - (b.overdueTasks + b.openIssues);
}
</script>

<style scoped>
.compact-toolbar h2 {
  margin: 0;
  font-size: 20px;
}

.new-broker-stat-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.compact-card span {
  display: block;
  margin-top: 6px;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.5;
}

.broker-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.broker-cell small {
  color: var(--text-subtle);
}

.stage-name {
  display: inline-block;
  margin-left: 8px;
}

.new-broker-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.75fr);
  gap: 16px;
  align-items: start;
}

.detail-summary-grid {
  margin-bottom: 12px;
}

.detail-summary-grid .compact-card strong {
  font-size: 15px;
  line-height: 1.4;
}

.phase-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.phase-row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-muted);
}

.phase-index {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: var(--brand-soft);
  color: var(--brand);
  font-weight: 700;
  font-size: 12px;
}

.phase-row.done .phase-index {
  background: #e7f5ef;
  color: var(--success);
}

.phase-row.blocked .phase-index {
  background: #fdeceb;
  color: var(--danger);
}

.phase-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.phase-title strong {
  line-height: 1.45;
}

.phase-meta {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  color: var(--text-subtle);
  font-size: 12px;
}

.workbench-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.workbench-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-muted);
}

.workbench-item strong {
  display: block;
  margin-bottom: 6px;
  line-height: 1.45;
}

.workbench-item p {
  margin: 0;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.6;
}

.issue-item {
  border-left: 3px solid var(--warm);
}

@media (max-width: 1280px) {
  .new-broker-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .new-broker-detail-grid {
    grid-template-columns: 1fr;
  }

  .phase-meta {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .new-broker-stat-grid,
  .phase-meta {
    grid-template-columns: 1fr;
  }
}
</style>
