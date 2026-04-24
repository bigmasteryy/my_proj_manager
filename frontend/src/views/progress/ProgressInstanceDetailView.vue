<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">券商项目详情</p>
        <h2>{{ detail?.instance.projectName }} / {{ detail?.instance.brokerName }}</h2>
        <p class="compact-muted">{{ detail?.instance.remark || "查看某个项目在某家券商上的详细推进过程、进度项和风险。" }}</p>
      </div>
      <div class="hero-actions">
        <StatusTag v-if="detail" :label="detail.instance.status" />
        <el-button type="primary" @click="handleBack">返回</el-button>
      </div>
    </section>

    <section class="compact-grid compact-grid-4" v-if="detail">
      <article class="compact-card">
        <small>总进度</small>
        <strong>{{ detail.instance.progressPercent }}%</strong>
      </article>
      <article class="compact-card">
        <small>最近更新</small>
        <strong>{{ detail.instance.latestUpdateAt || "-" }}</strong>
      </article>
      <article class="compact-card">
        <small>风险数</small>
        <strong>{{ detail.instance.riskCount }}</strong>
      </article>
      <article class="compact-card">
        <small>里程碑</small>
        <strong>{{ detail.instance.milestoneCount }}</strong>
      </article>
    </section>

    <section class="section-card" v-if="detail">
      <div class="progress-block" style="margin-bottom: 16px;">
        <div class="progress-meta">
          <span>项目整体推进进度</span>
          <strong>{{ detail.instance.progressPercent }}%</strong>
        </div>
        <el-progress :percentage="detail.instance.progressPercent" :stroke-width="10" />
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane :label="`结构化进度项 (${detail.progressItems.length})`" name="items">
          <div class="section-title">
            <div>
              <h3>结构化进度项</h3>
              <p>按项目模板定义的动态进度项逐项维护。</p>
            </div>
          </div>
          <el-table :data="detail.progressItems" stripe max-height="480">
            <el-table-column prop="itemLabel" label="进度项" min-width="150" sortable />
            <el-table-column label="类型" min-width="100" sortable :sort-method="compareType">
              <template #default="{ row }">
                {{ formatItemType(row.type) }}
              </template>
            </el-table-column>
            <el-table-column label="当前值" min-width="180" sortable :sort-method="compareProgressValue">
              <template #default="{ row }">
                <ProgressValueDisplay :value="row.value" :input-mode="detail.instance.inputMode" />
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" min-width="70" sortable />
            <el-table-column label="备注" min-width="220">
              <template #default="{ row }">
                <div class="table-multiline">{{ row.value.remark || "-" }}</div>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openValueDialog(row)">更新进度</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="`推进记录 (${detail.logs.length})`" name="logs">
          <div class="section-title">
            <div>
              <h3>推进记录时间线</h3>
              <p>记录每一次推进内容、进度变化和里程碑。</p>
            </div>
            <el-button type="primary" @click="logDialogVisible = true">新增记录</el-button>
          </div>
          <el-table v-if="detail.logs.length" :data="detail.logs" stripe max-height="520">
            <el-table-column prop="logDate" label="日期" min-width="110" sortable />
            <el-table-column prop="itemLabel" label="关联进度项" min-width="120" sortable />
            <el-table-column label="推进内容" min-width="240">
              <template #default="{ row }">
                <div class="table-multiline">{{ row.content }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="progressDelta" label="变化" min-width="70" sortable>
              <template #default="{ row }">+{{ row.progressDelta }}%</template>
            </el-table-column>
            <el-table-column prop="progressAfter" label="当前进度" min-width="90" sortable>
              <template #default="{ row }">{{ row.progressAfter }}%</template>
            </el-table-column>
            <el-table-column prop="isMilestone" label="里程碑" min-width="90" sortable>
              <template #default="{ row }">
                <StatusTag :label="row.isMilestone ? '里程碑' : '普通记录'" />
              </template>
            </el-table-column>
          </el-table>
          <EmptyBlock
            v-else
            compact
            title="当前没有推进记录"
            description="新增第一条推进记录后，这里会形成完整时间线。"
          />
        </el-tab-pane>

        <el-tab-pane :label="`风险与阻塞 (${detail.risks.length})`" name="risks">
          <div class="section-title">
            <div>
              <h3>风险与阻塞</h3>
              <p>记录当前阻塞、影响说明和计划解决时间。</p>
            </div>
            <el-button type="primary" @click="openRiskDialog()">新增风险</el-button>
          </div>
          <el-table v-if="detail.risks.length" :data="detail.risks" stripe max-height="520">
            <el-table-column prop="title" label="风险标题" min-width="160" sortable />
            <el-table-column label="影响说明" min-width="220">
              <template #default="{ row }">
                <div class="table-multiline">{{ row.impactDesc || row.description || "-" }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="ownerName" label="责任人" min-width="90" sortable />
            <el-table-column prop="plannedResolveDate" label="计划解决" min-width="110" sortable />
            <el-table-column prop="status" label="状态" min-width="100" sortable>
              <template #default="{ row }">
                <StatusTag :label="row.status" />
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="120" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openRiskDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <EmptyBlock
            v-else
            compact
            title="当前没有风险项"
            description="项目有阻塞或关键依赖时，可以在这里补充风险。"
          />
        </el-tab-pane>
      </el-tabs>
    </section>

    <el-dialog v-model="valueDialogVisible" title="更新进度项" width="620px">
      <el-form :model="valueForm" label-width="110px">
        <el-form-item label="进度项">
          <el-input :model-value="editingItem?.itemLabel || ''" disabled />
        </el-form-item>
        <template v-if="editingItem?.type === 'status'">
          <el-form-item label="状态值">
            <el-select v-model="valueForm.status_value" style="width: 100%;">
              <el-option label="不支持" value="不支持" />
              <el-option label="未开始" value="未开始" />
              <el-option label="推进中" value="推进中" />
              <el-option label="就绪" value="就绪" />
              <el-option label="已支持" value="已支持" />
              <el-option label="已完成" value="已完成" />
              <el-option label="阻塞" value="阻塞" />
            </el-select>
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="当前值">
            <el-input-number v-model="valueForm.current_num" :min="0" />
          </el-form-item>
          <el-form-item label="目标值">
            <el-input-number v-model="valueForm.target_num" :min="0" />
          </el-form-item>
          <el-form-item label="不适用">
            <el-switch v-model="valueForm.is_na" />
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="valueForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="valueDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveValue">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="logDialogVisible" title="新增推进记录" width="620px">
      <el-form :model="logForm" label-width="110px">
        <el-form-item label="关联进度项">
          <el-select v-model="logForm.item_template_id" clearable style="width: 100%;">
            <el-option v-for="item in detail?.progressItems || []" :key="item.itemTemplateId" :label="item.itemLabel" :value="item.itemTemplateId" />
          </el-select>
        </el-form-item>
        <el-form-item label="记录日期">
          <el-date-picker v-model="logForm.log_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="推进内容">
          <el-input v-model="logForm.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="本次变化">
          <el-input-number v-model="logForm.progress_delta" :min="0" />
        </el-form-item>
        <el-form-item label="当前总进度">
          <el-input-number v-model="logForm.progress_after" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="里程碑">
          <el-switch v-model="logForm.is_milestone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="logForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="logDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateLog">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="riskDialogVisible" :title="editingRisk ? '编辑风险' : '新增风险'" width="620px">
      <el-form :model="riskForm" label-width="110px">
        <el-form-item label="风险标题">
          <el-input v-model="riskForm.title" />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="riskForm.level" style="width: 100%;">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任人">
          <el-input v-model="riskForm.owner_name" />
        </el-form-item>
        <el-form-item label="计划解决">
          <el-date-picker v-model="riskForm.planned_resolve_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-select v-model="riskForm.status" style="width: 100%;">
            <el-option label="待处理" value="待处理" />
            <el-option label="处理中" value="处理中" />
            <el-option label="持续关注" value="持续关注" />
            <el-option label="已解除" value="已解除" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险说明">
          <el-input v-model="riskForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="影响说明">
          <el-input v-model="riskForm.impact_desc" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="riskForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="riskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRisk">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import EmptyBlock from "../../components/EmptyBlock.vue";
import ProgressValueDisplay from "../../components/ProgressValueDisplay.vue";
import StatusTag from "../../components/StatusTag.vue";
import {
  createProgressLog,
  createProgressRisk,
  getProgressInstanceDetail,
  updateProgressItemValue,
  updateProgressRisk
} from "../../api/progress";
import type {
  ProgressInstanceDetail,
  ProgressItemDetail,
  ProgressRiskItem,
  ProgressRiskUpdatePayload,
  ProgressValueUpdatePayload
} from "../../types/models";

const route = useRoute();
const router = useRouter();

const activeTab = ref("items");
const detail = ref<ProgressInstanceDetail | null>(null);
const valueDialogVisible = ref(false);
const logDialogVisible = ref(false);
const riskDialogVisible = ref(false);
const editingItem = ref<ProgressItemDetail | null>(null);
const editingRisk = ref<ProgressRiskItem | null>(null);

const valueForm = reactive<ProgressValueUpdatePayload>({
  status_value: "",
  current_num: null,
  target_num: null,
  bool_value: null,
  text_value: "",
  is_na: false,
  remark: ""
});

const logForm = reactive({
  item_template_id: null as number | null,
  log_date: "",
  content: "",
  progress_delta: 0,
  progress_after: 0,
  is_milestone: false,
  remark: ""
});

const riskForm = reactive<ProgressRiskUpdatePayload>({
  title: "",
  description: "",
  impact_desc: "",
  level: "中",
  owner_name: "",
  planned_resolve_date: "",
  status: "待处理",
  remark: ""
});

const instanceId = Number(route.params.id);

async function loadDetail() {
  detail.value = await getProgressInstanceDetail(instanceId);
}

function formatItemType(type: string) {
  if (type === "status") return "状态型";
  if (type === "number_progress") return "数量型";
  if (type === "boolean") return "布尔型";
  if (type === "milestone") return "里程碑型";
  return type;
}

function compareType(a: { type: string }, b: { type: string }) {
  return formatItemType(a.type).localeCompare(formatItemType(b.type));
}

function compareProgressValue(a: { value: { calculatedPercent: number; statusValue: string } }, b: { value: { calculatedPercent: number; statusValue: string } }) {
  const valueA = a.value.calculatedPercent ?? 0;
  const valueB = b.value.calculatedPercent ?? 0;
  if (valueA !== valueB) {
    return valueA - valueB;
  }
  return (a.value.statusValue || "").localeCompare(b.value.statusValue || "");
}

function handleBack() {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  if (detail.value) {
    router.push(`/progress/matrix?projectId=${detail.value.instance.projectTemplateId}`);
    return;
  }
  router.push("/progress/overview");
}

function openValueDialog(item: ProgressItemDetail) {
  editingItem.value = item;
  valueForm.status_value = item.value.statusValue || "";
  valueForm.current_num = item.value.currentNum;
  valueForm.target_num = item.value.targetNum;
  valueForm.is_na = item.value.isNa;
  valueForm.remark = item.value.remark || "";
  valueDialogVisible.value = true;
}

async function handleSaveValue() {
  if (!editingItem.value) {
    return;
  }
  await updateProgressItemValue(instanceId, editingItem.value.itemTemplateId, valueForm);
  valueDialogVisible.value = false;
  ElMessage.success("进度项已更新");
  await loadDetail();
}

async function handleCreateLog() {
  await createProgressLog(instanceId, {
    item_template_id: logForm.item_template_id,
    log_date: `${logForm.log_date}T00:00:00`,
    content: logForm.content,
    progress_delta: logForm.progress_delta,
    progress_after: logForm.progress_after,
    is_milestone: logForm.is_milestone,
    remark: logForm.remark
  });
  logDialogVisible.value = false;
  ElMessage.success("推进记录已新增");
  logForm.item_template_id = null;
  logForm.log_date = "";
  logForm.content = "";
  logForm.progress_delta = 0;
  logForm.progress_after = 0;
  logForm.is_milestone = false;
  logForm.remark = "";
  await loadDetail();
}

function openRiskDialog(risk?: ProgressRiskItem) {
  editingRisk.value = risk || null;
  riskForm.title = risk?.title || "";
  riskForm.description = risk?.description || "";
  riskForm.impact_desc = risk?.impactDesc || "";
  riskForm.level = risk?.level || "中";
  riskForm.owner_name = risk?.ownerName || "";
  riskForm.planned_resolve_date = risk?.plannedResolveDate || "";
  riskForm.status = risk?.status || "待处理";
  riskForm.remark = risk?.remark || "";
  riskDialogVisible.value = true;
}

async function handleSaveRisk() {
  if (editingRisk.value) {
    await updateProgressRisk(editingRisk.value.id, riskForm);
    ElMessage.success("风险已更新");
  } else {
    await createProgressRisk(instanceId, riskForm);
    ElMessage.success("风险已新增");
  }
  riskDialogVisible.value = false;
  await loadDetail();
}

onMounted(async () => {
  await loadDetail();
});
</script>
