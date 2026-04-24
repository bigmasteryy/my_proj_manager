<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">模板中心</p>
        <h2>把成熟项目沉淀成模板，后续快速复制。</h2>
        <p>这里建议以“项目模板”为核心，而不是券商模板。</p>
      </div>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button @click="openGenerateDialog" :disabled="!selectedTemplate">基于模板生成项目</el-button>
        <el-button @click="openEditDialog" :disabled="!selectedTemplate">编辑模板</el-button>
        <el-button type="danger" plain @click="handleDeleteTemplate" :disabled="!selectedTemplate">删除模板</el-button>
        <el-button type="primary" @click="openCreateDialog">新建模板</el-button>
      </div>
    </section>

    <div class="split-grid">
      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>模板清单</h3>
            <p>支持查看详情、创建模板、基于模板生成项目。</p>
          </div>
        </div>
        <el-table v-if="templates.length" :data="templates" stripe highlight-current-row @current-change="handleTemplateSelect">
          <el-table-column prop="name" label="模板名称" min-width="180" />
          <el-table-column prop="templateType" label="类型" min-width="120" />
          <el-table-column prop="scene" label="适用场景" min-width="220" />
          <el-table-column prop="taskCount" label="标准任务数" min-width="120" />
          <el-table-column prop="riskCount" label="默认风险项" min-width="120" />
          <el-table-column prop="recentUseCount" label="最近使用次数" min-width="140" />
          <el-table-column label="操作" min-width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="selectTemplate(row.id)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <EmptyBlock
          v-else
          title="还没有项目模板"
          description="可以从空白新建模板，或先在项目详情里把成熟项目保存为模板。"
        >
          <div class="empty-inline-action">
            <el-button type="primary" @click="openCreateDialog">新建模板</el-button>
          </div>
        </EmptyBlock>
      </section>

      <section class="section-card">
        <div class="section-title">
          <div>
            <h3>模板详情</h3>
            <p v-if="selectedTemplate">{{ selectedTemplate.scene }}</p>
            <p v-else>请选择一个模板查看详情。</p>
          </div>
        </div>

        <template v-if="selectedTemplate">
          <div class="stack">
            <div>
              <h4 style="margin: 0 0 10px;">标准任务</h4>
              <ul class="bullet-panel">
                <li v-for="task in selectedTemplate.tasks" :key="`${selectedTemplate.id}-${task.name}`">
                  {{ task.name }} / {{ task.plannedContent }} / 默认负责人：{{ task.defaultOwnerName || "未指定" }} / 偏移 {{ task.offsetDays }} 天
                </li>
              </ul>
            </div>
            <div>
              <h4 style="margin: 0 0 10px;">默认风险项</h4>
              <ul class="bullet-panel">
                <li v-for="risk in selectedTemplate.risks" :key="`${selectedTemplate.id}-${risk.title}`">
                  {{ risk.title }} / {{ risk.level }} / 偏移 {{ risk.offsetDays }} 天
                </li>
              </ul>
            </div>
          </div>
        </template>
        <EmptyBlock
          v-else
          compact
          title="请选择一个模板"
          description="选中左侧模板后，这里会显示标准任务和默认风险项。"
        />
      </section>
    </div>

    <el-dialog v-model="templateDialogVisible" :title="editingTemplateId ? '编辑模板' : '新建模板'" width="760px">
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="110px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" />
        </el-form-item>
        <el-form-item label="模板类型" prop="template_type">
          <el-input v-model="templateForm.template_type" />
        </el-form-item>
        <el-form-item label="适用场景" prop="scene">
          <el-input v-model="templateForm.scene" />
        </el-form-item>

        <el-divider content-position="left">标准任务</el-divider>
        <div v-for="(task, index) in templateForm.tasks" :key="index" class="section-card" style="margin-bottom: 12px; padding: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <strong>任务 {{ index + 1 }}</strong>
            <el-button link type="danger" @click="removeTemplateTask(index)">删除</el-button>
          </div>
          <el-input v-model="task.name" placeholder="任务名称" style="margin-bottom: 10px;" />
          <el-input v-model="task.planned_content" placeholder="计划内容" style="margin-bottom: 10px;" />
          <div style="display: grid; grid-template-columns: 1fr 120px; gap: 10px;">
            <el-input v-model="task.default_owner_name" placeholder="默认负责人" />
            <el-input-number v-model="task.offset_days" :step="1" />
          </div>
        </div>
        <el-button @click="addTemplateTask">新增任务项</el-button>

        <el-divider content-position="left">默认风险项</el-divider>
        <div v-for="(risk, index) in templateForm.risks" :key="index" class="section-card" style="margin-bottom: 12px; padding: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <strong>风险 {{ index + 1 }}</strong>
            <el-button link type="danger" @click="removeTemplateRisk(index)">删除</el-button>
          </div>
          <el-input v-model="risk.title" placeholder="风险标题" style="margin-bottom: 10px;" />
          <div style="display: grid; grid-template-columns: 1fr 120px; gap: 10px; margin-bottom: 10px;">
            <el-select v-model="risk.level">
              <el-option label="高风险" value="高风险" />
              <el-option label="中风险" value="中风险" />
              <el-option label="低风险" value="低风险" />
            </el-select>
            <el-input-number v-model="risk.offset_days" :step="1" />
          </div>
          <el-switch v-model="risk.affects_milestone" style="margin-bottom: 10px;" />
          <el-input v-model="risk.action_plan" type="textarea" :rows="3" placeholder="应对措施" />
        </div>
        <el-button @click="addTemplateRisk">新增风险项</el-button>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="templateSubmitting" @click="handleCreateTemplate">保存模板</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="generateDialogVisible" title="基于模板生成项目" width="620px">
      <el-form ref="generateFormRef" :model="generateForm" :rules="generateRules" label-width="110px">
        <el-form-item label="所属券商" prop="broker_id">
          <el-select v-model="generateForm.broker_id" style="width: 100%;">
            <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="generateForm.name" />
        </el-form-item>
        <el-form-item label="负责人" prop="owner_name">
          <el-input v-model="generateForm.owner_name" />
        </el-form-item>
        <el-form-item label="关键日期" prop="planned_date">
          <el-date-picker v-model="generateForm.planned_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="generateForm.status" style="width: 100%;">
            <el-option label="准备中" value="准备中" />
            <el-option label="执行中" value="执行中" />
            <el-option label="规划中" value="规划中" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="generateForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generateSubmitting" @click="handleGenerateProject">生成项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { useRouter } from "vue-router";
