export interface DashboardOverview {
  totalBrokers: number;
  activeProjects: number;
  pendingTasks: number;
  overdueTasks: number;
  highRiskCount: number;
  summary: string;
}

export interface DashboardProject {
  id: number;
  brokerId: number;
  brokerName: string;
  projectName: string;
  projectType: string;
  ownerName: string;
  plannedDate: string;
  progressPercent: number;
  riskCount: number;
  overdueCount: number;
  status: string;
}

export interface BrokerSummary {
  id: number;
  name: string;
  shortName: string;
  currentProjects: number;
  activeProjects: number;
  nextMilestone: string;
  riskCount: number;
  overdueCount: number;
}

export interface BrokerCreatePayload {
  name: string;
  short_name: string;
  contact_name?: string;
  contact_phone?: string;
  status: string;
  note?: string;
}

export interface BrokerUpdatePayload extends BrokerCreatePayload {}

export interface AuthUser {
  id: number;
  username: string;
  displayName: string;
  role: string;
  status: string;
  createdAt: string;
  lastLoginAt: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: AuthUser;
}

export interface ProjectTask {
  id: number;
  name: string;
  ownerName: string;
  plannedContent: string;
  plannedDate: string;
  actualAction: string;
  completionResult: string;
  status: string;
}

export interface ProjectRisk {
  id: number;
  title: string;
  level: string;
  affectsMilestone: boolean;
  ownerName: string;
  plannedResolveDate: string;
  status: string;
  actionPlan: string;
}

export interface ProjectLog {
  id: number;
  logDate: string;
  content: string;
  nextAction: string;
}

export interface HistoryLogItem {
  id: number;
  brokerId: number;
  brokerName: string;
  projectId: number;
  projectName: string;
  projectType: string;
  logDate: string;
  content: string;
  nextAction: string;
}

export interface PersonalTaskItem {
  id: number;
  title: string;
  category: string;
  priority: string;
  note: string;
  completionResult: string;
  plannedDate: string;
  parentTaskId: number | null;
  parentTaskTitle: string;
  childCount: number;
  completedChildCount: number;
  status: string;
  sortOrder: number;
  createdAt: string;
  completedAt: string;
}

export interface PersonalRiskItem {
  id: number;
  type: string;
  title: string;
  category: string;
  priority: string;
  plannedDate: string;
  status: string;
  note: string;
}

export interface PersonalTaskCreatePayload {
  title: string;
  category: string;
  priority: string;
  note?: string;
  planned_date?: string;
  parent_task_id?: number | null;
}

export interface PersonalTaskUpdatePayload extends PersonalTaskCreatePayload {}

export interface PersonalTaskCompletePayload {
  completion_result: string;
}

export interface ProjectDetail {
  id: number;
  brokerId: number;
  brokerName: string;
  name: string;
  projectType: string;
  ownerName: string;
  plannedDate: string;
  status: string;
  progressPercent: number;
  overdueCount: number;
  description: string;
  tasks: ProjectTask[];
  risks: ProjectRisk[];
  logs: ProjectLog[];
}

export interface ReminderItem {
  id: number;
  type: string;
  brokerName: string;
  projectName: string;
  itemName: string;
  level: string;
  deadline: string;
  status: string;
  description: string;
}

export interface TemplateSummary {
  id: number;
  name: string;
  templateType: string;
  scene: string;
  taskCount: number;
  riskCount: number;
  recentUseCount: number;
}

export interface TemplateTaskItem {
  id?: number;
  name: string;
  plannedContent: string;
  defaultOwnerName: string;
  offsetDays: number;
}

export interface TemplateRiskItem {
  id?: number;
  title: string;
  level: string;
  affectsMilestone: boolean;
  actionPlan: string;
  offsetDays: number;
}

export interface TemplateDetail extends TemplateSummary {
  tasks: TemplateTaskItem[];
  risks: TemplateRiskItem[];
}

export interface WeeklyReport {
  summary: string;
  completed: string[];
  nextWeek: string[];
  overdue: string[];
  risks: string[];
  coordination: string[];
}

