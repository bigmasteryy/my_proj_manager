<template>
  <div class="page-shell">
    <section class="page-hero">
      <div>
        <p class="eyebrow">服务器</p>
        <h2>维护各家券商的服务器基础信息。</h2>
        <p>点击券商列表里的服务器数量会直接跳到这里，并自动定位到对应券商。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedBrokerId" style="width: 260px;" filterable placeholder="选择券商" @change="handleBrokerChange">
          <el-option v-for="broker in brokers" :key="broker.id" :label="broker.name" :value="broker.id" />
        </el-select>
        <el-button type="primary" :disabled="!detail" @click="openServerDialog()">新增服务器</el-button>
      </div>
    </section>

    <section class="section-card" v-loading="loading">
      <template v-if="detail">
        <div class="section-title">
          <div>
            <h3>{{ detail.name }}</h3>
            <p>当前共 {{ detail.servers.length }} 台服务器。</p>
          </div>
        </div>

        <el-table v-if="detail.servers.length" :data="detail.servers" stripe>
          <el-table-column prop="name" label="服务器名称" min-width="160" />
          <el-table-column prop="cpu" label="CPU" min-width="140" />
          <el-table-column prop="memory" label="内存" min-width="120" />
          <el-table-column prop="operatingSystem" label="操作系统" min-width="140" />
          <el-table-column prop="ipAddress" label="IP/地址" min-width="140" />
          <el-table-column label="备注" min-width="180">
            <template #default="{ row }">
              <div class="table-multiline">{{ row.remark || "-" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="120" fixed="right">
            <template #default="{ row }">
              <div class="action-row">
                <el-button link type="primary" @click="openServerDialog(row)">编辑</el-button>
                <el-button link type="danger" @click="handleDeleteServer(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <EmptyBlock
          v-else
          compact
          title="还没有服务器信息"
          description="先新增一台服务器，CPU、内存、操作系统和 IP 都可以在这里维护。"
        />
      </template>
      <EmptyBlock
        v-else-if="!loading"
        compact
        title="请选择一家具商"
        description="选择券商后就能在这里维护服务器信息。"
      />
    </section>

    <el-dialog v-model="serverDialogVisible" :title="editingServerId ? '编辑服务器' : '新增服务器'" width="680px">
      <el-form :model="serverForm" label-width="110px">
        <el-form-item label="服务器名称">
          <el-input v-model="serverForm.name" />
        </el-form-item>
        <el-form-item label="CPU">
          <el-input v-model="serverForm.cpu" />
        </el-form-item>
        <el-form-item label="内存">
          <el-input v-model="serverForm.memory" />
        </el-form-item>
        <el-form-item label="操作系统">
          <el-input v-model="serverForm.operating_system" />
        </el-form-item>
        <el-form-item label="IP/地址">
          <el-input v-model="serverForm.ip_address" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="serverForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serverDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveServer">保存服务器</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { createBrokerServer, deleteBrokerServer, getBrokerDetail, getBrokers, updateBrokerServer } from "../../api/brokers";
import EmptyBlock from "../../components/EmptyBlock.vue";
import type { BrokerDetail, BrokerServerItem, BrokerServerPayload, BrokerSummary } from "../../types/models";

const route = useRoute();
const router = useRouter();

const brokers = ref<BrokerSummary[]>([]);
const detail = ref<BrokerDetail | null>(null);
const selectedBrokerId = ref<number | null>(null);
const loading = ref(false);
const submitting = ref(false);
const editingServerId = ref<number | null>(null);
const serverDialogVisible = ref(false);

const serverForm = reactive<BrokerServerPayload>({
  name: "",
  cpu: "",
  memory: "",
  operating_system: "",
  ip_address: "",
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

function resetServerForm() {
  editingServerId.value = null;
  serverForm.name = "";
  serverForm.cpu = "";
  serverForm.memory = "";
  serverForm.operating_system = "";
  serverForm.ip_address = "";
  serverForm.remark = "";
}

function openServerDialog(server?: BrokerServerItem) {
  if (server) {
    editingServerId.value = server.id;
    serverForm.name = server.name;
    serverForm.cpu = server.cpu;
    serverForm.memory = server.memory;
    serverForm.operating_system = server.operatingSystem;
    serverForm.ip_address = server.ipAddress;
    serverForm.remark = server.remark;
  } else {
    resetServerForm();
  }
  serverDialogVisible.value = true;
}

async function handleSaveServer() {
  if (!selectedBrokerId.value) {
    return;
  }
  submitting.value = true;
  try {
    if (editingServerId.value) {
      await updateBrokerServer(editingServerId.value, serverForm);
      ElMessage.success("服务器已更新");
    } else {
      await createBrokerServer(selectedBrokerId.value, serverForm);
      ElMessage.success("服务器已新增");
    }
    serverDialogVisible.value = false;
    await loadDetail(selectedBrokerId.value);
  } finally {
    submitting.value = false;
  }
}

async function handleDeleteServer(serverId: number) {
  await deleteBrokerServer(serverId);
  ElMessage.success("服务器已删除");
  if (selectedBrokerId.value) {
    await loadDetail(selectedBrokerId.value);
  }
}

async function handleBrokerChange(brokerId: number) {
  await router.replace(`/brokers/servers?brokerId=${brokerId}`);
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
