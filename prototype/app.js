const views = document.querySelectorAll(".view");
const navLinks = document.querySelectorAll("[data-view-target]");
const toast = document.querySelector("#toast");

const brokerData = [
  {
    id: "a",
    name: "A券商",
    summary: "升级类项目较多，当前有 1 个逾期任务需要优先处理。",
    totalProjects: 3,
    activeProjects: 2,
    nextNode: "4/20 版本升级",
    riskCount: 2,
    note: "该券商建议首页默认展示“关键节点 + 逾期任务 + 高风险事项”，避免进入详情前信息过少。",
    projects: [
      ["4月20日版本升级", "执行中", "75%", "风险 2 / 逾期 1"],
      ["接口包补充验证", "准备中", "40%", "风险 1 / 逾期 0"],
      ["升级复盘整理", "规划中", "10%", "风险 0 / 逾期 0"]
    ]
  },
  {
    id: "b",
    name: "B券商",
    summary: "接口改造项目推进中，当前联调压力较大但没有逾期。",
    totalProjects: 2,
    activeProjects: 1,
    nextNode: "4/18 接口改造",
    riskCount: 1,
    note: "适合在券商页直接展示负责人与联调进展，方便快速判断是否需要提前压进度。",
    projects: [
      ["接口改造", "准备中", "40%", "风险 1 / 逾期 0"],
      ["验证回归", "规划中", "15%", "风险 0 / 逾期 0"]
    ]
  },
  {
    id: "c",
    name: "C券商",
    summary: "新接入项目受对方环境影响，当前主要是协调类工作。",
    totalProjects: 4,
    activeProjects: 3,
    nextNode: "4/24 首轮验证",
    riskCount: 2,
    note: "这类项目更适合在风险中心高亮“环境未就绪”“对方待反馈”等风险类型。",
    projects: [
      ["新接入项目", "执行中", "55%", "风险 2 / 逾期 0"],
      ["资料补充", "执行中", "62%", "风险 0 / 逾期 0"],
      ["联调准备", "准备中", "35%", "风险 0 / 逾期 0"]
    ]
  }
];

const templateData = [
  {
    id: "upgrade",
    name: "版本升级模板",
    subtitle: "适用于版本升级、投产和上线准备类项目。",
    stats: ["标准任务 8", "默认风险 4", "最近使用 10 次"],
    badges: ["升级 / 上线", "关键节点强依赖", "默认提前 3 天提醒"],
    tasks: ["后台程序包", "接口包", "条件单包", "联调验证", "升级确认", "结果回收"],
    risks: ["交付延迟", "环境未就绪", "联调失败", "对方反馈慢"],
    note: "适合做成“先选模板，再补日期和负责人”的快速创建流程，不建议让用户反复回填重复内容。"
  },
  {
    id: "api",
    name: "接口改造模板",
    subtitle: "适用于接口联调、协议调整和改造验证。",
    stats: ["标准任务 6", "默认风险 3", "最近使用 5 次"],
    badges: ["联调 / 改造", "多轮验证", "适合中短周期"],
    tasks: ["接口包准备", "接口联调", "回归验证", "问题回收", "确认上线窗口"],
    risks: ["接口不兼容", "反馈不及时", "验证窗口不足"],
    note: "建议重点保留任务排序与里程碑偏移天数，方便新项目按关键日期快速带出计划。"
  },
  {
    id: "routine",
    name: "常规对接模板",
    subtitle: "适用于常规需求接入、资料准备和例行事项。",
    stats: ["标准任务 7", "默认风险 2", "最近使用 3 次"],
    badges: ["常规对接", "轻量流程", "适合快速复制"],
    tasks: ["需求确认", "资料准备", "接口清单确认", "跟进反馈", "收尾总结"],
    risks: ["资料缺失", "对接人反馈慢"],
    note: "适合新需求快速落地，建议在创建时支持删减默认任务，避免模板过重。"
  }
];

function activateView(viewName) {
  views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === viewName);
  });

  navLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.viewTarget === viewName);
  });
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    toast.classList.remove("visible");
  }, 2200);
}