export interface ProjectCreatePayload {
  broker_id: number;
  name: string;
  project_type: string;
  owner_name: string;
  planned_date: string;
  status: string;
  description?: string;
}

export interface ProjectUpdatePayload extends ProjectCreatePayload {}

export interface TaskCreatePayload {
  name: string;
  owner_name: string;
  planned_content: string;
  planned_date: string;
  actual_action?: string;
  completion_result?: string;
  status: string;
}

export interface TaskUpdatePayload extends TaskCreatePayload {}

export interface RiskCreatePayload {
  title: string;
  level: string;
  affects_milestone: boolean;
  owner_name: string;
  planned_resolve_date: string;
  status: string;
  action_plan: string;
}

export interface RiskUpdatePayload extends RiskCreatePayload {}

export interface ProjectLogCreatePayload {
  content: string;
  next_action: string;
}

export interface ProjectLogUpdatePayload extends ProjectLogCreatePayload {}

export interface TemplateCreatePayload {
  name: string;
  template_type: string;
  scene: string;
  tasks: Array<{
    name: string;
    planned_content: string;
    default_owner_name?: string;
    offset_days: number;
  }>;
  risks: Array<{
    title: string;
    level: string;
    affects_milestone: boolean;
    action_plan: string;
    offset_days: number;
  }>;
}

export interface TemplateGenerateProjectPayload {
  broker_id: number;
  name: string;
  owner_name: string;
  planned_date: string;
  status: string;
  description?: string;
}

export interface TemplateUpdatePayload extends TemplateCreatePayload {}

export interface ProjectSaveAsTemplatePayload {
  name: string;
  scene: string;
}

export interface UserCreatePayload {
  username: string;
  display_name: string;
  password: string;
  role: string;
  status: string;
}

export interface UserUpdatePayload {
  display_name: string;
  role: string;
  status: string;
}

export interface UserResetPasswordPayload {
  password: string;
}

export interface ProgressProjectSummary {
  projectTemplateId: number;
  projectCode: string;
  projectName: string;
  brokerCount: number;
  completedCount: number;
  inProgressCount: number;
  notStartedCount: number;
  avgProgress: number;
  riskCount: number;
}

export interface ProgressProjectCreatePayload {
  code?: string;
  name: string;
  project_type: string;
  description?: string;
  status: string;
  sort_no?: number | null;
}

export interface ProgressProjectBrokerAddPayload {
  broker_ids: number[];
  input_mode: string;
  owner_name?: string;
  remark?: string;
}

export interface ProgressItemTemplateCreatePayload {
  item_key?: string;
  item_label: string;
  group_key?: string;
  group_label?: string;
  item_type: string;
  weight: number;
  allow_na: boolean;
  sort_no?: number | null;
  value_rule?: string;
  remark?: string;
}

export interface ProgressDynamicColumn {
  id: number;
  key: string;
  label: string;
  groupKey: string;
  groupLabel: string;
  type: string;
  weight: number;
  allowNa: boolean;
  sortNo: number;
}

export interface ProgressCellValue {
  type: string;
  statusValue: string;
  currentNum: number | null;
  targetNum: number | null;
  isNa: boolean;
  remark: string;
  calculatedPercent: number;
}

export interface ProgressMatrixRow {
  instanceId: number;
  brokerId: number;
  brokerName: string;
  inputMode: string;
  overallConclusion: string;
  progressPercent: number;
  status: string;
  latestUpdateAt: string;
  milestoneCount: number;
  riskCount: number;
  stage2?: {
    status: string;
    completedCount: number;
    totalCount: number;
    progressPercent: number;
    blockedCount: number;
    currentStepCode: string;
    currentStepNo: string;
    currentStepName: string;
    currentStepOwner: string;
  } | null;
  values: Record<string, ProgressCellValue>;
}

export interface ProgressMatrixResponse {
  project: {
    id: number;
    code: string;
    name: string;
    description: string;
  };
  summary: {
    brokerCount: number;
    completedCount: number;
    inProgressCount: number;
    notStartedCount: number;
    avgProgress: number;
    riskCount: number;
  };
  fixedColumns: Array<{ key: string; label: string }>;
  dynamicColumns: ProgressDynamicColumn[];
  rows: ProgressMatrixRow[];
}

