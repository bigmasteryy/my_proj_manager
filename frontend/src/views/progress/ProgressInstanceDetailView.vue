<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">券商项目详情</p>
        <h2>{{ detail?.instance.projectName || "项目详情" }}<template v-if="detail"> / {{ detail.instance.brokerName }}</template></h2>
        <p class="compact-muted">{{ detail?.instance.remark || "查看某个项目在某家券商上的详细推进过程、结构化进度项、客户端放开步骤和风险记录。" }}</p>
      </div>
      <div class="hero-actions">
        <StatusTag v-if="detail" :label="detail.instance.status" />
        <el-button type="primary" @click="handleBack">返回</el-button>
      </div>
    </section>

    <section v-if="detail" class="compact-grid compact-grid-4">
      <article class="compact-card">
        <small>总进度</small>
        <strong>{{ detail.instance.progressPercent }}%</strong>
      </article>
      <article class="compact-card">
        <small>最新更新</small>
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

    <section class="section-card" v-loading="detailLoading">
      <template v-if="detail">
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
                <p>在这里维护结构化进度值，也在这里统一做字段的新增、编辑和删除。</p>
              </div>
              <el-button type="primary" @click="openItemTemplateDialog()">新增</el-button>
            </div>
            <el-table :data="detail.progressItems" stripe max-height="480">
              <el-table-column prop="itemLabel" label="进度项" min-width="160" sortable />
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
              <el-table-column label="操作" min-width="180" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openValueDialog(row)">更新进度</el-button>
                  <el-button link @click="openItemTemplateDialog(row)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteItemTemplate(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane v-if="detail.stage2" :label="`客户端放开 (${detail.stage2.completedCount}/${detail.stage2.totalCount})`" name="stage2">
            <div class="section-title">
              <div>
                <h3>客户端放开</h3>
                <p>统一按步骤清单维护，不再区分前置确认等分组，也不展示依赖关系。</p>
              </div>
              <el-button type="primary" @click="openStage2StepDialog()">新增步骤</el-button>
            </div>

            <section class="compact-grid compact-grid-4" style="margin-bottom: 16px;">
              <article class="compact-card">
                <small>阶段状态</small>
                <strong>{{ detail.stage2.status }}</strong>
              </article>
              <article class="compact-card">
                <small>已完成步骤</small>
                <strong>{{ detail.stage2.completedCount }}/{{ detail.stage2.totalCount }}</strong>
              </article>
              <article class="compact-card">
                <small>当前步骤</small>
                <strong>{{ detail.stage2.currentStepNo || "-" }}</strong>
              </article>
              <article class="compact-card">
                <small>阻塞步骤</small>
                <strong>{{ detail.stage2.blockedCount }}</strong>
              </article>
            </section>

            <el-table :data="stage2Steps" stripe max-height="520">
              <el-table-column prop="stepNoDisplay" label="步骤" min-width="90" />
              <el-table-column prop="stepName" label="步骤名称" min-width="260" />
              <el-table-column label="负责人" min-width="160">
                <template #default="{ row }">
                  <div class="table-multiline">{{ row.ownerActual || row.ownersDefault || "-" }}</div>
                </template>
              </el-table-column>
              <el-table-column label="状态" min-width="120">
                <template #default="{ row }">
                  <StatusTag :label="row.effectiveStatus || row.status" />
                </template>
              </el-table-column>
              <el-table-column label="备注" min-width="220">
                <template #default="{ row }">
                  <div class="table-multiline">{{ row.remark || row.remarkTemplate || "-" }}</div>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="170" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openStage2StepDialog(row)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteStage2Step(row)">删除</el-button>
                  <el-button link @click="handleMoveStage2Step(row, 'up')">↑</el-button>
                  <el-button link @click="handleMoveStage2Step(row, 'down')">↓</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane :label="`推进记录 (${detail.logs.length})`" name="logs">
            <div class="section-title">
              <div>
                <h3>推进记录时间线</h3>
                <p>记录每一次推进内容、进度变化、备注和里程碑。</p>
              </div>
              <el-button type="primary" @click="openLogDialog()">新增记录</el-button>
            </div>
            <el-table v-if="detail.logs.length" :data="detail.logs" stripe max-height="520">
              <el-table-column prop="logDate" label="日期" min-width="110" sortable />
              <el-table-column prop="itemLabel" label="关联进度项" min-width="130" sortable />
              <el-table-column label="推进内容" min-width="260">
                <template #default="{ row }">
                  <div class="table-multiline">{{ row.content }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="progressDelta" label="变化" min-width="80" sortable>
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
              <el-table-column label="备注" min-width="220">
                <template #default="{ row }">
                  <div class="table-multiline">{{ row.remark || "-" }}</div>
                </template>
              </el-table-column>
              <el-table-column label="操作" min-width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openLogDialog(row)">编辑</el-button>
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
      </template>

      <EmptyBlock
        v-else-if="!detailLoading"
        compact
        title="没有加载到项目详情"
        description="请从推进矩阵重新进入这条记录。"
      />
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

    <el-dialog v-model="itemTemplateDialogVisible" :title="editingItemTemplate ? '编辑结构化进度项' : '新增结构化进度项'" width="720px">
      <el-form :model="itemTemplateForm" label-width="120px">
        <el-form-item label="名称" required>
          <el-input v-model="itemTemplateForm.item_label" placeholder="例如：主站数量" />
        </el-form-item>
        <el-form-item label="标识">
          <el-input v-model="itemTemplateForm.item_key" :disabled="Boolean(editingItemTemplate)" placeholder="可不填，系统会自动生成" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="itemTemplateForm.item_type" style="width: 100%;" :disabled="Boolean(editingItemTemplate)">
            <el-option label="状态型" value="status" />
            <el-option label="数量型" value="number_progress" />
            <el-option label="布尔型" value="boolean" />
            <el-option label="文本型" value="text" />
          </el-select>
        </el-form-item>
        <el-form-item label="分组名称">
          <el-input v-model="itemTemplateForm.group_label" placeholder="可选，例如：主站升级" />
        </el-form-item>
        <el-form-item label="分组标识">
          <el-input v-model="itemTemplateForm.group_key" placeholder="可不填，系统会自动生成" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="itemTemplateForm.weight" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="允许不适用">
          <el-switch v-model="itemTemplateForm.allow_na" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="itemTemplateForm.sort_no" :min="1" />
        </el-form-item>
        <el-form-item label="取值规则">
          <el-input v-model="itemTemplateForm.value_rule" placeholder="例如：未开始/进行中/已完成 或 current/target" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="itemTemplateForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemTemplateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemTemplateSubmitting" @click="handleSaveItemTemplate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="logDialogVisible" :title="editingLog ? '编辑推进记录' : '新增推进记录'" width="620px">
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

    <el-dialog v-model="stage2StepDialogVisible" :title="editingStage2Step ? '编辑步骤' : '新增步骤'" width="680px">
      <el-form :model="stage2StepForm" label-width="110px">
        <el-form-item label="步骤名称">
          <el-input v-model="stage2StepForm.step_name" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="stage2StepForm.owner_actual" />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-select v-model="stage2StepForm.status" style="width: 100%;">
            <el-option label="未开始" value="未开始" />
            <el-option label="可开始" value="可开始" />
            <el-option label="进行中" value="进行中" />
            <el-option label="阻塞" value="阻塞" />
            <el-option label="已完成" value="已完成" />
            <el-option label="不适用" value="不适用" />
            <el-option label="已跳过" value="已跳过" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker v-model="stage2StepForm.started_at" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="完成时间">
          <el-date-picker v-model="stage2StepForm.finished_at" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="stage2StepForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stage2StepDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="stage2StepSubmitting" @click="handleSaveStage2Step">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";

import EmptyBlock from "../../components/EmptyBlock.vue";
import ProgressValueDisplay from "../../components/ProgressValueDisplay.vue";
import StatusTag from "../../components/StatusTag.vue";
import {
  createProgressLog,
  createProgressProjectItem,
  createProgressRisk,
  createProgressStage2Step,
  deleteProgressProjectItem,
  deleteProgressStage2Step,
  getProgressInstanceDetail,
  moveProgressStage2Step,
  updateProgressItemValue,
  updateProgressLog,
  updateProgressProjectItem,
  updateProgressRisk,
  updateProgressStage2Step
} from "../../api/progress";
import type {
  ProgressInstanceDetail,
  ProgressItemDetail,
  ProgressItemTemplateCreatePayload,
  ProgressLogItem,
  ProgressRiskItem,
  ProgressRiskUpdatePayload,
  ProgressStage2StepCreatePayload,
  ProgressStage2StepItem,
  ProgressStage2StepUpdatePayload,
  ProgressValueUpdatePayload
} from "../../types/models";

const route = useRoute();
const router = useRouter();

const activeTab = ref("items");
const detail = ref<ProgressInstanceDetail | null>(null);
const detailLoading = ref(false);
const valueDialogVisible = ref(false);
const itemTemplateDialogVisible = ref(false);
const logDialogVisible = ref(false);
const riskDialogVisible = ref(false);
const stage2StepDialogVisible = ref(false);

const editingItem = ref<ProgressItemDetail | null>(null);
const editingItemTemplate = ref<ProgressItemDetail | null>(null);
const editingLog = ref<ProgressLogItem | null>(null);
const editingRisk = ref<ProgressRiskItem | null>(null);
const editingStage2Step = ref<ProgressStage2StepItem | null>(null);

const itemTemplateSubmitting = ref(false);
const stage2StepSubmitting = ref(false);

const valueForm = reactive<ProgressValueUpdatePayload>({
  status_value: "",
  current_num: null,
  target_num: null,
  bool_value: null,
  text_value: "",
  is_na: false,
  remark: ""
});

const itemTemplateForm = reactive<ProgressItemTemplateCreatePayload>({
  item_key: "",
  item_label: "",
  group_key: "",
  group_label: "",
  item_type: "status",
  weight: 10,
  allow_na: false,
  sort_no: null,
  value_rule: "",
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

const stage2StepForm = reactive<ProgressStage2StepCreatePayload & ProgressStage2StepUpdatePayload>({
  step_no_display: "",
  step_name: "",
  owner_actual: "",
  status: "未开始",
  remark: "",
  blocker_reason: "",
  started_at: "",
  finished_at: ""
});

const instanceId = computed(() => Number(route.params.id || 0));
const stage2Steps = computed(() => detail.value?.stage2Groups.flatMap((group) => group.steps) || []);

async function loadDetail() {
  if (!instanceId.value) {
    detail.value = null;
    return;
  }
  detailLoading.value = true;
  try {
    detail.value = await getProgressInstanceDetail(instanceId.value);
  } finally {
    detailLoading.value = false;
  }
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

function compareStage2StatusInDetail(a: { effectiveStatus: string; status: string }, b: { effectiveStatus: string; status: string }) {
  return (a.effectiveStatus || a.status || "").localeCompare(b.effectiveStatus || b.status || "");
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

function openItemTemplateDialog(item?: ProgressItemDetail) {
  editingItemTemplate.value = item || null;
  itemTemplateForm.item_key = item?.itemKey || "";
  itemTemplateForm.item_label = item?.itemLabel || "";
  itemTemplateForm.group_key = item?.groupKey || "";
  itemTemplateForm.group_label = item?.groupLabel || "";
  itemTemplateForm.item_type = item?.type || "status";
  itemTemplateForm.weight = item?.weight || 10;
  itemTemplateForm.allow_na = item?.allowNa || false;
  itemTemplateForm.sort_no = item ? null : (detail.value?.progressItems.length || 0) + 1;
  itemTemplateForm.value_rule = "";
  itemTemplateForm.remark = item?.value.remark || "";
  itemTemplateDialogVisible.value = true;
}

function openStage2StepDialog(step?: ProgressStage2StepItem) {
  editingStage2Step.value = step || null;
  stage2StepForm.step_no_display = step?.stepNoDisplay || String((stage2Steps.value.length || 0) + 1);
  stage2StepForm.step_name = step?.stepName || "";
  stage2StepForm.owner_actual = step?.ownerActual || step?.ownersDefault || "";
  stage2StepForm.status = step?.status || "未开始";
  stage2StepForm.remark = step?.remark || "";
  stage2StepForm.blocker_reason = step?.blockerReason || "";
  stage2StepForm.started_at = step?.startedAt || "";
  stage2StepForm.finished_at = step?.finishedAt || "";
  stage2StepDialogVisible.value = true;
}

async function handleSaveValue() {
  if (!editingItem.value) {
    return;
  }
  await updateProgressItemValue(instanceId.value, editingItem.value.itemTemplateId, valueForm);
  valueDialogVisible.value = false;
  ElMessage.success("进度项已更新");
  await loadDetail();
}

async function handleSaveItemTemplate() {
  if (!detail.value) {
    return;
  }
  if (!itemTemplateForm.item_label.trim()) {
    ElMessage.warning("请先填写名称");
    return;
  }
  itemTemplateSubmitting.value = true;
  try {
    const payload = {
      item_key: itemTemplateForm.item_key?.trim() || undefined,
      item_label: itemTemplateForm.item_label.trim(),
      group_key: itemTemplateForm.group_key?.trim() || undefined,
      group_label: itemTemplateForm.group_label?.trim() || undefined,
      item_type: itemTemplateForm.item_type,
      weight: itemTemplateForm.weight,
      allow_na: itemTemplateForm.allow_na,
      sort_no: itemTemplateForm.sort_no,
      value_rule: itemTemplateForm.value_rule?.trim() || undefined,
      remark: itemTemplateForm.remark?.trim() || undefined
    };
    if (editingItemTemplate.value) {
      await updateProgressProjectItem(detail.value.instance.projectTemplateId, editingItemTemplate.value.itemTemplateId, payload);
      ElMessage.success("结构化进度项已更新");
    } else {
      await createProgressProjectItem(detail.value.instance.projectTemplateId, payload);
      ElMessage.success("结构化进度项已新增");
    }
    itemTemplateDialogVisible.value = false;
    await loadDetail();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "保存结构化进度项失败");
  } finally {
    itemTemplateSubmitting.value = false;
  }
}

async function handleDeleteItemTemplate(item: ProgressItemDetail) {
  if (!detail.value) {
    return;
  }
  await ElMessageBox.confirm(`确认删除“${item.itemLabel}”吗？该结构化进度项在当前项目下所有券商的数据都会一起删除。`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  try {
    await deleteProgressProjectItem(detail.value.instance.projectTemplateId, item.itemTemplateId);
    ElMessage.success("结构化进度项已删除");
    await loadDetail();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "删除结构化进度项失败");
  }
}

async function handleCreateLog() {
  const payload = {
    item_template_id: logForm.item_template_id,
    log_date: `${logForm.log_date}T00:00:00`,
    content: logForm.content,
    progress_delta: logForm.progress_delta,
    progress_after: logForm.progress_after,
    is_milestone: logForm.is_milestone,
    remark: logForm.remark
  };
  if (editingLog.value) {
    await updateProgressLog(editingLog.value.id, payload);
    ElMessage.success("推进记录已更新");
  } else {
    await createProgressLog(instanceId.value, payload);
    ElMessage.success("推进记录已新增");
  }
  logDialogVisible.value = false;
  editingLog.value = null;
  logForm.item_template_id = null;
  logForm.log_date = "";
  logForm.content = "";
  logForm.progress_delta = 0;
  logForm.progress_after = 0;
  logForm.is_milestone = false;
  logForm.remark = "";
  await loadDetail();
}

function openLogDialog(log?: ProgressLogItem) {
  editingLog.value = log || null;
  logForm.item_template_id = log?.itemTemplateId ?? null;
  logForm.log_date = log?.logDate || "";
  logForm.content = log?.content || "";
  logForm.progress_delta = log?.progressDelta || 0;
  logForm.progress_after = log?.progressAfter || 0;
  logForm.is_milestone = log?.isMilestone || false;
  logForm.remark = log?.remark || "";
  logDialogVisible.value = true;
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
    await createProgressRisk(instanceId.value, riskForm);
    ElMessage.success("风险已新增");
  }
  riskDialogVisible.value = false;
  await loadDetail();
}

async function handleSaveStage2Step() {
  if (!stage2StepForm.step_name?.trim()) {
    ElMessage.warning("请先填写步骤名称");
    return;
  }
  stage2StepSubmitting.value = true;
  try {
    const payload = {
      step_no_display: stage2StepForm.step_no_display.trim(),
      step_name: stage2StepForm.step_name.trim(),
      owner_actual: stage2StepForm.owner_actual,
      status: stage2StepForm.status,
      remark: stage2StepForm.remark,
      blocker_reason: stage2StepForm.blocker_reason,
      started_at: stage2StepForm.started_at ? `${stage2StepForm.started_at}T00:00:00` : null,
      finished_at: stage2StepForm.finished_at ? `${stage2StepForm.finished_at}T00:00:00` : null
    };
    if (editingStage2Step.value) {
      await updateProgressStage2Step(instanceId.value, editingStage2Step.value.stepInstanceId, payload);
      ElMessage.success("客户端放开步骤已更新");
    } else {
      await createProgressStage2Step(instanceId.value, payload);
      ElMessage.success("客户端放开步骤已新增");
    }
    stage2StepDialogVisible.value = false;
    await loadDetail();
  } finally {
    stage2StepSubmitting.value = false;
  }
}

async function handleMoveStage2Step(step: ProgressStage2StepItem, direction: "up" | "down") {
  try {
    const index = stage2Steps.value.findIndex((item) => item.stepInstanceId === step.stepInstanceId);
    if ((direction === "up" && index <= 0) || (direction === "down" && index === stage2Steps.value.length - 1)) {
      return;
    }
    await moveProgressStage2Step(instanceId.value, step.stepInstanceId, { direction });
    await loadDetail();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "调整步骤顺序失败");
  }
}

async function handleDeleteStage2Step(step: ProgressStage2StepItem) {
  await ElMessageBox.confirm(`确认删除步骤“${step.stepNoDisplay} ${step.stepName}”吗？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  try {
    await deleteProgressStage2Step(instanceId.value, step.stepInstanceId);
    ElMessage.success("客户端放开步骤已删除");
    await loadDetail();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || "删除步骤失败");
  }
}

watch(
  () => instanceId.value,
  async () => {
    activeTab.value = "items";
    await loadDetail();
  },
  { immediate: true }
);
</script>
