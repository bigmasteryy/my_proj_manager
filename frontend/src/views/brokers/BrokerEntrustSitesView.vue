<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">委托主站</p>
        <h2>维护各家券商的委托主站信息。</h2>
        <p>点击券商列表里的委托主站数量会直接跳到这里，并自动定位到对应券商。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedBrokerId" style="width: 260px;" filterable placeholder="选择券商" @change="handleBrokerChange">
          <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
        </el-select>
        <el-button type="primary" :disabled="!detail" @click="openEntrustSiteDialog()">新增委托主站</el-button>
      </div>
    </section>

    <section class="section-card" v-loading="loading">
      <template v-if="detail">
        <div class="section-title">
          <div>
            <h3>{{ detail.name }}</h3>
            <p>当前共 {{ detail.entrustSites.length }} 条委托主站记录。</p>
          </div>
        </div>

        <el-table v-if="detail.entrustSites.length" :data="detail.entrustSites" stripe>
          <el-table-column prop="name" label="主站名称" min-width="160" />
          <el-table-column prop="clientType" label="类型" min-width="90" />
          <el-table-column prop="softwareVersion" label="软件版本" min-width="120" />
          <el-table-column prop="updatedAt" label="更新时间" min-width="160" />
          <el-table-column prop="operatingSystem" label="Win/Linux" min-width="120" />
          <el-table-column label="是否信创" min-width="100">
            <template #default="{ row }">
              <StatusTag :label="row.isXinchuang ? '是' : '否'" />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="180">
            <template #default="{ row }">
              <div class="table-multiline">{{ row.remark || "-" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="120" fixed="right">
            <template #default="{ row }">
              <div class="action-row">
                <el-button link type="primary" @click="openEntrustSiteDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteEntrustSite(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <EmptyBlock
          v-else
          compact
          title="还没有委托主站信息"
          description="先新增一条主站记录，后续版本、更新时间、Windows/Linux、是否信创都可以在这里维护。"
        />
      </template>
      <EmptyBlock
        v-else-if="!loading"
        compact
        title="请选择一家具商"
        description="选择券商后就能在这里维护委托主站信息。"
      />
    </section>

    <el-dialog v-model="entrustSiteDialogVisible" :title="editingEntrustSiteId ? '编辑委托主站' : '新增委托主站'" width="760px">
      <el-form :model="entrustSiteForm" label-width="120px">
        <el-form-item label="主站名称">
          <el-input v-model="entrustSiteForm.name" />
        </el-form-item>
        <el-form-item label="客户端类型">
          <el-select v-model="entrustSiteForm.client_type" style="width: 100%;">
            <el-option label="PC" value="PC" />
            <el-option label="APP" value="APP" />
          </el-select>
        </el-form-item>
        <el-form-item label="软件版本">
          <el-input v-model="entrustSiteForm.software_version" />
        </el-form-item>
        <el-form-item label="更新时间">
          <el-date-picker v-model="entrustSiteForm.updated_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="Win/Linux">
          <el-select v-model="entrustSiteForm.operating_system" style="width: 100%;">
            <el-option label="Windows" value="Windows" />
            <el-option label="Linux" value="Linux" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否信创">
          <el-switch v-model="entrustSiteForm.is_xinchuang" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="entrustSiteForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="entrustSiteDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveEntrustSite">保存委托主站</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { createBrokerEntrustSite, deleteBrokerEntrustSite, getBrokerDetail, getBrokers, updateBrokerEntrustSite } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import StatusTag from "../../components/StatusTag.vue";
import type { BrokerDetail, BrokerEntrustSiteItem, BrokerEntrustSitePayload, BrokerSummary } from "../../types/models";

const route = useRoute();
const router = useRouter();

const brokers = ref<BrokerSummary[]>([]);
const detail = ref<BrokerDetail | null>(null);
const selectedBrokerId = ref<number | null>(null);
const loading = ref(false);
const submitting = ref(false);
const editingEntrustSiteId = ref<number | null>(null);
const entrustSiteDialogVisible = ref(false);

const entrustSiteForm = reactive<BrokerEntrustSitePayload>({
  name: "",
  client_type: "PC",
  software_version: "",
  updated_at: "",
  operating_system: "Windows",
  is_xinchuang: false,
  remark: ""
});

async function loadBrokers() {
  brokers.value = await getBrokers();
}

async function loadDetail(brokerId: number) {
  loading.value = true;
  try {
    detail.value = await getBrokerDetail(brokerId);
  } finally {
    loading.value = false;
  }
}

function resetEntrustSiteForm() {
  editingEntrustSiteId.value = null;
  entrustSiteForm.name = "";
  entrustSiteForm.client_type = "PC";
  entrustSiteForm.software_version = "";
  entrustSiteForm.updated_at = "";
  entrustSiteForm.operating_system = "Windows";
  entrustSiteForm.is_xinchuang = false;
  entrustSiteForm.remark = "";
}

function openEntrustSiteDialog(site?: BrokerEntrustSiteItem) {
  if (site) {
    editingEntrustSiteId.value = site.id;
    entrustSiteForm.name = site.name;
    entrustSiteForm.client_type = site.clientType;
    entrustSiteForm.software_version = site.softwareVersion;
    entrustSiteForm.updated_at = site.updatedAt ? site.updatedAt.replace(" ", "T") : "";
    entrustSiteForm.operating_system = site.operatingSystem;
    entrustSiteForm.is_xinchuang = site.isXinchuang;
    entrustSiteForm.remark = site.remark;
  } else {
    resetEntrustSiteForm();
  }
  entrustSiteDialogVisible.value = true;
}

async function handleSaveEntrustSite() {
  if (!selectedBrokerId.value) {
    return;
  }
  submitting.value = true;
  try {
    if (editingEntrustSiteId.value) {
      await updateBrokerEntrustSite(editingEntrustSiteId.value, entrustSiteForm);
      ElMessage.success("委托主站已更新");
    } else {
      await createBrokerEntrustSite(selectedBrokerId.value, entrustSiteForm);
      ElMessage.success("委托主站已新增");
    }
    entrustSiteDialogVisible.value = false;
    await loadDetail(selectedBrokerId.value);
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteEntrustSite(siteId: number) {
  await deleteBrokerEntrustSite(siteId);
  ElMessage.success("委托主站已删除");
  if (selectedBrokerId.value) {
    await loadDetail(selectedBrokerId.value);
  }
}

async function handleBrokerChange(brokerId: number) {
  await router.replace(`/brokers/entrust-sites?brokerId=${brokerId}`);
}

onMounted(async () => {
  await loadBrokers();
  const queryBrokerId = Number(route.query.brokerId || 0);
  selectedBrokerId.value = queryBrokerId || brokers.value[0]?.id || null;
  if (selectedBrokerId.value) {
    await loadDetail(selectedBrokerId.value);
  }
});

watch(
  () => route.query.brokerId,
  async (value) => {
    const brokerId = Number(value || 0);
    if (!brokerId) {
      return;
    }
    selectedBrokerId.value = brokerId;
    await loadDetail(brokerId);
  }
);
</script>
