<template>
  <div class="page-shell">
    <section class="compact-toolbar">
      <div>
        <p class="eyebrow">新建新券商</p>
        <h2>生成接入计划</h2>
        <p class="compact-muted">在新建页面选择券商、模板、排期方式和全局工作日历，生成后进入该券商的接入详情。</p>
      </div>
      <div class="hero-actions compact">
        <el-button @click="router.push('/new-brokers')">返回总览</el-button>
        <el-button>保存草稿</el-button>
        <el-button type="primary" @click="router.push('/new-brokers')">生成并进入详情</el-button>
      </div>
    </section>

    <section class="create-layout">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>基础信息</h3>
            <p>新券商接入项目创建时一次性生成阶段、阶段任务和基线计划。</p>
          </div>
        </div>
        <el-form label-position="top">
          <section class="form-grid">
            <el-form-item label="券商">
              <el-input model-value="东莞证券" />
            </el-form-item>
            <el-form-item label="项目名称">
              <el-input model-value="订单系统对接东莞证券" />
            </el-form-item>
            <el-form-item label="项目负责人">
              <el-input model-value="戴洪添" />
            </el-form-item>
            <el-form-item label="接入模板">
              <el-select model-value="new-broker-v1" style="width: 100%;">
                <el-option label="新券商订单系统接入模板 V1" value="new-broker-v1" />
              </el-select>
            </el-form-item>
          </section>
          <el-form-item label="说明">
            <el-input
              model-value="用于新券商订单系统接入，包含方案沟通、环境部署、功能适配、验收、生产部署、灰度、小规模放开和正式上线。"
              type="textarea"
              :rows="4"
            />
          </el-form-item>
        </el-form>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>排期设置</h3>
            <p>这块从总览页面移到新建流程里。</p>
          </div>
        </div>
        <el-form label-position="top">
          <el-form-item label="生成方式">
            <el-segmented v-model="scheduleMode" :options="scheduleModeOptions" />
          </el-form-item>
          <section class="form-grid">
            <el-form-item label="计划开始日期">
              <el-input :model-value="scheduleMode === 'reverse' ? '自动倒推出：2026-02-18' : '2026-02-18'" />
            </el-form-item>
            <el-form-item label="目标上线日期">
              <el-date-picker model-value="2026-08-28" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
            </el-form-item>
            <el-form-item label="工作日历">
              <el-select model-value="china-2026" style="width: 100%;">
                <el-option label="中国大陆工作日历 2026" value="china-2026" />
              </el-select>
            </el-form-item>
            <el-form-item label="延期重算策略">
              <el-select model-value="current-only" style="width: 100%;">
                <el-option label="只影响当前券商，保留基线" value="current-only" />
              </el-select>
            </el-form-item>
          </section>
          <el-form-item label="日历规则">
            <el-input
              model-value="周六、周日、法定节假日不算工作日；调休上班日算工作日；手工修正由平台级工作日历统一维护。"
              type="textarea"
              :rows="3"
            />
          </el-form-item>
        </el-form>
      </section>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>生成结果预览</h3>
          <p>确认后生成该券商自己的阶段实例、阶段任务和基线计划。</p>
        </div>
        <div class="hero-actions compact">
          <el-button plain type="primary" @click="router.push('/workday-calendar')">查看工作日历</el-button>
          <el-button type="primary">重新计算</el-button>
        </div>
      </div>

      <section class="compact-grid compact-grid-3 create-summary-grid">
        <article class="compact-card">
          <small>总周期</small>
          <strong>2026-02-18 至 2026-08-28</strong>
        </article>
        <article class="compact-card">
          <small>合计工作日</small>
          <strong>135d</strong>
        </article>
        <article class="compact-card">
          <small>默认生成</small>
          <strong>17 阶段 / 82 任务</strong>
        </article>
      </section>

      <el-table :data="previewPhases" stripe>
        <el-table-column prop="name" label="阶段" min-width="220" sortable />
        <el-table-column prop="start" label="计划开始" min-width="120" sortable />
        <el-table-column prop="workDays" label="工作日" min-width="100" sortable>
          <template #default="{ row }">{{ row.workDays }}d</template>
        </el-table-column>
        <el-table-column prop="due" label="计划完成" min-width="120" sortable />
        <el-table-column prop="taskCount" label="默认任务" min-width="100" sortable />
        <el-table-column prop="level" label="关键性" min-width="120" sortable>
          <template #default="{ row }">
            <StatusTag :label="row.level" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="create-layout">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>默认任务模板</h3>
            <p>复杂阶段会自动生成多个任务，进入详情后可继续增删改。</p>
          </div>
        </div>
        <div class="quick-list">
          <article class="quick-item">
            <div>
              <strong>接口和订单系统功能适配</strong>
              <p>接口、客户端、H5、测试、后台、交易、订单回报、联调问题修复等 14 个默认任务。</p>
            </div>
          </article>
          <article class="quick-item">
            <div>
              <strong>系统安装部署</strong>
              <p>生产机器确认、应用部署、数据库配置、接口程序部署、回滚方案确认等 7 个默认任务。</p>
            </div>
          </article>
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>创建后的去向</h3>
            <p>新建页只负责生成计划，日常跟踪回到详情页。</p>
          </div>
        </div>
        <div class="quick-list">
          <article class="quick-item">
            <div>
              <strong>进入券商接入详情</strong>
              <p>查看阶段计划、阶段工作台、任务、问题、风险和推进日志。</p>
            </div>
          </article>
          <article class="quick-item">
            <div>
              <strong>同步总览摘要</strong>
              <p>总览页只展示当前阶段、总进度、下一节点、逾期任务和未关闭问题/风险。</p>
            </div>
          </article>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import StatusTag from "../../components/StatusTag.vue";

const router = useRouter();
const scheduleMode = ref("reverse");
const scheduleModeOptions = [
  { label: "按开始日期正排", value: "forward" },
  { label: "按目标上线倒排", value: "reverse" }
];

const previewPhases = [
  { name: "产品方案沟通", start: "2026-02-18", workDays: 5, due: "2026-02-24", taskCount: 4, level: "普通阶段" },
  { name: "券商信息技术、合规部门产品方案通过", start: "2026-02-25", workDays: 25, due: "2026-04-01", taskCount: 6, level: "关键里程碑" },
  { name: "测试环境部署", start: "2026-04-10", workDays: 10, due: "2026-04-23", taskCount: 8, level: "普通阶段" },
  { name: "接口和订单系统功能适配", start: "2026-05-12", workDays: 15, due: "2026-06-02", taskCount: 14, level: "高风险阶段" },
  { name: "系统安装部署", start: "2026-06-11", workDays: 5, due: "2026-06-17", taskCount: 7, level: "关键里程碑" },
  { name: "正式上线", start: "2026-08-28", workDays: 1, due: "2026-08-28", taskCount: 3, level: "关键里程碑" }
];
</script>

<style scoped>
.compact-toolbar h2 {
  margin: 0;
  font-size: 20px;
}

.create-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  align-items: start;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 14px;
}

.compact-grid-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.create-summary-grid {
  margin-bottom: 12px;
}

.create-summary-grid .compact-card strong {
  font-size: 16px;
  line-height: 1.4;
}

.quick-item p {
  margin: 4px 0 0;
  color: var(--text-subtle);
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .create-layout,
  .form-grid,
  .compact-grid-3 {
    grid-template-columns: 1fr;
  }
}
</style>
