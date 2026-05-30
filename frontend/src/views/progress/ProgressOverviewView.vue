<template>
  <div class="page-shell">
    <section class="compact-toolbar">
      <div>
        <p class="eyebrow">项目总览</p>
        <h2>先看重点项目的整体推进，再进入矩阵逐家券商盯进度。</h2>
      </div>
      <div class="hero-actions compact">
        <el-button type="primary" @click="openFirstMatrix">打开推进矩阵</el-button>
      </div>
    </section>

    <section class="compact-grid overview-stat-grid">
      <article class="compact-card">
        <small>重点项目</small>
        <strong>{{ overview.summary.totalProjects }}</strong>
      </article>
      <article class="compact-card">
        <small>推进中券商</small>
        <strong>{{ overview.summary.inProgressBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>已完成券商</small>
        <strong>{{ overview.summary.completedBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>灰度中券商</small>
        <strong>{{ overview.summary.grayBrokers }}</strong>
      </article>
      <article class="compact-card">
        <small>高风险项目</small>
        <strong>{{ overview.summary.highRiskProjects }}</strong>
      </article>
    </section>

    <section class="overview-layout">
      <div class="overview-main">
        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>重点项目推进</h3>
              <p>优先看最重要的推进项目，点击卡片直接进入矩阵。</p>
            </div>
            <el-button size="small" @click="openFeaturedDialog">编辑重点项目</el-button>
          </div>
          <div v-if="overview.featuredProjects.length" class="featured-project-grid">
            <article
              v-for="item in overview.featuredProjects"
              :key="item.projectTemplateId"
              class="project-overview-card"
              @click="goMatrix(item.projectTemplateId)"
            >
              <div class="project-card-head">
                <div>
                  <strong>{{ item.projectName }}</strong>
                  <small>平均进度 {{ item.avgProgress }}%</small>
                </div>
                <StatusTag :label="item.projectStatus" />
              </div>
              <el-progress :percentage="item.avgProgress" :stroke-width="8" />
              <div class="project-card-metrics">
                <span>覆盖 {{ item.brokerCount }}</span>
                <span>完成 {{ item.completedCount }}</span>
                <span>灰度 {{ item.grayCount }}</span>
              </div>
            </article>
          </div>
          <EmptyBlock
            v-else
            title="当前还没有重点项目"
            description="点击“编辑重点项目”，选择最多 3 个项目展示在这里。"
          />
        </section>

        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>完整项目总表</h3>
              <p>统一查看覆盖券商、未完成数量、风险和最近更新。</p>
            </div>
          </div>
          <el-table
            v-if="overview.projectRows.length"
            :data="overview.projectRows"
            stripe
            v-loading="loading"
          >
            <el-table-column prop="projectName" label="项目名称" min-width="170" sortable />
            <el-table-column prop="projectStatus" label="项目状态" min-width="110" sortable>
              <template #default="{ row }">
                <StatusTag :label="row.projectStatus" />
              </template>
            </el-table-column>
            <el-table-column prop="brokerCount" label="覆盖券商" min-width="100" sortable />
            <el-table-column prop="completedCount" label="已完成" min-width="90" sortable />
            <el-table-column prop="grayCount" label="灰度中" min-width="90" sortable />
            <el-table-column prop="unfinishedCount" label="未完成" min-width="90" sortable />
            <el-table-column prop="riskCount" label="风险数" min-width="90" sortable />
            <el-table-column prop="latestUpdateAt" label="最近更新" min-width="110" sortable>
              <template #default="{ row }">{{ row.latestUpdateAt || "-" }}</template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="goMatrix(row.projectTemplateId)">查看矩阵</el-button>
              </template>
            </el-table-column>
          </el-table>
          <EmptyBlock
            v-else
            title="当前还没有项目推进数据"
            description="新增推进项目后，这里会汇总所有项目。"
          />
        </section>
      </div>

      <aside class="overview-side">
        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>未完成项目</h3>
              <p>展示全部未完成项目，不按最近更新时间过滤。</p>
            </div>
          </div>
          <div v-if="overview.unfinishedProjects.length" class="quick-list">
            <button
              v-for="item in overview.unfinishedProjects"
              :key="item.projectTemplateId"
              class="overview-list-item"
              type="button"
              @click="goMatrix(item.projectTemplateId)"
            >
              <div class="overview-list-head">
                <strong>{{ item.projectName }}</strong>
                <StatusTag :label="item.projectStatus" />
              </div>
              <div class="overview-list-meta">
                <span>未完成 {{ item.unfinishedCount }}/{{ item.brokerCount }}</span>
                <span>平均 {{ item.avgProgress }}%</span>
                <span>风险 {{ item.riskCount }}</span>
              </div>
              <small>最近更新：{{ item.latestUpdateAt || "-" }}</small>
            </button>
          </div>
          <EmptyBlock
            v-else
            title="当前没有未完成项目"
            description="所有推进项目完成后，这里会保持为空。"
          />
        </section>

        <section class="section-card">
          <div class="section-title">
            <div>
              <h3>高风险提醒</h3>
              <p>优先展示需要立即关注的风险和阻塞。</p>
            </div>
          </div>
          <div v-if="overview.riskHighlights.length" class="quick-list">
            <article
              v-for="item in overview.riskHighlights"
              :key="item.id"
              class="overview-risk-item"
            >
              <div class="overview-list-head">
                <strong>{{ item.title }}</strong>
                <StatusTag :label="item.level" />
              </div>
              <div class="overview-list-meta">
                <span>{{ item.projectName }}</span>
                <span>{{ item.brokerName }}</span>
              </div>
              <small>{{ item.status }} · {{ item.updatedAt || "-" }}</small>
            </article>
          </div>
          <EmptyBlock
            v-else
            title="当前没有高风险提醒"
            description="新增风险或阻塞后，这里会集中展示。"
          />
        </section>
      </aside>
    </section>

    <el-dialog v-model="featuredDialogVisible" title="编辑重点项目" width="560px">
      <p class="featured-dialog-tip">选择最多 3 个项目展示在“重点项目推进”区域，保存后立即生效。</p>
      <el-checkbox-group v-model="featuredProjectIds" :max="3" class="featured-project-options">
        <el-checkbox
          v-for="item in overview.projectRows"
          :key="item.projectTemplateId"
          :label="item.projectTemplateId"
        >
          <span class="featured-option">
            <strong>{{ item.projectName }}</strong>
            <small>平均进度 {{ item.avgProgress }}% · 覆盖 {{ item.brokerCount }} 家券商</small>
          </span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="featuredDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="featuredSaving" @click="saveFeaturedProjects">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import { getProgressProjectOverview, updateProgressFeaturedProjects } from "../../api/progress";
import type { ProgressProjectOverview } from "../../types/models";

const router = useRouter();
const loading = ref(false);
const featuredDialogVisible = ref(false);
const featuredSaving = ref(false);
const featuredProjectIds = ref<number[]>([]);
const overview = ref<ProgressProjectOverview>({
  summary: {
    totalProjects: 0,
    inProgressBrokers: 0,
    completedBrokers: 0,
    grayBrokers: 0,
    highRiskProjects: 0
  },
  featuredProjects: [],
  projectRows: [],
  unfinishedProjects: [],
  riskHighlights: []
});

function goMatrix(projectTemplateId: number) {
  router.push(`/progress/matrix?projectId=${projectTemplateId}`);
}

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getProgressProjectOverview();
  } finally {
    loading.value = false;
  }
}

function openFeaturedDialog() {
  featuredProjectIds.value = overview.value.featuredProjects.map((item) => item.projectTemplateId);
  featuredDialogVisible.value = true;
}

async function saveFeaturedProjects() {
  featuredSaving.value = true;
  try {
    await updateProgressFeaturedProjects({ project_template_ids: featuredProjectIds.value });
    await loadOverview();
    featuredDialogVisible.value = false;
    ElMessage.success("重点项目已更新");
  } finally {
    featuredSaving.value = false;
  }
}

function openFirstMatrix() {
  const firstProject = overview.value.projectRows[0];
  if (!firstProject) {
    return;
  }
  goMatrix(firstProject.projectTemplateId);
}

onMounted(loadOverview);
</script>

<style scoped>
.overview-stat-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.overview-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.85fr) minmax(320px, 0.85fr);
  gap: 16px;
  align-items: start;
}

