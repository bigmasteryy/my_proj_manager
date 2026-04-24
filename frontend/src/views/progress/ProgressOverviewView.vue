<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目总览</p>
        <h2>先看三大重点项目的整体推进，再进入矩阵逐家券商盯进度。</h2>
        <p>这一页适合每天先扫全局，快速识别推进中、已完成和风险聚集的项目。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="openFirstMatrix">打开推进矩阵</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4">
      <article class="compact-card">
        <small>重点项目</small>
        <strong>{{ summary.totalProjects }}</strong>
      </article>
      <article class="compact-card">
        <small>推进中券商</small>
        <strong>{{ summary.inProgress }}</strong>
      </article>
      <article class="compact-card">
        <small>已完成券商</small>
        <strong>{{ summary.completed }}</strong>
      </article>
      <article class="compact-card">
        <small>高风险数</small>
        <strong>{{ summary.risks }}</strong>
      </article>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>重点项目列表</h3>
          <p>先按项目看全局推进，再进入矩阵查看每家券商的细节。</p>
        </div>
      </div>
      <el-table v-if="projects.length" :data="projects" stripe>
        <el-table-column prop="projectName" label="项目" min-width="180" />
        <el-table-column prop="brokerCount" label="覆盖券商" min-width="100" />
        <el-table-column prop="completedCount" label="已完成" min-width="100" />
        <el-table-column prop="inProgressCount" label="推进中" min-width="100" />
        <el-table-column prop="notStartedCount" label="未开始" min-width="100" />
        <el-table-column prop="avgProgress" label="平均进度" min-width="100">
          <template #default="{ row }">{{ row.avgProgress }}%</template>
        </el-table-column>
        <el-table-column prop="riskCount" label="风险" min-width="80" />
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/progress/matrix?projectId=${row.projectTemplateId}`)">查看矩阵</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="当前还没有项目推进数据"
        description="初始化三大重点项目后，这里会自动汇总整体推进情况。"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import EmptyBlock from "../../components/EmptyBlock.vue";
import { getProgressProjects } from "../../api/progress";
import type { ProgressProjectSummary } from "../../types/models";

const router = useRouter();
const projects = ref<ProgressProjectSummary[]>([]);

const summary = computed(() => ({
  totalProjects: projects.value.length,
  inProgress: projects.value.reduce((sum, item) => sum + item.inProgressCount, 0),
  completed: projects.value.reduce((sum, item) => sum + item.completedCount, 0),
  risks: projects.value.reduce((sum, item) => sum + item.riskCount, 0)
}));

function openFirstMatrix() {
  if (!projects.value.length) {
    return;
  }
  router.push(`/progress/matrix?projectId=${projects.value[0].projectTemplateId}`);
}

onMounted(async () => {
  projects.value = await getProgressProjects();
});
</script>