import { getBrokers } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import {
  createTemplate,
  deleteTemplate,
  generateProjectFromTemplate,
  getTemplateDetail,
  getTemplates,
  updateTemplate
} from "../../api/templates";
import type {
  BrokerSummary,
  TemplateCreatePayload,
  TemplateDetail,
  TemplateGenerateProjectPayload,
  TemplateSummary,
  TemplateUpdatePayload
} from "../../types/models";

const router = useRouter();
const templates = ref<TemplateSummary[]>([]);
const brokers = ref<BrokerSummary[]>([]);
const selectedTemplate = ref<TemplateDetail | null>(null);
const templateDialogVisible = ref(false);
const generateDialogVisible = ref(false);
const templateSubmitting = ref(false);
const generateSubmitting = ref(false);
const editingTemplateId = ref<number | null>(null);
const templateFormRef = ref<FormInstance>();
const generateFormRef = ref<FormInstance>();

const templateForm = reactive<TemplateUpdatePayload>({
  name: "",
  template_type: "",
  scene: "",
  tasks: [
    { name: "", planned_content: "", default_owner_name: "", offset_days: 0 }
  ],
  risks: [
    { title: "", level: "高风险", affects_milestone: false, action_plan: "", offset_days: 0 }
  ]
});

const generateForm = reactive<TemplateGenerateProjectPayload>({
  broker_id: 0,
  name: "",
  owner_name: "",
  planned_date: "",
  status: "准备中",
  description: ""
});

const templateRules: FormRules<TemplateCreatePayload> = {
  name: [{ required: true, message: "请输入模板名称", trigger: "blur" }],
  template_type: [{ required: true, message: "请输入模板类型", trigger: "blur" }],
  scene: [{ required: true, message: "请输入适用场景", trigger: "blur" }]
};