.overview-main,
.overview-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compact-toolbar h2 {
  margin: 0;
  font-size: 20px;
}

.featured-project-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.project-overview-card,
.overview-list-item,
.overview-risk-item {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-muted);
  text-align: left;
}

.featured-dialog-tip {
  margin: 0 0 12px;
  color: var(--text-subtle);
  line-height: 1.6;
}

.featured-project-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow: auto;
}

.featured-project-options :deep(.el-checkbox) {
  height: auto;
  align-items: flex-start;
  margin-right: 0;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface-muted);
}

.featured-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  white-space: normal;
}

.featured-option strong {
  color: var(--text-main);
}

.featured-option small {
  color: var(--text-subtle);
}

.project-overview-card,
.overview-list-item {
  cursor: pointer;
}

.project-overview-card:hover,
.overview-list-item:hover {
  border-color: rgba(15, 109, 121, 0.26);
  background: rgba(255, 255, 255, 0.94);
}

.project-card-head,
.overview-list-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 10px;
}

.project-card-head strong,
.overview-list-head strong {
  display: block;
  margin-bottom: 4px;
  color: var(--text-main);
}

.project-card-head small,
.overview-list-item small,
.overview-risk-item small {
  color: var(--text-subtle);
}

.project-card-metrics,
.overview-list-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
  color: var(--text-subtle);
  font-size: 13px;
}

@media (max-width: 1280px) {
  .featured-project-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .overview-layout {
    grid-template-columns: 1fr;
  }

  .overview-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .featured-project-grid,
  .overview-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
