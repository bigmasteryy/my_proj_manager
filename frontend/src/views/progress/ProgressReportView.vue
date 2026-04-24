<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">项目周报</p>
        <h2>围绕批量推进项目自动汇总本周推进、风险和下周计划。</h2>
        <p>先选项目，再生成周报内容，适合直接复制到汇报材料里。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedProjectId" clearable style="width: 240px;" placeholder="全部重点项目">
          <el-option v-for="item in projects" :key="item.projectTemplateId" :label="item.projectName" :value="item.projectTemplateId" />
        </el-select>
        <el-button type="primary" @click="loadReport">生成周报</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>周报摘要</h3>
          <p>{{ report.summary }}</p>
        </div>
      </div>
      <div class="split-grid">
        <section class="section-card">
          <h3>本周完成</h3>
          <ul class="bullet-panel">
            <li v-for="item in report.completed" :key="item">{{ item }}</li>
          </ul>
        </section>
        <section class="section-card">
          <h3>下周推进</h3>
          <ul class="bullet-panel">
            <li v-for="item in report.nextWeek" :key="item">{{ item }}</li>
          </ul>
        </section>
      </div>
      <div class="split-grid">
        <section class="section-card">
          <h3>风险与阻塞</h3>
          <ul class="bullet-panel">
            <li v-for="item in report.risks" :key="item">{{ item }}</li>
          </ul>
        </section>
        <section class="section-card">
          <h3>需协调事项</h3>
          <ul class="bullet-panel">
            <li v-for="item in report.coordination" :key="item">{{ item }}</li>
          </ul>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { getProgressProjects, getProgressWeeklyReport } from "../../api/progress";
import type { ProgressProjectSummary, WeeklyReport } from "../../types/models";

const projects = ref<ProgressProjectSummary[]>([]);
const selectedProjectId = ref<number | undefined>();
const report = ref<WeeklyReport>({
  summary: "",
  completed: [],
  nextWeek: [],
  overdue: [],
  risks: [],
  coordination: []
});

async function loadReport() {
  report.value = await getProgressWeeklyReport(selectedProjectId.value);
}

onMounted(async () => {
  projects.value = await getProgressProjects();
  await loadReport();
});

watch(selectedProjectId, async () => {
  await loadReport();
});
</script>