function renderBrokerCards(selectedId = brokerData[0].id) {
  const brokerCards = document.querySelector("#broker-cards");
  const detailName = document.querySelector("#broker-detail-name");
  const detailProjectCount = document.querySelector("#broker-detail-project-count");
  const detailActiveCount = document.querySelector("#broker-detail-active-count");
  const detailNextNode = document.querySelector("#broker-detail-next-node");
  const detailRiskCount = document.querySelector("#broker-detail-risk-count");
  const detailProjects = document.querySelector("#broker-detail-projects");
  const detailNote = document.querySelector("#broker-detail-note");

  brokerCards.innerHTML = brokerData
    .map((broker) => `
      <button type="button" class="broker-card ${broker.id === selectedId ? "active" : ""}" data-broker-id="${broker.id}">
        <div>
          <p class="eyebrow">Broker</p>
          <h4>${broker.name}</h4>
          <p>${broker.summary}</p>
        </div>
        <div class="broker-card-footer">
          <span>${broker.totalProjects} 个项目</span>
          <span>${broker.nextNode}</span>
        </div>
      </button>
    `)
    .join("");

  const broker = brokerData.find((item) => item.id === selectedId) || brokerData[0];
  detailName.textContent = broker.name;
  detailProjectCount.textContent = `${broker.totalProjects} 个`;
  detailActiveCount.textContent = `${broker.activeProjects} 个`;
  detailNextNode.textContent = broker.nextNode;
  detailRiskCount.textContent = `${broker.riskCount} 个`;
  detailNote.textContent = broker.note;

  detailProjects.innerHTML = `
    <table>
      <tbody>
        ${broker.projects
          .map(
            ([name, status, progress, meta]) => `
            <tr>
              <td><strong>${name}</strong></td>
              <td>${status}</td>
              <td>${progress}</td>
              <td>${meta}</td>
            </tr>
          `
          )
          .join("")}
      </tbody>
    </table>
  `;

  brokerCards.querySelectorAll("[data-broker-id]").forEach((button) => {
    button.addEventListener("click", () => renderBrokerCards(button.dataset.brokerId));
  });
}

function renderTemplateCards(selectedId = templateData[0].id) {
  const templateCards = document.querySelector("#template-cards");
  const detailName = document.querySelector("#template-detail-name");
  const detailBadges = document.querySelector("#template-detail-badges");
  const taskList = document.querySelector("#template-task-list");
  const riskList = document.querySelector("#template-risk-list");
  const detailNote = document.querySelector("#template-detail-note");

  templateCards.innerHTML = templateData
    .map((template) => `
      <button type="button" class="template-card ${template.id === selectedId ? "active" : ""}" data-template-id="${template.id}">
        <div>
          <p class="eyebrow">Template</p>
          <h4>${template.name}</h4>
          <p>${template.subtitle}</p>
        </div>
        <div class="template-card-footer">
          ${template.stats.map((stat) => `<span>${stat}</span>`).join("")}
        </div>
      </button>
    `)
    .join("");

  const template = templateData.find((item) => item.id === selectedId) || templateData[0];
  detailName.textContent = template.name;
  detailBadges.innerHTML = template.badges.map((badge) => `<span class="tag info">${badge}</span>`).join("");
  taskList.innerHTML = template.tasks.map((task) => `<li>${task}</li>`).join("");
  riskList.innerHTML = template.risks.map((risk) => `<li>${risk}</li>`).join("");
  detailNote.textContent = template.note;

  templateCards.querySelectorAll("[data-template-id]").forEach((button) => {
    button.addEventListener("click", () => renderTemplateCards(button.dataset.templateId));
  });
}

function setupRiskFilters() {
  const filterButtons = document.querySelectorAll("[data-risk-filter]");
  const alertItems = document.querySelectorAll(".alert-item");

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");

      const selected = button.dataset.riskFilter;
      alertItems.forEach((item) => {
        const types = item.dataset.riskType.split(" ");
        const visible = selected === "all" || types.includes(selected);
        item.style.display = visible ? "grid" : "none";
      });
    });
  });
}

navLinks.forEach((link) => {
  link.addEventListener("click", () => activateView(link.dataset.viewTarget));
});

document.querySelector("#template-use-btn").addEventListener("click", () => {
  showToast("已模拟进入“从模板创建项目”流程。");
});

document.querySelector("#copy-report").addEventListener("click", async () => {
  const reportText = [
    "本周完成事项：A券商后台程序包已交付；B券商接口联调完成第一轮。",
    "下周计划事项：推进 A券商条件单包交付；完成 C券商环境确认。",
    "逾期事项：A券商条件单包已逾期 1 天。",
    "重点风险：C券商环境未就绪，影响关键节点。",
    "需协调事项：确认升级窗口与备用验证安排。"
  ].join("\n");

  try {
    await navigator.clipboard.writeText(reportText);
    showToast("周报摘要已复制到剪贴板。");
  } catch (error) {
    showToast("浏览器未开放剪贴板权限，但周报结构已准备好。");
  }
});

renderBrokerCards();
renderTemplateCards();
setupRiskFilters();