const generateRules: FormRules<TemplateGenerateProjectPayload> = {
  broker_id: [{ required: true, message: "请选择券商", trigger: "change" }],
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
  owner_name: [{ required: true, message: "请输入负责人", trigger: "blur" }],
  planned_date: [{ required: true, message: "请选择关键日期", trigger: "change" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

async function loadTemplates() {
  templates.value = await getTemplates();
  if (!selectedTemplate.value && templates.value.length > 0) {
    await selectTemplate(templates.value[0].id);
  }
}

async function loadBrokers() {
  brokers.value = await getBrokers();
  if (!generateForm.broker_id && brokers.value.length > 0) {
    generateForm.broker_id = brokers.value[0].id;
  }
}

async function selectTemplate(templateId: number) {
  selectedTemplate.value = await getTemplateDetail(templateId);
}

function handleTemplateSelect(row: TemplateSummary | undefined) {
  if (row) {
    void selectTemplate(row.id);
  }
}

function resetTemplateForm() {
  editingTemplateId.value = null;
  templateForm.name = "";
  templateForm.template_type = "";
  templateForm.scene = "";
  templateForm.tasks = [{ name: "", planned_content: "", default_owner_name: "", offset_days: 0 }];
  templateForm.risks = [{ title: "", level: "高风险", affects_milestone: false, action_plan: "", offset_days: 0 }];
}

function resetGenerateForm() {
  generateForm.broker_id = brokers.value[0]?.id ?? 0;
  generateForm.name = selectedTemplate.value ? `${selectedTemplate.value.name}生成项目` : "";
  generateForm.owner_name = "";
  generateForm.planned_date = "";
  generateForm.status = "准备中";
  generateForm.description = "";
}

function openCreateDialog() {
  resetTemplateForm();
  templateDialogVisible.value = true;
}

function openEditDialog() {
  if (!selectedTemplate.value) {
    ElMessage.warning("请先选择模板");
    return;
  }

  editingTemplateId.value = selectedTemplate.value.id;
  templateForm.name = selectedTemplate.value.name;
  templateForm.template_type = selectedTemplate.value.templateType;
  templateForm.scene = selectedTemplate.value.scene;
  templateForm.tasks = selectedTemplate.value.tasks.map((task) => ({
    name: task.name,
    planned_content: task.plannedContent,
    default_owner_name: task.defaultOwnerName,
    offset_days: task.offsetDays
  }));
  templateForm.risks = selectedTemplate.value.risks.map((risk) => ({
    title: risk.title,
    level: risk.level,
    affects_milestone: risk.affectsMilestone,
    action_plan: risk.actionPlan,
    offset_days: risk.offsetDays
  }));
  templateDialogVisible.value = true;
}

function openGenerateDialog() {
  if (!selectedTemplate.value) {
    ElMessage.warning("请先选择模板");
    return;
  }

  resetGenerateForm();
  generateDialogVisible.value = true;
}

function addTemplateTask() {
  templateForm.tasks.push({ name: "", planned_content: "", default_owner_name: "", offset_days: 0 });
}

function removeTemplateTask(index: number) {
  if (templateForm.tasks.length === 1) {
    return;
  }
  templateForm.tasks.splice(index, 1);
}

function addTemplateRisk() {
  templateForm.risks.push({ title: "", level: "高风险", affects_milestone: false, action_plan: "", offset_days: 0 });
}

function removeTemplateRisk(index: number) {
  if (templateForm.risks.length === 1) {
    return;
  }
  templateForm.risks.splice(index, 1);
}

async function handleCreateTemplate() {
  const valid = await templateFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  templateSubmitting.value = true;
  try {
    const created = editingTemplateId.value
      ? await updateTemplate(editingTemplateId.value, templateForm)
      : await createTemplate(templateForm);
    templateDialogVisible.value = false;
    await loadTemplates();
    await selectTemplate(created.id);
    ElMessage.success(editingTemplateId.value ? "模板已更新" : "模板已创建");
  } finally {
    templateSubmitting.value = false;
  }
}

async function handleDeleteTemplate() {
  if (!selectedTemplate.value) {
    ElMessage.warning("请先选择模板");
    return;
  }

  await ElMessageBox.confirm(`确认删除模板“${selectedTemplate.value.name}”？`, "删除确认", {
    type: "warning",
    confirmButtonText: "确认删除",
    cancelButtonText: "取消"
  });
  await deleteTemplate(selectedTemplate.value.id);
  ElMessage.success("模板已删除");
  selectedTemplate.value = null;
  await loadTemplates();
}

async function handleGenerateProject() {
  const valid = await generateFormRef.value?.validate().catch(() => false);
  if (!valid || !selectedTemplate.value) {
    return;
  }

  generateSubmitting.value = true;
  try {
    const created = await generateProjectFromTemplate(selectedTemplate.value.id, generateForm);
    generateDialogVisible.value = false;
    await loadTemplates();
    ElMessage.success("已基于模板生成项目");
    router.push(`/projects/${created.id}`);
  } finally {
    generateSubmitting.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadTemplates(), loadBrokers()]);
});
</script>
