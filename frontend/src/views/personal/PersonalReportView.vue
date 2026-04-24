<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">个人周报</p>
        <h2>这里只生成个人任务的数据。</h2>
        <p>{{ report.summary }}</p>
      </div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button @click="downloadReportText">下载文本</el-button>
        <el-button type="primary" @click="copyReportText">复制汇报文本</el-button>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>筛选条件</h3>
          <p>支持按每日/长期筛选个人周报。</p>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: 240px 1fr; gap: 16px;">
        <el-form-item label="任务类型" style="margin-bottom: 0;">
          <el-select v-model="category" clearable placeholder="全部">
            <el-option label="每日" value="每日" />
            <el-option label="长期" value="长期" />
          </el-select>
        </el-form-item>
        <div style="display: flex; align-items: end;">
          <el-button type="primary" @click="loadReport">更新周报</el-button>
        </div>
      </div>
    </section>

    <div v-if="hasReportContent" class="split-grid">
      <section class="section-card">
        <div class="section-title"><div><h3>本周完成</h3></div></div>
        <ul class="bullet-panel"><li v-for="item in report.completed" :key="item">{{ item }}</li></ul>
      </section>
      <section class="section-card">
        <div class="section-title"><div><h3>下周计划</h3></div></div>
        <ul class="bullet-panel"><li v-for="item in report.nextWeek" :key="item">{{ item }}</li></ul>
      </section>
      <section class="section-card">
        <div class="section-title"><div><h3>逾期事项</h3></div></div>
        <ul class="bullet-panel"><li v-for="item in report.overdue" :key="item">{{ item }}</li></ul>
      </section>
      <section class="section-card">
        <div class="section-title"><div><h3>重点关注</h3></div></div>
        <ul class="bullet-panel"><li v-for="item in report.risks" :key="item">{{ item }}</li></ul>
      </section>
    </div>

    <EmptyBlock
      v-else
      title="当前没有可生成的个人周报内容"
      description="可以先补充个人任务，或切换每日/长期筛选后再试。"
    >
      <div class="empty-inline-action">
        <el-button type="primary" @click="loadReport">重新生成</el-button>
      </div>
    </EmptyBlock>

    <section v-if="hasReportContent" class="section-card">
      <div class="section-title"><div><h3>汇报文本</h3></div></div>
      <el-input :model-value="reportText" type="textarea" :rows="12" readonly />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { getPersonalWeeklyReport } from "../../api/personal";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { WeeklyReport } from "../../types/models";

const category = ref<string | undefined>(undefined);
const report = ref<WeeklyReport>({
  summary: "",
  completed: [],
  nextWeek: [],
  overdue: [],
  risks: [],
  coordination: []
});

const hasReportContent = computed(() => {
  return (
    report.value.completed.length > 0 ||
    report.value.nextWeek.length > 0 ||
    report.value.overdue.length > 0 ||
    report.value.risks.length > 0
  );
});

const reportText = computed(() => {
  const sections = [
    "【本周完成】",
    ...report.value.completed.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【下周计划】",
    ...report.value.nextWeek.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【逾期事项】",
    ...report.value.overdue.map((item, index) => `${index + 1}. ${item}`),
    "",
    "【重点关注】",
    ...report.value.risks.map((item, index) => `${index + 1}. ${item}`)
  ];
  return sections.join("\n");
});

async function copyReportText() {
  await navigator.clipboard.writeText(reportText.value);
  ElMessage.success("个人周报已复制");
}

function downloadReportText() {
  const blob = new Blob([reportText.value], { type: "text/plain;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "个人周报.txt";
  link.click();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  await loadReport();
});

async function loadReport() {
  report.value = await getPersonalWeeklyReport(category.value);
}
</script>
