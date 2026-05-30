<template>
  <div class="page-shell">
    <section class="compact-toolbar">
      <div>
        <p class="eyebrow">平台级治理</p>
        <h2>工作日历</h2>
        <p class="compact-muted">统一维护工作日、法定节假日、调休工作日和特殊休息日，供所有排期能力复用。</p>
      </div>
      <div class="hero-actions compact">
        <el-button @click="router.push('/new-brokers')">返回新券商接入</el-button>
        <el-button>导入节假日</el-button>
        <el-button type="primary">新增修正</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4">
      <article v-for="item in summaryCards" :key="item.label" class="compact-card">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
        <span>{{ item.note }}</span>
      </article>
    </section>

    <section class="calendar-layout">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>月历维护</h3>
            <p>点击日期后可标记为工作日、休息日、节假日或调休工作日。</p>
          </div>
          <div class="compact-toolbar-group">
            <el-select v-model="selectedYear" size="small" style="width: 120px;">
              <el-option label="2026 年" value="2026" />
              <el-option label="2027 年" value="2027" />
            </el-select>
            <el-select v-model="selectedMonth" size="small" style="width: 120px;">
              <el-option label="5 月" value="5" />
              <el-option label="6 月" value="6" />
            </el-select>
          </div>
        </div>
        <div class="calendar-toolbar">
          <span>2026 年 5 月</span>
          <span>默认：周一至周五工作</span>
          <span>应用：中国大陆</span>
        </div>
        <section class="calendar-grid">
          <strong v-for="item in weekdays" :key="item" class="weekday">{{ item }}</strong>
          <article
            v-for="day in calendarDays"
            :key="day.date"
            :class="['calendar-day', day.type]"
          >
            <strong>{{ day.date }}</strong>
            <span>{{ day.label }}</span>
          </article>
        </section>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>规则与引用</h3>
            <p>日历是平台能力，不属于某一个项目模块。</p>
          </div>
        </div>
        <div class="quick-list">
          <article v-for="item in rules" :key="item.title" class="quick-item">
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </article>
        </div>
      </section>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>手工修正记录</h3>
          <p>保留谁在什么时候把某天改成了什么类型，便于追溯排期变化。</p>
        </div>
      </div>
      <el-table :data="adjustments" stripe>
        <el-table-column prop="date" label="日期" min-width="120" sortable />
        <el-table-column prop="type" label="类型" min-width="120" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.type" />
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="220" />
        <el-table-column prop="scope" label="影响模块" min-width="180" />
        <el-table-column prop="operator" label="更新人" min-width="100" sortable />
        <el-table-column prop="updatedAt" label="更新时间" min-width="120" sortable />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const selectedYear = ref("2026");
const selectedMonth = ref("5");

const summaryCards = [
  { label: "当前日历", value: "2026", note: "中国大陆工作日历" },
  { label: "法定节假日", value: "29", note: "自动内置，可手工覆盖" },
  { label: "调休工作日", value: "7", note: "周末但计入工作日" },
  { label: "手工修正", value: "3", note: "项目级排期实时读取" }
];

const weekdays = ["一", "二", "三", "四", "五", "六", "日"];
const calendarDays = [
  { date: 4, label: "工作", type: "" },
  { date: 5, label: "工作", type: "" },
  { date: 6, label: "工作", type: "" },
  { date: 7, label: "工作", type: "" },
  { date: 8, label: "工作", type: "" },
  { date: 9, label: "周末", type: "off" },
  { date: 10, label: "周末", type: "off" },
  { date: 11, label: "工作", type: "" },
  { date: 12, label: "法定节假", type: "holiday" },
  { date: 13, label: "法定节假", type: "holiday" },
  { date: 14, label: "工作", type: "" },
  { date: 15, label: "工作", type: "" },
  { date: 16, label: "调休工作", type: "work" },
  { date: 17, label: "周末", type: "off" },
  { date: 18, label: "工作", type: "" },
  { date: 19, label: "工作", type: "" },
  { date: 20, label: "特殊休息", type: "adjust" },
  { date: 21, label: "工作", type: "" },
  { date: 22, label: "工作", type: "" },
  { date: 23, label: "周末", type: "off" },
  { date: 24, label: "周末", type: "off" }
];

const rules = [
  { title: "默认规则", desc: "周六、周日不算工作日；法定节假日不算工作日；调休上班日算工作日。" },
  { title: "优先级", desc: "手工修正优先于内置节假日，内置节假日优先于默认周末规则。" },
  { title: "影响范围", desc: "新券商接入排期、普通项目任务计划、风险计划关闭、临期/逾期提醒、周报周期统计。" },
  { title: "更新策略", desc: "未来年份可批量导入，历史年份保留快照，避免老项目计划被新规则误改。" }
];

const adjustments = [
  { date: "2026-05-16", type: "调休工作日", reason: "节假日调休补班", scope: "全部排期", operator: "系统内置", updatedAt: "2026-05-01" },
  { date: "2026-05-20", type: "特殊休息日", reason: "公司统一培训，项目排期不计入工作日", scope: "新券商接入、任务提醒", operator: "项目管理员", updatedAt: "2026-05-18" },
  { date: "2026-06-06", type: "节假日", reason: "端午假期补充", scope: "全部排期", operator: "系统内置", updatedAt: "2026-05-01" }
];
</script>

<style scoped>
.compact-toolbar h2 {
  margin: 0;
  font-size: 20px;
}

.compact-card span {
  display: block;
  margin-top: 6px;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.5;
}

.calendar-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
  gap: 16px;
  align-items: start;
}

.calendar-toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  color: var(--text-subtle);
  font-size: 13px;
}

.calendar-toolbar span {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-muted);
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
}

.weekday {
  text-align: center;
  color: var(--text-subtle);
  font-size: 12px;
}

.calendar-day {
  min-height: 72px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
}

.calendar-day span {
  color: var(--text-subtle);
  font-size: 12px;
}

.calendar-day.off {
  background: #f1f4f8;
  color: #98a2b3;
}

.calendar-day.holiday {
  background: #fdeceb;
  color: var(--danger);
  border-color: #f7c5bf;
}

.calendar-day.work {
  background: #e7f5ef;
  color: var(--success);
  border-color: #b7dfcf;
}

.calendar-day.adjust {
  background: #fff1e8;
  color: var(--warm);
  border-color: #f6d0b8;
}

.quick-item p {
  margin: 4px 0 0;
  color: var(--text-subtle);
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .calendar-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .calendar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
