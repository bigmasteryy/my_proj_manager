<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">券商台账</p>
        <h2>按券商查看项目、关键节点和风险概况。</h2>
        <p>这一页更偏客户视角，适合快速回答“这家券商现在有什么事”。</p>
      </div>
      <div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          <el-button @click="downloadBrokerCsv">导出 CSV</el-button>
          <el-button type="primary" @click="openCreateBrokerDialog">新增券商</el-button>
        </div>
      </div>
    </section>

    <section class="section-card">
      <div class="section-title">
        <div>
          <h3>券商台账</h3>
          <p>现在已经支持新增、编辑、删除券商。</p>
        </div>
      </div>
      <el-table v-if="brokers.length" :data="brokers" stripe>
        <el-table-column prop="name" label="券商名称" min-width="180" />
        <el-table-column prop="currentProjects" label="当前项目数" min-width="120" />
        <el-table-column prop="activeProjects" label="进行中" min-width="100" />
        <el-table-column prop="nextMilestone" label="最近关键节点" min-width="180" />
        <el-table-column prop="riskCount" label="风险数" min-width="100" />
        <el-table-column prop="overdueCount" label="逾期数" min-width="100" />
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px;">
              <el-button link type="primary" @click="openEditBrokerDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDeleteBroker(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyBlock
        v-else
        title="还没有券商台账"
        description="先新增一条券商记录，后续项目、风险和周报都会从这里展开。"
      >
        <div class="empty-inline-action">
          <el-button type="primary" @click="openCreateBrokerDialog">新增券商</el-button>
        </div>
      </EmptyBlock>
    </section>

    <el-dialog
      v-model="brokerDialogVisible"
      :title="editingBrokerId ? '编辑券商' : '新增券商'"
      width="620px"
    >
      <el-form ref="brokerFormRef" :model="brokerForm" :rules="brokerRules" label-width="110px">
        <el-form-item label="券商名称" prop="name">
          <el-input v-model="brokerForm.name" placeholder="填写券商全称" />
        </el-form-item>
        <el-form-item label="券商简称" prop="short_name">
          <el-input v-model="brokerForm.short_name" placeholder="填写简称" />
        </el-form-item>
        <el-form-item label="对接人">
          <el-input v-model="brokerForm.contact_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="brokerForm.contact_phone" placeholder="可选" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="brokerForm.status" style="width: 100%;">
            <el-option label="active" value="active" />
            <el-option label="inactive" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="brokerForm.note" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brokerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveBroker">保存券商</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from "element-plus";
import { createBroker, deleteBroker, getBrokers, updateBroker } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { BrokerCreatePayload, BrokerSummary } from "../../types/models";

const brokers = ref<BrokerSummary[]>([]);
const brokerDialogVisible = ref(false);
const submitting = ref(false);
const editingBrokerId = ref<number | null>(null);
const brokerFormRef = ref<FormInstance>();
const brokerForm = reactive<BrokerCreatePayload>({
  name: "",
  short_name: "",
  contact_name: "",
  contact_phone: "",
  status: "active",
  note: ""
});

const brokerRules: FormRules<BrokerCreatePayload> = {
  name: [{ required: true, message: "请输入券商名称", trigger: "blur" }],
  short_name: [{ required: true, message: "请输入券商简称", trigger: "blur" }],
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

function resetBrokerForm() {
  editingBrokerId.value = null;
  brokerForm.name = "";
  brokerForm.short_name = "";
  brokerForm.contact_name = "";
  brokerForm.contact_phone = "";
  brokerForm.status = "active";
  brokerForm.note = "";
}

function fillBrokerForm(broker: BrokerSummary) {
  brokerForm.name = broker.name;
  brokerForm.short_name = broker.shortName;
  brokerForm.contact_name = "";
  brokerForm.contact_phone = "";
  brokerForm.status = "active";
  brokerForm.note = "";
}

async function loadBrokers() {
  brokers.value = await getBrokers();
}

function openCreateBrokerDialog() {
  resetBrokerForm();
  brokerDialogVisible.value = true;
}

function openEditBrokerDialog(broker: BrokerSummary) {
  editingBrokerId.value = broker.id;
  fillBrokerForm(broker);
  brokerDialogVisible.value = true;
}

async function handleSaveBroker() {
  const valid = await brokerFormRef.value?.validate().catch(() => false);
  if (!valid) {
    return;
  }

  submitting.value = true;
  try {
    if (editingBrokerId.value) {
      await updateBroker(editingBrokerId.value, brokerForm);
      ElMessage.success("券商已更新");
    } else {
      await createBroker(brokerForm);
      ElMessage.success("券商已新增");
    }

    brokerDialogVisible.value = false;
    resetBrokerForm();
    await loadBrokers();
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteBroker(broker: BrokerSummary) {
  await ElMessageBox.confirm(
    `确认删除券商“${broker.name}”？如果该券商下有项目，将一并删除。`,
    "删除确认",
    {
      type: "warning",
      confirmButtonText: "确认删除",
      cancelButtonText: "取消"
    }
  );

  await deleteBroker(broker.id);
  ElMessage.success("券商已删除");
  await loadBrokers();
}

function downloadBrokerCsv() {
  const header = ["券商名称", "当前项目数", "进行中", "最近关键节点", "风险数", "逾期数"];
  const rows = brokers.value.map((item) => [
    item.name,
    item.currentProjects,
    item.activeProjects,
    item.nextMilestone,
    item.riskCount,
    item.overdueCount
  ]);
  const csv = [header, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "券商台账.csv";
  link.click();
  URL.revokeObjectURL(url);
  ElMessage.success("券商台账 CSV 已导出");
}

onMounted(async () => {
  await loadBrokers();
});
</script>