export interface ProgressBrokerSimple {
  id: number;
  name: string;
}

export interface ProgressBrokerProject {
  instanceId: number;
  projectTemplateId: number;
  projectName: string;
  progressPercent: number;
  status: string;
  latestUpdateAt: string;
  riskCount: number;
  milestoneCount: number;
}

export interface ProgressBrokerView {
  brokerId: number;
  brokerName: string;
  projects: ProgressBrokerProject[];
}

export interface ProgressItemDetail {
  itemTemplateId: number;
  itemKey: string;
  itemLabel: string;
  groupKey: string;
  groupLabel: string;
  type: string;
  weight: number;
  allowNa: boolean;
  value: ProgressCellValue;
}

export interface ProgressLogItem {
  id: number;
  projectName?: string;
  brokerName?: string;
  logDate: string;
  itemTemplateId?: number | null;
  itemLabel: string;
  content: string;
  progressDelta: number;
  progressAfter: number;
  isMilestone: boolean;
  remark: string;
}

export interface ProgressRiskItem {
  id: number;
  projectName?: string;
  brokerName?: string;
  title: string;
  description: string;
  impactDesc: string;
  level: string;
  ownerName: string;
  plannedResolveDate: string;
  status: string;
  remark: string;
}

export interface ProgressStage2StepItem {
  stepInstanceId: number;
  stepCode: string;
  stepNoDisplay: string;
  stepName: string;
  ownersDefault: string;
  ownerActual: string;
  status: string;
  effectiveStatus: string;
  isOptional: boolean;
  isLastStep: boolean;
  applicableRule: string;
  dependencyStepCodes: string[];
  remarkTemplate: string;
  remark: string;
  blockerReason: string;
  startedAt: string;
  finishedAt: string;
}

export interface ProgressStage2Group {
  groupCode: string;
  groupName: string;
  completedCount: number;
  totalCount: number;
  steps: ProgressStage2StepItem[];
}

export interface ProgressInstanceDetail {
  instance: {
    id: number;
    projectTemplateId: number;
    projectName: string;
    brokerId: number;
    brokerName: string;
    inputMode: string;
    overallConclusion: string;
    progressPercent: number;
    status: string;
    latestUpdateAt: string;
    riskCount: number;
    milestoneCount: number;
    remark: string;
  };
  stage2?: {
    status: string;
    completedCount: number;
    totalCount: number;
    progressPercent: number;
    blockedCount: number;
    currentStepCode: string;
    currentStepNo: string;
    currentStepName: string;
    currentStepOwner: string;
  } | null;
  stage2Groups: ProgressStage2Group[];
  progressItems: ProgressItemDetail[];
  logs: ProgressLogItem[];
  risks: ProgressRiskItem[];
}

export interface ProgressValueUpdatePayload {
  status_value?: string | null;
  current_num?: number | null;
  target_num?: number | null;
  bool_value?: boolean | null;
  text_value?: string | null;
  is_na: boolean;
  remark?: string | null;
}

export interface ProgressLogCreatePayload {
  item_template_id?: number | null;
  log_date: string;
  content: string;
  progress_delta: number;
  progress_after: number;
  is_milestone: boolean;
  remark?: string | null;
}

export interface ProgressRiskCreatePayload {
  title: string;
  description?: string | null;
  impact_desc?: string | null;
  level: string;
  owner_name?: string | null;
  planned_resolve_date?: string | null;
  status: string;
  remark?: string | null;
}

export interface ProgressRiskUpdatePayload extends ProgressRiskCreatePayload {}

export interface ProgressStage2StepUpdatePayload {
  step_no_display?: string;
  step_name?: string;
  owner_actual?: string | null;
  status: string;
  remark?: string | null;
  blocker_reason?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface ProgressStage2StepCreatePayload {
  step_no_display: string;
  step_name: string;
  owner_actual?: string | null;
  status: string;
  remark?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface ProgressStage2StepMovePayload {
  direction: string;
}
