# InlineEdit Recent Changes 技术方案

## 1. 方案概述

### 1.1 背景
当前InlineEdit功能基于代码上下文（above context、below context）和import内容进行代码生成，但缺少本地开发历史信息。为了提升代码生成的准确性和上下文相关性，需要引入同文件最近三次changes来补充InlineEdit的上下文信息。

### 1.2 目标
- **增强上下文理解**: 通过Recent Changes提供代码演进历史，帮助模型理解开发意图
- **提升生成质量**: 基于最近的代码变更模式，生成更符合开发习惯的代码
- **实时感知变化**: 捕获IDEA中的本地changes，提供最新的开发上下文

### 1.3 技术架构
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IDEA Plugin   │───▶│  Change Detector │───▶│  Context Builder│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Local Changes   │    │   JGit Scanner   │    │ InlineEdit API  │
│   Collection    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 2. 数据组织格式

### 2.1 Context结构
基于现有benchmark格式，扩展Recent Changes部分：

```java
// Context Above (带行号)
  1: @Service
  2: public class TResMsServiceImpl implements TResMsService {
  3:     private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
  4:
  5:     private static final String TABLE_NAME = "t_res_micro_service";

// Context Below (带行号，为目标代码预留空间)
 101: @Override
 102:     public int update(ResMsRequestBody requestBody) throws VscServiceException {
 103:         String operateUser = DevCloudTokenStore.getUserName();
```

### 2.2 Recent Changes格式
按照优先级rc1 > rc2 > rc3组织，使用标准unified diff格式：

```diff
### Recent Change 3 (Earliest preparation work)
```diff
@@ -2,5 +2,5 @@
  2: public class TResMsServiceImpl implements TResMsService {
-  3: // TODO add logger
+  3: private static final Logger LOGGER = LogManager.getLogger(TResMsServiceImpl.class);
  4:
-  5: // TODO table name  
+  5: private static final String TABLE_NAME = "t_res_micro_service";
```

### Recent Change 2 (Intermediate preparation)
```diff
@@ -18,10 +18,10 @@
- 18: LOGGER.info("listService start");
+ 18: LOGGER.info("[begin listService][tableName={}]", TABLE_NAME);
  19: IPage page = new Page(pageNum, pageSize);
+ 20: try {
  21:   IPage<TResServiceResp> servicePage = tResMicroServiceMapper.getServiceList(page);
+ 22:   LOGGER.info("[end listService][tableName={}]", TABLE_NAME);
+ 23:   return CommonPage.restPage(servicePage);
+ 24: } catch (DataAccessException e) {
+ 25:   LOGGER.error("[listService from {} error][message = {}]", TABLE_NAME, e.getMessage());
+ 26:   throw ExceptionUtils.getSqlException(e, "query service list from database error");
+ 27: }
```

### Recent Change 1 (Latest preparation work)  
```diff
@@ -25,3 +25,8 @@
  25: LOGGER.error("[listService from {} error][message = {}]", TABLE_NAME, e.getMessage());
  26:   throw ExceptionUtils.getSqlException(e, "query service list from database error");
  27: }
+ 28:
+ 29: // TODO: Implement new method here
+ 30: // This is where the new functionality will be added
+ 31: // Based on the recent changes pattern
```
```

### 2.3 关键格式要求
- **行号标注**: 所有代码行必须有明确的行号标注（如`+ 23:`、`- 18:`）
- **diff头信息**: 使用标准格式`@@ -起始行,变更数 +起始行,变更数 @@`
- **变更符号**: 明确使用`+`表示新增，`-`表示删除，空格表示上下文
- **行号一致性**: diff中的行号必须与context中的行号完全对应

## 3. IDEA插件实现方案

### 3.1 Local Changes收集

#### 3.1.1 JGit集成方案
```java
public class GitChangeDetector {
    private final Repository repository;
    private final Git git;

    public List<RecentChange> getRecentChanges(String filePath, int maxChanges) {
        try {
            // 1. 获取文件的commit历史
            Iterable<RevCommit> commits = git.log()
                .addPath(filePath)
                .setMaxCount(maxChanges + 1) // +1 to get diff with previous
                .call();

            // 2. 分析每次commit的diff
            List<RecentChange> changes = new ArrayList<>();
            RevCommit[] commitArray = StreamSupport.stream(commits.spliterator(), false)
                .toArray(RevCommit[]::new);

            for (int i = 0; i < Math.min(maxChanges, commitArray.length - 1); i++) {
                RevCommit current = commitArray[i];
                RevCommit previous = commitArray[i + 1];

                // 3. 生成diff
                DiffEntry diff = getDiffEntry(previous, current, filePath);
                RecentChange change = parseDiffToRecentChange(diff, i + 1);
                changes.add(change);
            }

            return changes;
        } catch (Exception e) {
            log.error("Failed to get recent changes for {}", filePath, e);
            return Collections.emptyList();
        }
    }

    private RecentChange parseDiffToRecentChange(DiffEntry diff, int changeNumber) {
        // 解析diff内容，生成标准格式的RecentChange
        return RecentChange.builder()
            .number(changeNumber)
            .description(getChangeDescription(changeNumber))
            .diffContent(formatDiffWithLineNumbers(diff))
            .build();
    }
}
```

#### 3.1.2 实时变更监听
```java
@Component
public class FileChangeListener implements VirtualFileListener {
    private final Map<String, List<Change>> pendingChanges = new ConcurrentHashMap<>();

    @Override
    public void contentsChanged(@NotNull VirtualFileEvent event) {
        VirtualFile file = event.getFile();
        if (isJavaFile(file)) {
            // 记录文件变更
            recordChange(file, ChangeType.CONTENT_MODIFIED);

            // 触发Recent Changes更新
            updateRecentChanges(file);
        }
    }

    private void updateRecentChanges(VirtualFile file) {
        ApplicationManager.getApplication().runReadAction(() -> {
            try {
                // 1. 获取当前文件内容
                String currentContent = VfsUtil.loadText(file);

                // 2. 与Git历史对比，生成Recent Changes
                List<RecentChange> recentChanges = gitChangeDetector
                    .getRecentChanges(file.getPath(), 3);

                // 3. 缓存结果供InlineEdit使用
                recentChangesCache.put(file.getPath(), recentChanges);

            } catch (Exception e) {
                log.error("Failed to update recent changes for {}", file.getPath(), e);
            }
        });
    }
}
```

### 3.2 插件架构设计

#### 3.2.1 核心组件
```java
// 主服务类
@Service
public class InlineEditRecentChangesService {
    private final GitChangeDetector gitDetector;
    private final ChangeFormatter formatter;
    private final RecentChangesCache cache;

    public InlineEditContext buildContext(PsiFile file, int caretOffset) {
        // 1. 获取传统上下文
        CodeContext codeContext = extractCodeContext(file, caretOffset);

        // 2. 获取Recent Changes
        List<RecentChange> recentChanges = getRecentChanges(file);

        // 3. 构建完整上下文
        return InlineEditContext.builder()
            .aboveContext(addLineNumbers(codeContext.getAbove()))
            .belowContext(addLineNumbers(codeContext.getBelow()))
            .imports(codeContext.getImports())
            .recentChanges(recentChanges)
            .build();
    }

    private List<RecentChange> getRecentChanges(PsiFile file) {
        String filePath = file.getVirtualFile().getPath();

        // 1. 尝试从缓存获取
        List<RecentChange> cached = cache.get(filePath);
        if (cached != null && !cache.isExpired(filePath)) {
            return cached;
        }

        // 2. 从Git获取最新changes
        List<RecentChange> changes = gitDetector.getRecentChanges(filePath, 3);

        // 3. 格式化为标准格式
        List<RecentChange> formatted = changes.stream()
            .map(formatter::formatWithLineNumbers)
            .collect(Collectors.toList());

        // 4. 更新缓存
        cache.put(filePath, formatted);

        return formatted;
    }
}
```

#### 3.2.2 数据模型
```java
@Data
@Builder
public class RecentChange {
    private int number;              // RC编号 (1, 2, 3)
    private String description;      // 变更描述
    private String diffContent;      // 标准diff格式内容
    private long timestamp;          // 变更时间戳
    private String commitHash;       // Git commit hash
}

@Data
@Builder
public class InlineEditContext {
    private String aboveContext;     // 上文代码（带行号）
    private String belowContext;     // 下文代码（带行号）
    private String imports;          // 导入信息
    private List<RecentChange> recentChanges; // 最近变更
    private String targetFeature;    // 目标功能描述
}
```

### 3.3 扫描检测机制

#### 3.3.1 增量扫描策略
```java
@Component
public class IncrementalChangeScanner {
    private final ScheduledExecutorService scheduler =
        Executors.newScheduledThreadPool(2);

    @PostConstruct
    public void startScanning() {
        // 1. 定期扫描Git变更
        scheduler.scheduleAtFixedRate(this::scanGitChanges, 0, 30, TimeUnit.SECONDS);

        // 2. 监听文件系统变更
        scheduler.scheduleAtFixedRate(this::scanFileSystemChanges, 0, 5, TimeUnit.SECONDS);
    }

    private void scanGitChanges() {
        try {
            // 扫描所有打开的项目
            for (Project project : ProjectManager.getInstance().getOpenProjects()) {
                VirtualFile baseDir = project.getBaseDir();
                if (baseDir != null) {
                    scanProjectChanges(project);
                }
            }
        } catch (Exception e) {
            log.error("Git changes scan failed", e);
        }
    }

    private void scanProjectChanges(Project project) {
        // 1. 获取Git仓库状态
        GitRepository repo = GitUtil.getRepositoryManager(project)
            .getRepositoryForRoot(project.getBaseDir());

        if (repo == null) return;

        // 2. 检查最近的commits
        String lastScannedCommit = getLastScannedCommit(project);
        List<String> newCommits = getNewCommits(repo, lastScannedCommit);

        // 3. 分析新commits中的Java文件变更
        for (String commitHash : newCommits) {
            analyzeCommitChanges(repo, commitHash);
        }

        // 4. 更新扫描状态
        updateLastScannedCommit(project, repo.getCurrentRevision());
    }
}
```

#### 3.3.2 智能过滤机制
```java
public class ChangeFilter {

    public boolean shouldIncludeChange(DiffEntry diff, RevCommit commit) {
        // 1. 文件类型过滤
        if (!isJavaFile(diff.getNewPath())) {
            return false;
        }

        // 2. 变更大小过滤（避免大规模重构）
        int linesChanged = calculateLinesChanged(diff);
        if (linesChanged > 100) {
            return false;
        }

        // 3. 时间过滤（只关注最近的变更）
        long commitTime = commit.getCommitTime() * 1000L;
        long cutoffTime = System.currentTimeMillis() - TimeUnit.DAYS.toMillis(7);
        if (commitTime < cutoffTime) {
            return false;
        }

        // 4. 变更类型过滤
        return isRelevantChange(diff);
    }

    private boolean isRelevantChange(DiffEntry diff) {
        // 排除以下类型的变更：
        // - 纯注释变更
        // - 格式化变更
        // - import调整
        // - 测试文件变更

        String content = getDiffContent(diff);

        // 检查是否包含实质性代码变更
        return content.lines()
            .filter(line -> line.startsWith("+") || line.startsWith("-"))
            .anyMatch(this::isSubstantiveChange);
    }

    private boolean isSubstantiveChange(String line) {
        String trimmed = line.substring(1).trim();

        // 排除注释行
        if (trimmed.startsWith("//") || trimmed.startsWith("/*") || trimmed.startsWith("*")) {
            return false;
        }

        // 排除空行
        if (trimmed.isEmpty()) {
            return false;
        }

        // 排除纯import变更
        if (trimmed.startsWith("import ")) {
            return false;
        }

        return true;
    }
}
```

## 4. 打点方案设计

### 4.1 采纳率指标

#### 4.1.1 核心指标定义
```java
@Data
public class InlineEditMetrics {
    // 基础指标
    private String sessionId;           // 会话ID
    private String userId;              // 用户ID
    private String projectId;           // 项目ID
    private long timestamp;             // 时间戳

    // 上下文指标
    private boolean hasRecentChanges;   // 是否包含Recent Changes
    private int recentChangesCount;     // Recent Changes数量
    private int contextLinesAbove;      // 上文行数
    private int contextLinesBelow;      // 下文行数

    // 生成指标
    private int suggestionsCount;       // 建议数量
    private int suggestedLinesCount;    // 建议代码行数
    private long generationTimeMs;      // 生成耗时

    // 采纳指标
    private boolean accepted;           // 是否采纳
    private int acceptedLinesCount;     // 采纳行数
    private double acceptanceRatio;     // 采纳比例
    private long acceptanceTimeMs;      // 采纳耗时

    // 质量指标
    private boolean compilable;         // 是否可编译
    private boolean hasRuntimeError;    // 是否有运行时错误
    private int editDistance;           // 与最终代码的编辑距离
}
```

#### 4.1.2 采纳率计算
```java
@Service
public class AdoptionRateCalculator {

    public AdoptionMetrics calculateAdoption(InlineEditSession session) {
        return AdoptionMetrics.builder()
            .immediateAdoption(calculateImmediateAdoption(session))
            .partialAdoption(calculatePartialAdoption(session))
            .modifiedAdoption(calculateModifiedAdoption(session))
            .overallAdoption(calculateOverallAdoption(session))
            .build();
    }

    private double calculateImmediateAdoption(InlineEditSession session) {
        // 完全采纳：用户直接接受建议，无修改
        if (session.isAccepted() && session.getEditDistance() == 0) {
            return 1.0;
        }
        return 0.0;
    }

    private double calculatePartialAdoption(InlineEditSession session) {
        // 部分采纳：用户采纳了部分建议
        if (session.getAcceptedLinesCount() > 0) {
            return (double) session.getAcceptedLinesCount() / session.getSuggestedLinesCount();
        }
        return 0.0;
    }

    private double calculateModifiedAdoption(InlineEditSession session) {
        // 修改后采纳：用户修改建议后采纳
        if (session.isAccepted() && session.getEditDistance() > 0) {
            // 基于编辑距离计算相似度
            int maxLength = Math.max(session.getSuggestedLinesCount(),
                                   session.getAcceptedLinesCount());
            return 1.0 - (double) session.getEditDistance() / maxLength;
        }
        return 0.0;
    }

    private double calculateOverallAdoption(InlineEditSession session) {
        // 综合采纳率
        double immediate = calculateImmediateAdoption(session);
        double partial = calculatePartialAdoption(session);
        double modified = calculateModifiedAdoption(session);

        return Math.max(immediate, Math.max(partial, modified));
    }
}
```

### 4.2 对比实验设计

#### 4.2.1 A/B测试框架
```java
@Component
public class ABTestManager {

    public ExperimentGroup assignUserToGroup(String userId) {
        // 基于用户ID的哈希值分组
        int hash = userId.hashCode();
        int group = Math.abs(hash) % 100;

        if (group < 50) {
            return ExperimentGroup.CONTROL;      // 对照组：无Recent Changes
        } else {
            return ExperimentGroup.TREATMENT;    // 实验组：有Recent Changes
        }
    }

    public InlineEditContext buildContextForGroup(ExperimentGroup group,
                                                 PsiFile file, int caretOffset) {
        InlineEditContext.Builder builder = InlineEditContext.builder();

        // 基础上下文（两组都有）
        CodeContext codeContext = extractCodeContext(file, caretOffset);
        builder.aboveContext(addLineNumbers(codeContext.getAbove()))
               .belowContext(addLineNumbers(codeContext.getBelow()))
               .imports(codeContext.getImports());

        // Recent Changes（仅实验组有）
        if (group == ExperimentGroup.TREATMENT) {
            List<RecentChange> recentChanges = getRecentChanges(file);
            builder.recentChanges(recentChanges);
        }

        return builder.build();
    }
}

enum ExperimentGroup {
    CONTROL,    // 对照组
    TREATMENT   // 实验组
}
```

#### 4.2.2 效果对比分析
```java
@Service
public class ExperimentAnalyzer {

    public ExperimentResults analyzeResults(LocalDate startDate, LocalDate endDate) {
        // 1. 获取实验数据
        List<InlineEditMetrics> controlData = getMetricsByGroup(
            ExperimentGroup.CONTROL, startDate, endDate);
        List<InlineEditMetrics> treatmentData = getMetricsByGroup(
            ExperimentGroup.TREATMENT, startDate, endDate);

        // 2. 计算关键指标
        return ExperimentResults.builder()
            .controlMetrics(calculateGroupMetrics(controlData))
            .treatmentMetrics(calculateGroupMetrics(treatmentData))
            .improvement(calculateImprovement(controlData, treatmentData))
            .significance(calculateStatisticalSignificance(controlData, treatmentData))
            .build();
    }

    private GroupMetrics calculateGroupMetrics(List<InlineEditMetrics> data) {
        return GroupMetrics.builder()
            .totalSessions(data.size())
            .averageAdoptionRate(calculateAverageAdoption(data))
            .averageGenerationTime(calculateAverageGenerationTime(data))
            .compilationSuccessRate(calculateCompilationSuccessRate(data))
            .userSatisfactionScore(calculateSatisfactionScore(data))
            .build();
    }

    private ImprovementMetrics calculateImprovement(List<InlineEditMetrics> control,
                                                   List<InlineEditMetrics> treatment) {
        double controlAdoption = calculateAverageAdoption(control);
        double treatmentAdoption = calculateAverageAdoption(treatment);

        double adoptionImprovement = (treatmentAdoption - controlAdoption) / controlAdoption;

        return ImprovementMetrics.builder()
            .adoptionRateImprovement(adoptionImprovement)
            .generationTimeImprovement(calculateGenerationTimeImprovement(control, treatment))
            .qualityImprovement(calculateQualityImprovement(control, treatment))
            .build();
    }
}
```

### 4.3 数据收集策略

#### 4.3.1 埋点实现
```java
@Component
public class MetricsCollector {
    private final MetricsRepository repository;
    private final AsyncExecutor asyncExecutor;

    public void recordInlineEditSession(InlineEditSession session) {
        // 异步记录，避免影响用户体验
        asyncExecutor.execute(() -> {
            try {
                InlineEditMetrics metrics = buildMetrics(session);
                repository.save(metrics);

                // 实时指标更新
                updateRealTimeMetrics(metrics);

            } catch (Exception e) {
                log.error("Failed to record metrics for session {}",
                         session.getSessionId(), e);
            }
        });
    }

    private InlineEditMetrics buildMetrics(InlineEditSession session) {
        return InlineEditMetrics.builder()
            .sessionId(session.getSessionId())
            .userId(session.getUserId())
            .projectId(session.getProjectId())
            .timestamp(System.currentTimeMillis())
            .hasRecentChanges(session.getContext().getRecentChanges() != null)
            .recentChangesCount(getRecentChangesCount(session))
            .contextLinesAbove(getContextLinesCount(session.getContext().getAboveContext()))
            .contextLinesBelow(getContextLinesCount(session.getContext().getBelowContext()))
            .suggestionsCount(session.getSuggestions().size())
            .suggestedLinesCount(calculateSuggestedLines(session))
            .generationTimeMs(session.getGenerationTimeMs())
            .accepted(session.isAccepted())
            .acceptedLinesCount(session.getAcceptedLinesCount())
            .acceptanceRatio(calculateAcceptanceRatio(session))
            .acceptanceTimeMs(session.getAcceptanceTimeMs())
            .compilable(session.isCompilable())
            .hasRuntimeError(session.hasRuntimeError())
            .editDistance(session.getEditDistance())
            .build();
    }
}
```

#### 4.3.2 隐私保护
```java
@Component
public class PrivacyProtector {

    public InlineEditMetrics sanitizeMetrics(InlineEditMetrics raw) {
        return raw.toBuilder()
            // 移除敏感信息
            .userId(hashUserId(raw.getUserId()))
            .projectId(hashProjectId(raw.getProjectId()))
            // 代码内容不记录，只记录统计信息
            .build();
    }

    private String hashUserId(String userId) {
        // 使用单向哈希保护用户隐私
        return DigestUtils.sha256Hex(userId + SALT);
    }

    public boolean shouldCollectMetrics(String userId) {
        // 检查用户是否同意数据收集
        return userConsentService.hasConsent(userId, ConsentType.METRICS_COLLECTION);
    }
}
```

## 5. 数据存储与收集

### 5.1 Recent Changes数据存储设计

#### 5.1.1 核心数据库Schema设计

```sql
-- 项目信息表
CREATE TABLE projects (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_hash VARCHAR(64) UNIQUE NOT NULL,  -- 项目标识哈希
    language VARCHAR(32) NOT NULL,             -- 编程语言
    framework VARCHAR(64),                     -- 框架信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_project_hash (project_hash),
    INDEX idx_language (language)
) PARTITION BY HASH(id) PARTITIONS 16;

-- 文件信息表
CREATE TABLE files (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    file_path_hash VARCHAR(64) NOT NULL,       -- 文件路径哈希
    file_extension VARCHAR(16),                -- 文件扩展名
    file_size_bytes INT,                       -- 文件大小
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE KEY uk_project_file (project_id, file_path_hash),
    INDEX idx_file_extension (file_extension)
) PARTITION BY HASH(project_id) PARTITIONS 16;

-- Git提交信息表
CREATE TABLE git_commits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    commit_hash VARCHAR(40) NOT NULL,          -- Git commit SHA
    commit_message TEXT,                       -- 提交信息
    author_hash VARCHAR(64),                   -- 作者哈希
    commit_timestamp TIMESTAMP NOT NULL,       -- 提交时间
    files_changed INT DEFAULT 0,               -- 变更文件数
    lines_added INT DEFAULT 0,                 -- 新增行数
    lines_deleted INT DEFAULT 0,               -- 删除行数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE KEY uk_project_commit (project_id, commit_hash),
    INDEX idx_commit_timestamp (commit_timestamp),
    INDEX idx_author_hash (author_hash)
) PARTITION BY RANGE (UNIX_TIMESTAMP(commit_timestamp)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01')),
    PARTITION p202403 VALUES LESS THAN (UNIX_TIMESTAMP('2024-04-01')),
    -- 按月分区，支持自动分区管理
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Recent Changes核心表
CREATE TABLE recent_changes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    file_id BIGINT NOT NULL,
    commit_id BIGINT NOT NULL,
    change_type ENUM('ADD', 'MODIFY', 'DELETE', 'RENAME') NOT NULL,
    start_line INT NOT NULL,                   -- 变更起始行
    end_line INT NOT NULL,                     -- 变更结束行
    lines_added INT DEFAULT 0,
    lines_deleted INT DEFAULT 0,
    diff_content MEDIUMTEXT,                   -- 标准diff格式内容
    diff_content_hash VARCHAR(64),             -- diff内容哈希，用于去重
    context_before MEDIUMTEXT,                 -- 变更前上下文
    context_after MEDIUMTEXT,                  -- 变更后上下文
    change_priority TINYINT DEFAULT 3,         -- 变更优先级 (1=高, 2=中, 3=低)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (commit_id) REFERENCES git_commits(id),
    INDEX idx_file_commit (file_id, commit_id),
    INDEX idx_change_type (change_type),
    INDEX idx_change_priority (change_priority),
    INDEX idx_diff_hash (diff_content_hash),
    INDEX idx_created_at (created_at)
) PARTITION BY HASH(file_id) PARTITIONS 32;

-- InlineEdit会话表
CREATE TABLE inline_edit_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_hash VARCHAR(64) NOT NULL,            -- 用户哈希
    project_id BIGINT NOT NULL,
    file_id BIGINT NOT NULL,
    caret_position INT NOT NULL,               -- 光标位置
    context_above TEXT,                        -- 上文代码
    context_below TEXT,                        -- 下文代码
    recent_changes_used JSON,                  -- 使用的Recent Changes ID列表
    target_feature TEXT,                       -- 目标功能描述
    generated_code TEXT,                       -- 生成的代码
    final_code TEXT,                          -- 最终采纳的代码
    adoption_status ENUM('ACCEPTED', 'REJECTED', 'MODIFIED', 'PARTIAL') NOT NULL,
    adoption_ratio DECIMAL(5,4) DEFAULT 0.0000, -- 采纳比例
    generation_time_ms INT,                    -- 生成耗时
    adoption_time_ms INT,                      -- 采纳耗时
    edit_distance INT DEFAULT 0,               -- 编辑距离
    compilation_success BOOLEAN DEFAULT FALSE, -- 编译是否成功
    runtime_error BOOLEAN DEFAULT FALSE,       -- 是否有运行时错误
    experiment_group ENUM('CONTROL', 'TREATMENT') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (file_id) REFERENCES files(id),
    INDEX idx_user_hash (user_hash),
    INDEX idx_adoption_status (adoption_status),
    INDEX idx_experiment_group (experiment_group),
    INDEX idx_created_at (created_at)
) PARTITION BY RANGE (UNIX_TIMESTAMP(created_at)) (
    PARTITION p202401 VALUES LESS THAN (UNIX_TIMESTAMP('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (UNIX_TIMESTAMP('2024-03-01')),
    -- 按月分区
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

#### 5.1.2 分布式存储架构

```java
@Configuration
public class DataStorageConfig {

    // 主数据库配置（写入）
    @Bean
    @Primary
    public DataSource primaryDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:mysql://primary-db:3306/inline_edit");
        config.setUsername("app_user");
        config.setPassword("${db.password}");
        config.setMaximumPoolSize(50);
        config.setMinimumIdle(10);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setMaxLifetime(1800000);
        return new HikariDataSource(config);
    }

    // 只读副本配置（读取）
    @Bean
    public DataSource readOnlyDataSource() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:mysql://readonly-db:3306/inline_edit");
        config.setUsername("readonly_user");
        config.setPassword("${db.readonly.password}");
        config.setMaximumPoolSize(30);
        config.setReadOnly(true);
        return new HikariDataSource(config);
    }

    // Redis缓存配置
    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(jedisConnectionFactory());
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());
        return template;
    }
}

@Service
public class RecentChangesStorageService {

    @Autowired
    @Qualifier("primaryDataSource")
    private DataSource writeDataSource;

    @Autowired
    @Qualifier("readOnlyDataSource")
    private DataSource readDataSource;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String CACHE_PREFIX = "rc:";
    private static final int CACHE_TTL = 3600; // 1小时

    public void saveRecentChange(RecentChangeEntity change) {
        // 1. 写入主数据库
        try (Connection conn = writeDataSource.getConnection()) {
            String sql = """
                INSERT INTO recent_changes
                (file_id, commit_id, change_type, start_line, end_line,
                 lines_added, lines_deleted, diff_content, diff_content_hash,
                 context_before, context_after, change_priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """;

            try (PreparedStatement stmt = conn.prepareStatement(sql)) {
                stmt.setLong(1, change.getFileId());
                stmt.setLong(2, change.getCommitId());
                stmt.setString(3, change.getChangeType().name());
                stmt.setInt(4, change.getStartLine());
                stmt.setInt(5, change.getEndLine());
                stmt.setInt(6, change.getLinesAdded());
                stmt.setInt(7, change.getLinesDeleted());
                stmt.setString(8, change.getDiffContent());
                stmt.setString(9, change.getDiffContentHash());
                stmt.setString(10, change.getContextBefore());
                stmt.setString(11, change.getContextAfter());
                stmt.setInt(12, change.getChangePriority());

                stmt.executeUpdate();
            }
        } catch (SQLException e) {
            log.error("Failed to save recent change", e);
            throw new DataStorageException("Failed to save recent change", e);
        }

        // 2. 异步更新缓存
        CompletableFuture.runAsync(() -> updateCache(change));
    }

    public List<RecentChangeEntity> getRecentChanges(Long fileId, int limit) {
        String cacheKey = CACHE_PREFIX + "file:" + fileId + ":limit:" + limit;

        // 1. 尝试从缓存获取
        List<RecentChangeEntity> cached = (List<RecentChangeEntity>)
            redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }

        // 2. 从只读数据库查询
        List<RecentChangeEntity> changes = queryFromDatabase(fileId, limit);

        // 3. 更新缓存
        redisTemplate.opsForValue().set(cacheKey, changes, CACHE_TTL, TimeUnit.SECONDS);

        return changes;
    }

    private List<RecentChangeEntity> queryFromDatabase(Long fileId, int limit) {
        try (Connection conn = readDataSource.getConnection()) {
            String sql = """
                SELECT rc.*, gc.commit_timestamp, gc.commit_hash
                FROM recent_changes rc
                JOIN git_commits gc ON rc.commit_id = gc.id
                WHERE rc.file_id = ?
                ORDER BY gc.commit_timestamp DESC, rc.change_priority ASC
                LIMIT ?
                """;

            try (PreparedStatement stmt = conn.prepareStatement(sql)) {
                stmt.setLong(1, fileId);
                stmt.setInt(2, limit);

                ResultSet rs = stmt.executeQuery();
                List<RecentChangeEntity> changes = new ArrayList<>();

                while (rs.next()) {
                    RecentChangeEntity change = RecentChangeEntity.builder()
                        .id(rs.getLong("id"))
                        .fileId(rs.getLong("file_id"))
                        .commitId(rs.getLong("commit_id"))
                        .changeType(ChangeType.valueOf(rs.getString("change_type")))
                        .startLine(rs.getInt("start_line"))
                        .endLine(rs.getInt("end_line"))
                        .linesAdded(rs.getInt("lines_added"))
                        .linesDeleted(rs.getInt("lines_deleted"))
                        .diffContent(rs.getString("diff_content"))
                        .contextBefore(rs.getString("context_before"))
                        .contextAfter(rs.getString("context_after"))
                        .changePriority(rs.getInt("change_priority"))
                        .commitTimestamp(rs.getTimestamp("commit_timestamp"))
                        .commitHash(rs.getString("commit_hash"))
                        .build();
                    changes.add(change);
                }

                return changes;
            }
        } catch (SQLException e) {
            log.error("Failed to query recent changes for file {}", fileId, e);
            throw new DataStorageException("Failed to query recent changes", e);
        }
    }
}
```

### 5.2 数据收集管道设计

#### 5.2.1 实时数据收集Pipeline

```java
@Component
public class DataCollectionPipeline {

    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final RecentChangesStorageService storageService;
    private final DataValidationService validationService;

    // Kafka主题配置
    private static final String TOPIC_RAW_CHANGES = "inline-edit.raw-changes";
    private static final String TOPIC_PROCESSED_CHANGES = "inline-edit.processed-changes";
    private static final String TOPIC_SESSION_EVENTS = "inline-edit.session-events";
    private static final String TOPIC_DLQ = "inline-edit.dead-letter";

    // 从IDEA插件收集原始数据
    public void collectRawChange(RawChangeEvent event) {
        try {
            // 1. 基础验证
            if (!validationService.isValidRawEvent(event)) {
                log.warn("Invalid raw event: {}", event);
                return;
            }

            // 2. 数据脱敏
            RawChangeEvent sanitized = sanitizeEvent(event);

            // 3. 发送到Kafka进行异步处理
            kafkaTemplate.send(TOPIC_RAW_CHANGES, sanitized.getFileId().toString(), sanitized)
                .addCallback(
                    result -> log.debug("Raw change sent successfully: {}", event.getSessionId()),
                    failure -> {
                        log.error("Failed to send raw change: {}", event.getSessionId(), failure);
                        // 降级到本地队列
                        fallbackToLocalQueue(sanitized);
                    }
                );

        } catch (Exception e) {
            log.error("Error collecting raw change", e);
            // 记录到错误队列
            sendToDeadLetterQueue(event, e);
        }
    }

    // 处理原始变更事件
    @KafkaListener(topics = TOPIC_RAW_CHANGES, concurrency = "3")
    public void processRawChange(RawChangeEvent event) {
        try {
            // 1. 详细验证
            ValidationResult validation = validationService.validateRawEvent(event);
            if (!validation.isValid()) {
                log.warn("Validation failed for event {}: {}",
                        event.getSessionId(), validation.getErrors());
                return;
            }

            // 2. 数据清洗和标准化
            ProcessedChangeEvent processed = cleanAndNormalize(event);

            // 3. 提取Recent Changes
            List<RecentChange> recentChanges = extractRecentChanges(processed);

            // 4. 存储到数据库
            for (RecentChange change : recentChanges) {
                RecentChangeEntity entity = convertToEntity(change);
                storageService.saveRecentChange(entity);
            }

            // 5. 发送处理完成事件
            kafkaTemplate.send(TOPIC_PROCESSED_CHANGES, processed.getFileId().toString(), processed);

        } catch (Exception e) {
            log.error("Error processing raw change: {}", event.getSessionId(), e);
            // 重试机制
            handleProcessingError(event, e);
        }
    }

    // 处理InlineEdit会话事件
    @KafkaListener(topics = TOPIC_SESSION_EVENTS, concurrency = "5")
    public void processSessionEvent(SessionEvent event) {
        try {
            // 1. 验证会话事件
            if (!validationService.isValidSessionEvent(event)) {
                log.warn("Invalid session event: {}", event.getSessionId());
                return;
            }

            // 2. 构建完整的会话记录
            InlineEditSessionEntity session = buildSessionEntity(event);

            // 3. 计算采纳率指标
            AdoptionMetrics metrics = calculateAdoptionMetrics(session);
            session.setAdoptionRatio(metrics.getOverallAdoption());
            session.setEditDistance(metrics.getEditDistance());

            // 4. 存储会话数据
            storageService.saveSession(session);

            // 5. 更新实时指标
            updateRealTimeMetrics(metrics);

        } catch (Exception e) {
            log.error("Error processing session event: {}", event.getSessionId(), e);
            handleSessionProcessingError(event, e);
        }
    }

    private RawChangeEvent sanitizeEvent(RawChangeEvent event) {
        return RawChangeEvent.builder()
            .sessionId(event.getSessionId())
            .userHash(hashUserId(event.getUserId()))  // 用户ID哈希化
            .projectHash(hashProjectId(event.getProjectId()))  // 项目ID哈希化
            .filePathHash(hashFilePath(event.getFilePath()))   // 文件路径哈希化
            .changeType(event.getChangeType())
            .diffContent(sanitizeDiffContent(event.getDiffContent()))  // 代码内容脱敏
            .timestamp(event.getTimestamp())
            .build();
    }

    private String sanitizeDiffContent(String diffContent) {
        // 移除敏感信息：密码、密钥、个人信息等
        return diffContent
            .replaceAll("password\\s*=\\s*[\"'][^\"']*[\"']", "password=\"***\"")
            .replaceAll("token\\s*=\\s*[\"'][^\"']*[\"']", "token=\"***\"")
            .replaceAll("key\\s*=\\s*[\"'][^\"']*[\"']", "key=\"***\"")
            .replaceAll("\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "***@***.***");
    }
}
```

#### 5.2.2 批量处理和数据清洗

```java
@Component
@Scheduled
public class BatchDataProcessor {

    private final RecentChangesStorageService storageService;
    private final DataQualityService qualityService;

    // 每小时执行批量数据清洗
    @Scheduled(cron = "0 0 * * * *")
    public void performHourlyDataCleaning() {
        log.info("Starting hourly data cleaning...");

        try {
            // 1. 清理重复数据
            int duplicatesRemoved = removeDuplicateChanges();
            log.info("Removed {} duplicate changes", duplicatesRemoved);

            // 2. 数据质量检查
            DataQualityReport report = qualityService.generateQualityReport();
            log.info("Data quality report: {}", report);

            // 3. 清理过期数据
            int expiredRemoved = removeExpiredData();
            log.info("Removed {} expired records", expiredRemoved);

            // 4. 更新统计信息
            updateDatabaseStatistics();

        } catch (Exception e) {
            log.error("Error during hourly data cleaning", e);
        }
    }

    // 每天执行数据聚合
    @Scheduled(cron = "0 2 0 * * *")
    public void performDailyAggregation() {
        log.info("Starting daily data aggregation...");

        try {
            LocalDate yesterday = LocalDate.now().minusDays(1);

            // 1. 聚合采纳率指标
            aggregateAdoptionMetrics(yesterday);

            // 2. 聚合用户行为指标
            aggregateUserBehaviorMetrics(yesterday);

            // 3. 聚合代码质量指标
            aggregateCodeQualityMetrics(yesterday);

            // 4. 生成日报
            generateDailyReport(yesterday);

        } catch (Exception e) {
            log.error("Error during daily aggregation", e);
        }
    }

    private int removeDuplicateChanges() {
        String sql = """
            DELETE rc1 FROM recent_changes rc1
            INNER JOIN recent_changes rc2
            WHERE rc1.id > rc2.id
            AND rc1.diff_content_hash = rc2.diff_content_hash
            AND rc1.file_id = rc2.file_id
            AND ABS(TIMESTAMPDIFF(SECOND, rc1.created_at, rc2.created_at)) < 300
            """;

        try (Connection conn = storageService.getWriteConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            return stmt.executeUpdate();
        } catch (SQLException e) {
            log.error("Failed to remove duplicate changes", e);
            return 0;
        }
    }

    private void aggregateAdoptionMetrics(LocalDate date) {
        String sql = """
            INSERT INTO daily_adoption_metrics
            (date, experiment_group, total_sessions, accepted_sessions,
             avg_adoption_ratio, avg_generation_time, compilation_success_rate)
            SELECT
                DATE(created_at) as date,
                experiment_group,
                COUNT(*) as total_sessions,
                SUM(CASE WHEN adoption_status = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted_sessions,
                AVG(adoption_ratio) as avg_adoption_ratio,
                AVG(generation_time_ms) as avg_generation_time,
                AVG(CASE WHEN compilation_success = 1 THEN 1.0 ELSE 0.0 END) as compilation_success_rate
            FROM inline_edit_sessions
            WHERE DATE(created_at) = ?
            GROUP BY DATE(created_at), experiment_group
            ON DUPLICATE KEY UPDATE
                total_sessions = VALUES(total_sessions),
                accepted_sessions = VALUES(accepted_sessions),
                avg_adoption_ratio = VALUES(avg_adoption_ratio),
                avg_generation_time = VALUES(avg_generation_time),
                compilation_success_rate = VALUES(compilation_success_rate)
            """;

        try (Connection conn = storageService.getWriteConnection();
             PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setDate(1, Date.valueOf(date));
            stmt.executeUpdate();
        } catch (SQLException e) {
            log.error("Failed to aggregate adoption metrics for date {}", date, e);
        }
    }
}
```

### 5.3 面向机器学习任务的数据组织

#### 5.3.1 SFT (Supervised Fine-Tuning) 数据格式

```java
@Data
@Builder
public class SFTTrainingExample {
    private String id;                    // 样本唯一标识
    private String instruction;           // 指令模板
    private String input;                 // 输入上下文
    private String output;                // 期望输出
    private Map<String, Object> metadata; // 元数据
}

@Service
public class SFTDataGenerator {

    public List<SFTTrainingExample> generateSFTData(LocalDate startDate, LocalDate endDate) {
        List<SFTTrainingExample> examples = new ArrayList<>();

        // 查询成功的InlineEdit会话
        List<InlineEditSessionEntity> sessions = getSuccessfulSessions(startDate, endDate);

        for (InlineEditSessionEntity session : sessions) {
            try {
                SFTTrainingExample example = buildSFTExample(session);
                if (validateSFTExample(example)) {
                    examples.add(example);
                }
            } catch (Exception e) {
                log.warn("Failed to build SFT example for session {}", session.getSessionId(), e);
            }
        }

        return examples;
    }

    private SFTTrainingExample buildSFTExample(InlineEditSessionEntity session) {
        // 1. 构建指令模板
        String instruction = buildInstructionTemplate();

        // 2. 构建输入上下文
        String input = buildInputContext(session);

        // 3. 使用最终采纳的代码作为期望输出
        String output = session.getFinalCode();

        // 4. 构建元数据
        Map<String, Object> metadata = buildMetadata(session);

        return SFTTrainingExample.builder()
            .id(session.getSessionId())
            .instruction(instruction)
            .input(input)
            .output(output)
            .metadata(metadata)
            .build();
    }

    private String buildInstructionTemplate() {
        return """
            You are an AI coding assistant. Based on the provided code context and recent changes,
            implement the requested feature. Follow the coding patterns shown in recent changes.

            Guidelines:
            1. Analyze the recent changes to understand the development pattern
            2. Maintain consistency with the existing code style
            3. Consider the context above and below the insertion point
            4. Generate clean, compilable code
            """;
    }

    private String buildInputContext(InlineEditSessionEntity session) {
        StringBuilder context = new StringBuilder();

        // 1. 外部类信息
        context.append("Below are some information from external classes imported by current file:\n");
        context.append("```java\n\n```\n\n");

        // 2. 上文代码
        context.append("The context above is:\n");
        context.append("```java\n");
        context.append(session.getContextAbove());
        context.append("\n```\n\n");

        // 3. 下文代码
        context.append("The context below is:\n");
        context.append("```java\n");
        context.append(session.getContextBelow());
        context.append("\n```\n\n");

        // 4. Recent Changes
        if (session.getRecentChangesUsed() != null) {
            context.append(buildRecentChangesSection(session.getRecentChangesUsed()));
        }

        // 5. 功能描述
        context.append("The new feature is ").append(session.getTargetFeature()).append(".\n\n");

        // 6. 代码片段提示
        context.append("And here is the code snippet you are asked to modify:\n");
        context.append("```java\n");
        context.append(extractMethodSignature(session.getGeneratedCode()));
        context.append("\n```\n\n");

        context.append("Please analyze the mission carefully and thoroughly first, ");
        context.append("and then give a definitely runnable code. ");
        context.append("You should put your code between ```java and ```.");

        return context.toString();
    }

    private String buildRecentChangesSection(List<Long> recentChangeIds) {
        StringBuilder rcSection = new StringBuilder();

        rcSection.append("## Recent Changes Context\n");
        rcSection.append("Here are some recent changes that were made to this file to help you understand the development context:\n\n");

        List<RecentChangeEntity> changes = getRecentChangesByIds(recentChangeIds);

        // 按优先级排序 (rc3 -> rc2 -> rc1)
        changes.sort((a, b) -> Integer.compare(b.getChangePriority(), a.getChangePriority()));

        for (int i = 0; i < changes.size(); i++) {
            RecentChangeEntity change = changes.get(i);
            String description = getChangeDescription(changes.size() - i);

            rcSection.append("### Recent Change ").append(changes.size() - i)
                     .append(" (").append(description).append(")\n");
            rcSection.append("```diff\n");
            rcSection.append(change.getDiffContent());
            rcSection.append("\n```\n\n");
        }

        rcSection.append("These recent changes show the development progression leading up to the current task.\n\n");

        return rcSection.toString();
    }

    private Map<String, Object> buildMetadata(InlineEditSessionEntity session) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("session_id", session.getSessionId());
        metadata.put("user_hash", session.getUserHash());
        metadata.put("project_id", session.getProjectId());
        metadata.put("file_id", session.getFileId());
        metadata.put("adoption_status", session.getAdoptionStatus().name());
        metadata.put("adoption_ratio", session.getAdoptionRatio());
        metadata.put("generation_time_ms", session.getGenerationTimeMs());
        metadata.put("compilation_success", session.getCompilationSuccess());
        metadata.put("experiment_group", session.getExperimentGroup().name());
        metadata.put("recent_changes_count", session.getRecentChangesUsed() != null ?
                    session.getRecentChangesUsed().size() : 0);
        metadata.put("created_at", session.getCreatedAt());
        return metadata;
    }
}

// SFT数据导出服务
@Service
public class SFTDataExporter {

    public void exportSFTDataset(LocalDate startDate, LocalDate endDate, String outputPath) {
        List<SFTTrainingExample> examples = sftDataGenerator.generateSFTData(startDate, endDate);

        // 数据质量过滤
        List<SFTTrainingExample> filtered = examples.stream()
            .filter(this::isHighQualityExample)
            .collect(Collectors.toList());

        // 数据集分割
        Collections.shuffle(filtered);
        int trainSize = (int) (filtered.size() * 0.8);
        int validSize = (int) (filtered.size() * 0.1);

        List<SFTTrainingExample> trainSet = filtered.subList(0, trainSize);
        List<SFTTrainingExample> validSet = filtered.subList(trainSize, trainSize + validSize);
        List<SFTTrainingExample> testSet = filtered.subList(trainSize + validSize, filtered.size());

        // 导出为JSONL格式
        exportToJsonl(trainSet, outputPath + "/train.jsonl");
        exportToJsonl(validSet, outputPath + "/valid.jsonl");
        exportToJsonl(testSet, outputPath + "/test.jsonl");

        // 生成数据集统计报告
        generateDatasetReport(trainSet, validSet, testSet, outputPath + "/dataset_report.json");
    }

    private boolean isHighQualityExample(SFTTrainingExample example) {
        Map<String, Object> metadata = example.getMetadata();

        // 质量过滤条件
        return "ACCEPTED".equals(metadata.get("adoption_status")) &&
               (Double) metadata.get("adoption_ratio") >= 0.8 &&
               (Boolean) metadata.get("compilation_success") &&
               example.getOutput().length() >= 50 &&
               example.getOutput().length() <= 2000;
    }
}
```

#### 5.3.2 RL (Reinforcement Learning) 数据格式

```java
@Data
@Builder
public class RLTrainingExample {
    private String id;                    // 样本唯一标识
    private String state;                 // 状态（上下文）
    private String action;                // 动作（生成的代码）
    private double reward;                // 奖励信号
    private String nextState;             // 下一状态
    private boolean done;                 // 是否结束
    private Map<String, Object> metadata; // 元数据
}

@Service
public class RLDataGenerator {

    public List<RLTrainingExample> generateRLData(LocalDate startDate, LocalDate endDate) {
        List<RLTrainingExample> examples = new ArrayList<>();

        // 获取所有会话数据（包括成功和失败的）
        List<InlineEditSessionEntity> sessions = getAllSessions(startDate, endDate);

        for (InlineEditSessionEntity session : sessions) {
            try {
                RLTrainingExample example = buildRLExample(session);
                examples.add(example);
            } catch (Exception e) {
                log.warn("Failed to build RL example for session {}", session.getSessionId(), e);
            }
        }

        return examples;
    }

    private RLTrainingExample buildRLExample(InlineEditSessionEntity session) {
        // 1. 构建状态（上下文信息）
        String state = buildStateRepresentation(session);

        // 2. 动作就是生成的代码
        String action = session.getGeneratedCode();

        // 3. 计算奖励信号
        double reward = calculateReward(session);

        // 4. 下一状态（采纳后的状态）
        String nextState = buildNextStateRepresentation(session);

        // 5. 判断是否结束
        boolean done = session.getAdoptionStatus() != AdoptionStatus.PARTIAL;

        return RLTrainingExample.builder()
            .id(session.getSessionId())
            .state(state)
            .action(action)
            .reward(reward)
            .nextState(nextState)
            .done(done)
            .metadata(buildRLMetadata(session))
            .build();
    }

    private double calculateReward(InlineEditSessionEntity session) {
        double reward = 0.0;

        // 基础奖励：基于采纳状态
        switch (session.getAdoptionStatus()) {
            case ACCEPTED:
                reward += 1.0;
                break;
            case MODIFIED:
                reward += 0.5 + 0.3 * session.getAdoptionRatio();
                break;
            case PARTIAL:
                reward += 0.3 * session.getAdoptionRatio();
                break;
            case REJECTED:
                reward -= 0.5;
                break;
        }

        // 编译成功奖励
        if (session.getCompilationSuccess()) {
            reward += 0.3;
        } else {
            reward -= 0.3;
        }

        // 运行时错误惩罚
        if (session.getRuntimeError()) {
            reward -= 0.2;
        }

        // 生成时间惩罚（鼓励快速生成）
        if (session.getGenerationTimeMs() != null) {
            double timePenalty = Math.min(0.1, session.getGenerationTimeMs() / 10000.0);
            reward -= timePenalty;
        }

        // Recent Changes使用奖励
        if (session.getRecentChangesUsed() != null && !session.getRecentChangesUsed().isEmpty()) {
            reward += 0.1;
        }

        return Math.max(-1.0, Math.min(1.0, reward)); // 限制在[-1, 1]范围内
    }

    private String buildStateRepresentation(InlineEditSessionEntity session) {
        Map<String, Object> state = new HashMap<>();
        state.put("context_above", session.getContextAbove());
        state.put("context_below", session.getContextBelow());
        state.put("target_feature", session.getTargetFeature());
        state.put("recent_changes_used", session.getRecentChangesUsed());
        state.put("caret_position", session.getCaretPosition());

        return JsonUtils.toJson(state);
    }

    private String buildNextStateRepresentation(InlineEditSessionEntity session) {
        Map<String, Object> nextState = new HashMap<>();
        nextState.put("final_code", session.getFinalCode());
        nextState.put("adoption_status", session.getAdoptionStatus().name());
        nextState.put("compilation_success", session.getCompilationSuccess());
        nextState.put("runtime_error", session.getRuntimeError());

        return JsonUtils.toJson(nextState);
    }
}
```

#### 5.3.3 Next Prediction 数据格式

```java
@Data
@Builder
public class NextPredictionExample {
    private String id;                    // 样本唯一标识
    private List<String> inputTokens;     // 输入token序列
    private List<String> targetTokens;    // 目标token序列
    private int windowSize;               // 滑动窗口大小
    private Map<String, Object> metadata; // 元数据
}

@Service
public class NextPredictionDataGenerator {

    private final CodeTokenizer tokenizer;
    private static final int DEFAULT_WINDOW_SIZE = 512;
    private static final int PREDICTION_LENGTH = 128;

    public List<NextPredictionExample> generateNextPredictionData(
            LocalDate startDate, LocalDate endDate) {
        List<NextPredictionExample> examples = new ArrayList<>();

        // 获取所有成功的代码生成会话
        List<InlineEditSessionEntity> sessions = getSuccessfulSessions(startDate, endDate);

        for (InlineEditSessionEntity session : sessions) {
            try {
                List<NextPredictionExample> sessionExamples =
                    buildNextPredictionExamples(session);
                examples.addAll(sessionExamples);
            } catch (Exception e) {
                log.warn("Failed to build next prediction examples for session {}",
                        session.getSessionId(), e);
            }
        }

        return examples;
    }

    private List<NextPredictionExample> buildNextPredictionExamples(
            InlineEditSessionEntity session) {
        List<NextPredictionExample> examples = new ArrayList<>();

        // 1. 构建完整的代码上下文
        String fullContext = buildFullCodeContext(session);

        // 2. 对代码进行tokenization
        List<String> tokens = tokenizer.tokenize(fullContext);

        // 3. 使用滑动窗口生成训练样本
        for (int i = 0; i <= tokens.size() - DEFAULT_WINDOW_SIZE - PREDICTION_LENGTH; i++) {
            List<String> inputTokens = tokens.subList(i, i + DEFAULT_WINDOW_SIZE);
            List<String> targetTokens = tokens.subList(
                i + DEFAULT_WINDOW_SIZE,
                Math.min(i + DEFAULT_WINDOW_SIZE + PREDICTION_LENGTH, tokens.size())
            );

            if (targetTokens.size() >= 10) { // 确保有足够的目标tokens
                NextPredictionExample example = NextPredictionExample.builder()
                    .id(session.getSessionId() + "_" + i)
                    .inputTokens(new ArrayList<>(inputTokens))
                    .targetTokens(new ArrayList<>(targetTokens))
                    .windowSize(DEFAULT_WINDOW_SIZE)
                    .metadata(buildNextPredictionMetadata(session, i))
                    .build();

                examples.add(example);
            }
        }

        return examples;
    }

    private String buildFullCodeContext(InlineEditSessionEntity session) {
        StringBuilder context = new StringBuilder();

        // 1. 上文代码
        if (session.getContextAbove() != null) {
            context.append(session.getContextAbove()).append("\n");
        }

        // 2. 生成的代码
        if (session.getFinalCode() != null) {
            context.append(session.getFinalCode()).append("\n");
        }

        // 3. 下文代码
        if (session.getContextBelow() != null) {
            context.append(session.getContextBelow());
        }

        return context.toString();
    }

    private Map<String, Object> buildNextPredictionMetadata(
            InlineEditSessionEntity session, int windowIndex) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("session_id", session.getSessionId());
        metadata.put("window_index", windowIndex);
        metadata.put("user_hash", session.getUserHash());
        metadata.put("project_id", session.getProjectId());
        metadata.put("file_id", session.getFileId());
        metadata.put("has_recent_changes",
                    session.getRecentChangesUsed() != null &&
                    !session.getRecentChangesUsed().isEmpty());
        metadata.put("adoption_ratio", session.getAdoptionRatio());
        metadata.put("created_at", session.getCreatedAt());
        return metadata;
    }
}

@Component
public class CodeTokenizer {

    private final Pattern tokenPattern = Pattern.compile(
        "\\b\\w+\\b|[{}();,.]|\\s+|\\n|\\r\\n"
    );

    public List<String> tokenize(String code) {
        List<String> tokens = new ArrayList<>();
        Matcher matcher = tokenPattern.matcher(code);

        while (matcher.find()) {
            String token = matcher.group();
            if (!token.trim().isEmpty()) {
                tokens.add(token);
            }
        }

        return tokens;
    }

    public String detokenize(List<String> tokens) {
        return String.join("", tokens);
    }
}
```

### 5.4 数据质量保证机制

#### 5.4.1 数据验证规则

```java
@Service
public class DataValidationService {

    private static final int MAX_DIFF_SIZE = 10000;
    private static final int MAX_CONTEXT_SIZE = 50000;
    private static final Pattern JAVA_CODE_PATTERN =
        Pattern.compile(".*\\b(class|interface|enum|public|private|protected)\\b.*");

    public ValidationResult validateRawEvent(RawChangeEvent event) {
        ValidationResult result = new ValidationResult();

        // 1. 基础字段验证
        if (StringUtils.isBlank(event.getSessionId())) {
            result.addError("Session ID cannot be blank");
        }

        if (event.getTimestamp() == null ||
            event.getTimestamp().after(new Date(System.currentTimeMillis() + 60000))) {
            result.addError("Invalid timestamp");
        }

        // 2. 文件路径验证
        if (StringUtils.isBlank(event.getFilePath()) ||
            !event.getFilePath().endsWith(".java")) {
            result.addError("Invalid Java file path");
        }

        // 3. Diff内容验证
        if (StringUtils.isNotBlank(event.getDiffContent())) {
            if (event.getDiffContent().length() > MAX_DIFF_SIZE) {
                result.addError("Diff content too large");
            }

            if (!isValidDiffFormat(event.getDiffContent())) {
                result.addError("Invalid diff format");
            }
        }

        // 4. 代码内容验证
        if (StringUtils.isNotBlank(event.getContextBefore()) &&
            event.getContextBefore().length() > MAX_CONTEXT_SIZE) {
            result.addError("Context before too large");
        }

        if (StringUtils.isNotBlank(event.getContextAfter()) &&
            event.getContextAfter().length() > MAX_CONTEXT_SIZE) {
            result.addError("Context after too large");
        }

        return result;
    }

    public ValidationResult validateSessionEvent(SessionEvent event) {
        ValidationResult result = new ValidationResult();

        // 1. 会话基础信息验证
        if (StringUtils.isBlank(event.getSessionId())) {
            result.addError("Session ID cannot be blank");
        }

        if (event.getAdoptionStatus() == null) {
            result.addError("Adoption status cannot be null");
        }

        // 2. 代码质量验证
        if (StringUtils.isNotBlank(event.getGeneratedCode())) {
            if (!isValidJavaCode(event.getGeneratedCode())) {
                result.addWarning("Generated code may not be valid Java");
            }
        }

        if (StringUtils.isNotBlank(event.getFinalCode())) {
            if (!isValidJavaCode(event.getFinalCode())) {
                result.addWarning("Final code may not be valid Java");
            }
        }

        // 3. 指标合理性验证
        if (event.getAdoptionRatio() != null &&
            (event.getAdoptionRatio() < 0.0 || event.getAdoptionRatio() > 1.0)) {
            result.addError("Adoption ratio must be between 0.0 and 1.0");
        }

        if (event.getGenerationTimeMs() != null && event.getGenerationTimeMs() < 0) {
            result.addError("Generation time cannot be negative");
        }

        return result;
    }

    private boolean isValidDiffFormat(String diffContent) {
        // 检查是否包含标准diff格式的标记
        return diffContent.contains("@@") &&
               (diffContent.contains("+") || diffContent.contains("-"));
    }

    private boolean isValidJavaCode(String code) {
        // 简单的Java代码格式检查
        return JAVA_CODE_PATTERN.matcher(code).find() ||
               code.contains("{") || code.contains("}") ||
               code.contains(";");
    }
}

@Data
public class ValidationResult {
    private boolean valid = true;
    private List<String> errors = new ArrayList<>();
    private List<String> warnings = new ArrayList<>();

    public void addError(String error) {
        this.errors.add(error);
        this.valid = false;
    }

    public void addWarning(String warning) {
        this.warnings.add(warning);
    }
}
```

#### 5.4.2 数据质量评估

```java
@Service
public class DataQualityService {

    public DataQualityReport generateQualityReport() {
        return DataQualityReport.builder()
            .completenessScore(calculateCompletenessScore())
            .accuracyScore(calculateAccuracyScore())
            .consistencyScore(calculateConsistencyScore())
            .timelinessScore(calculateTimelinessScore())
            .duplicateRate(calculateDuplicateRate())
            .errorRate(calculateErrorRate())
            .generatedAt(LocalDateTime.now())
            .build();
    }

    private double calculateCompletenessScore() {
        String sql = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN diff_content IS NOT NULL AND diff_content != '' THEN 1 ELSE 0 END) as with_diff,
                SUM(CASE WHEN context_before IS NOT NULL AND context_before != '' THEN 1 ELSE 0 END) as with_context_before,
                SUM(CASE WHEN context_after IS NOT NULL AND context_after != '' THEN 1 ELSE 0 END) as with_context_after
            FROM recent_changes
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """;

        try (Connection conn = getReadConnection();
             PreparedStatement stmt = conn.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {

            if (rs.next()) {
                int total = rs.getInt("total");
                if (total == 0) return 1.0;

                double diffCompleteness = (double) rs.getInt("with_diff") / total;
                double contextBeforeCompleteness = (double) rs.getInt("with_context_before") / total;
                double contextAfterCompleteness = (double) rs.getInt("with_context_after") / total;

                return (diffCompleteness + contextBeforeCompleteness + contextAfterCompleteness) / 3.0;
            }
        } catch (SQLException e) {
            log.error("Failed to calculate completeness score", e);
        }

        return 0.0;
    }

    private double calculateAccuracyScore() {
        // 基于编译成功率和运行时错误率计算准确性
        String sql = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN compilation_success = 1 THEN 1 ELSE 0 END) as compilation_success,
                SUM(CASE WHEN runtime_error = 0 THEN 1 ELSE 0 END) as no_runtime_error
            FROM inline_edit_sessions
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """;

        try (Connection conn = getReadConnection();
             PreparedStatement stmt = conn.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {

            if (rs.next()) {
                int total = rs.getInt("total");
                if (total == 0) return 1.0;

                double compilationRate = (double) rs.getInt("compilation_success") / total;
                double noErrorRate = (double) rs.getInt("no_runtime_error") / total;

                return (compilationRate + noErrorRate) / 2.0;
            }
        } catch (SQLException e) {
            log.error("Failed to calculate accuracy score", e);
        }

        return 0.0;
    }

    private double calculateDuplicateRate() {
        String sql = """
            SELECT
                COUNT(*) as total,
                COUNT(*) - COUNT(DISTINCT diff_content_hash) as duplicates
            FROM recent_changes
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """;

        try (Connection conn = getReadConnection();
             PreparedStatement stmt = conn.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {

            if (rs.next()) {
                int total = rs.getInt("total");
                int duplicates = rs.getInt("duplicates");

                return total > 0 ? (double) duplicates / total : 0.0;
            }
        } catch (SQLException e) {
            log.error("Failed to calculate duplicate rate", e);
        }

        return 0.0;
    }
}

@Data
@Builder
public class DataQualityReport {
    private double completenessScore;     // 完整性评分 [0-1]
    private double accuracyScore;         // 准确性评分 [0-1]
    private double consistencyScore;      // 一致性评分 [0-1]
    private double timelinessScore;       // 时效性评分 [0-1]
    private double duplicateRate;         // 重复率 [0-1]
    private double errorRate;             // 错误率 [0-1]
    private LocalDateTime generatedAt;    // 报告生成时间

    public double getOverallScore() {
        return (completenessScore + accuracyScore + consistencyScore + timelinessScore) / 4.0;
    }
}
```

### 5.5 隐私和合规考虑

#### 5.5.1 代码内容脱敏处理

```java
@Component
public class CodeSanitizer {

    private static final List<Pattern> SENSITIVE_PATTERNS = Arrays.asList(
        // 密码和密钥
        Pattern.compile("(password|pwd|pass)\\s*[=:]\\s*[\"'][^\"']*[\"']", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(token|key|secret)\\s*[=:]\\s*[\"'][^\"']*[\"']", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(api[_-]?key|access[_-]?key)\\s*[=:]\\s*[\"'][^\"']*[\"']", Pattern.CASE_INSENSITIVE),

        // 数据库连接字符串
        Pattern.compile("jdbc:[^\\s;]+", Pattern.CASE_INSENSITIVE),
        Pattern.compile("mongodb://[^\\s;]+", Pattern.CASE_INSENSITIVE),

        // 邮箱地址
        Pattern.compile("\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"),

        // IP地址
        Pattern.compile("\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b"),

        // 电话号码
        Pattern.compile("\\b(?:\\+?86)?1[3-9]\\d{9}\\b"),

        // 身份证号
        Pattern.compile("\\b[1-9]\\d{5}(18|19|20)\\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\\d|3[01])\\d{3}[\\dXx]\\b")
    );

    private static final Map<Pattern, String> REPLACEMENT_MAP = Map.of(
        SENSITIVE_PATTERNS.get(0), "$1=\"***\"",
        SENSITIVE_PATTERNS.get(1), "$1=\"***\"",
        SENSITIVE_PATTERNS.get(2), "$1=\"***\"",
        SENSITIVE_PATTERNS.get(3), "jdbc:***",
        SENSITIVE_PATTERNS.get(4), "mongodb://***",
        SENSITIVE_PATTERNS.get(5), "***@***.***",
        SENSITIVE_PATTERNS.get(6), "***.***.***.***",
        SENSITIVE_PATTERNS.get(7), "***********",
        SENSITIVE_PATTERNS.get(8), "******************"
    );

    public String sanitizeCode(String code) {
        if (StringUtils.isBlank(code)) {
            return code;
        }

        String sanitized = code;

        // 应用所有脱敏规则
        for (Map.Entry<Pattern, String> entry : REPLACEMENT_MAP.entrySet()) {
            sanitized = entry.getKey().matcher(sanitized)
                           .replaceAll(entry.getValue());
        }

        // 移除注释中的敏感信息
        sanitized = sanitizeComments(sanitized);

        // 移除字符串字面量中的敏感信息
        sanitized = sanitizeStringLiterals(sanitized);

        return sanitized;
    }

    private String sanitizeComments(String code) {
        // 处理单行注释
        Pattern singleLineComment = Pattern.compile("//.*$", Pattern.MULTILINE);
        code = singleLineComment.matcher(code).replaceAll(match -> {
            String comment = match.group();
            return sanitizeText(comment);
        });

        // 处理多行注释
        Pattern multiLineComment = Pattern.compile("/\\*.*?\\*/", Pattern.DOTALL);
        code = multiLineComment.matcher(code).replaceAll(match -> {
            String comment = match.group();
            return sanitizeText(comment);
        });

        return code;
    }

    private String sanitizeStringLiterals(String code) {
        Pattern stringLiteral = Pattern.compile("\"([^\"\\\\]|\\\\.)*\"");
        return stringLiteral.matcher(code).replaceAll(match -> {
            String literal = match.group();
            String content = literal.substring(1, literal.length() - 1);
            String sanitized = sanitizeText(content);
            return "\"" + sanitized + "\"";
        });
    }

    private String sanitizeText(String text) {
        String sanitized = text;
        for (Map.Entry<Pattern, String> entry : REPLACEMENT_MAP.entrySet()) {
            sanitized = entry.getKey().matcher(sanitized)
                           .replaceAll(entry.getValue());
        }
        return sanitized;
    }
}
```

#### 5.5.2 用户同意和权限管理

```java
@Entity
@Table(name = "user_consents")
@Data
public class UserConsentEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_hash", nullable = false)
    private String userHash;

    @Enumerated(EnumType.STRING)
    @Column(name = "consent_type", nullable = false)
    private ConsentType consentType;

    @Column(name = "granted", nullable = false)
    private Boolean granted;

    @Column(name = "granted_at")
    private LocalDateTime grantedAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "version")
    private String version; // 隐私政策版本

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}

public enum ConsentType {
    METRICS_COLLECTION,      // 指标收集
    CODE_ANALYSIS,          // 代码分析
    ML_TRAINING,            // 机器学习训练
    PERFORMANCE_MONITORING, // 性能监控
    RESEARCH_PARTICIPATION  // 研究参与
}

@Service
public class UserConsentService {

    @Autowired
    private UserConsentRepository consentRepository;

    public boolean hasConsent(String userId, ConsentType consentType) {
        String userHash = hashUserId(userId);

        Optional<UserConsentEntity> consent = consentRepository
            .findByUserHashAndConsentTypeAndGrantedTrue(userHash, consentType);

        if (consent.isEmpty()) {
            return false;
        }

        UserConsentEntity entity = consent.get();

        // 检查是否过期
        if (entity.getExpiresAt() != null &&
            entity.getExpiresAt().isBefore(LocalDateTime.now())) {
            return false;
        }

        return true;
    }

    public void grantConsent(String userId, ConsentType consentType,
                           String policyVersion, Duration validity) {
        String userHash = hashUserId(userId);

        // 撤销之前的同意
        revokeConsent(userId, consentType);

        // 创建新的同意记录
        UserConsentEntity consent = new UserConsentEntity();
        consent.setUserHash(userHash);
        consent.setConsentType(consentType);
        consent.setGranted(true);
        consent.setGrantedAt(LocalDateTime.now());
        consent.setExpiresAt(validity != null ?
                           LocalDateTime.now().plus(validity) : null);
        consent.setVersion(policyVersion);
        consent.setCreatedAt(LocalDateTime.now());
        consent.setUpdatedAt(LocalDateTime.now());

        consentRepository.save(consent);

        log.info("User consent granted: userHash={}, type={}, version={}",
                userHash, consentType, policyVersion);
    }

    public void revokeConsent(String userId, ConsentType consentType) {
        String userHash = hashUserId(userId);

        List<UserConsentEntity> consents = consentRepository
            .findByUserHashAndConsentType(userHash, consentType);

        for (UserConsentEntity consent : consents) {
            consent.setGranted(false);
            consent.setUpdatedAt(LocalDateTime.now());
        }

        consentRepository.saveAll(consents);

        log.info("User consent revoked: userHash={}, type={}", userHash, consentType);
    }

    private String hashUserId(String userId) {
        return DigestUtils.sha256Hex(userId + SALT);
    }
}
```

#### 5.5.3 GDPR合规处理

```java
@Service
public class GDPRComplianceService {

    @Autowired
    private UserConsentService consentService;
    @Autowired
    private DataDeletionService deletionService;

    // 数据主体访问权（Right of Access）
    public UserDataExport exportUserData(String userId) {
        if (!consentService.hasConsent(userId, ConsentType.METRICS_COLLECTION)) {
            throw new UnauthorizedException("User has not consented to data collection");
        }

        String userHash = hashUserId(userId);

        return UserDataExport.builder()
            .userHash(userHash)
            .sessions(getSessionData(userHash))
            .consents(getConsentData(userHash))
            .metrics(getMetricsData(userHash))
            .exportedAt(LocalDateTime.now())
            .build();
    }

    // 被遗忘权（Right to be Forgotten）
    public void deleteUserData(String userId, String reason) {
        String userHash = hashUserId(userId);

        log.info("Starting GDPR data deletion for user: {}, reason: {}", userHash, reason);

        try {
            // 1. 删除会话数据
            deletionService.deleteSessionData(userHash);

            // 2. 删除指标数据
            deletionService.deleteMetricsData(userHash);

            // 3. 删除同意记录
            deletionService.deleteConsentData(userHash);

            // 4. 清理缓存
            deletionService.clearUserCache(userHash);

            // 5. 记录删除日志
            recordDeletionLog(userHash, reason);

            log.info("GDPR data deletion completed for user: {}", userHash);

        } catch (Exception e) {
            log.error("Failed to delete user data: {}", userHash, e);
            throw new DataDeletionException("Failed to delete user data", e);
        }
    }

    // 数据可携带权（Right to Data Portability）
    public byte[] exportUserDataAsJson(String userId) {
        UserDataExport export = exportUserData(userId);

        try {
            ObjectMapper mapper = new ObjectMapper();
            mapper.registerModule(new JavaTimeModule());
            return mapper.writeValueAsBytes(export);
        } catch (Exception e) {
            throw new DataExportException("Failed to export user data as JSON", e);
        }
    }

    // 数据处理限制权（Right to Restrict Processing）
    public void restrictDataProcessing(String userId, String reason) {
        String userHash = hashUserId(userId);

        // 标记用户数据为受限处理
        DataProcessingRestriction restriction = new DataProcessingRestriction();
        restriction.setUserHash(userHash);
        restriction.setReason(reason);
        restriction.setRestrictedAt(LocalDateTime.now());
        restriction.setActive(true);

        restrictionRepository.save(restriction);

        log.info("Data processing restricted for user: {}, reason: {}", userHash, reason);
    }

    // 检查数据处理是否受限
    public boolean isDataProcessingRestricted(String userId) {
        String userHash = hashUserId(userId);

        return restrictionRepository
            .findByUserHashAndActiveTrue(userHash)
            .isPresent();
    }

    private void recordDeletionLog(String userHash, String reason) {
        DataDeletionLog log = new DataDeletionLog();
        log.setUserHash(userHash);
        log.setReason(reason);
        log.setDeletedAt(LocalDateTime.now());
        log.setDeletedBy("GDPR_COMPLIANCE_SERVICE");

        deletionLogRepository.save(log);
    }
}

@Data
@Builder
public class UserDataExport {
    private String userHash;
    private List<SessionDataExport> sessions;
    private List<ConsentDataExport> consents;
    private List<MetricsDataExport> metrics;
    private LocalDateTime exportedAt;
}
```

## 6. 实施计划

### 6.1 开发阶段
1. **Phase 1**: JGit集成和基础变更检测 (2周)
2. **Phase 2**: IDEA插件开发和UI集成 (3周)
3. **Phase 3**: Recent Changes格式化和上下文构建 (2周)
4. **Phase 4**: 数据存储和收集管道 (3周)
5. **Phase 5**: 机器学习数据格式和导出 (2周)
6. **Phase 6**: 打点系统和A/B测试框架 (2周)
7. **Phase 7**: 隐私合规和数据质量保证 (2周)
8. **Phase 8**: 测试和优化 (2周)

### 6.2 风险控制
- **性能风险**: 异步处理Git操作，避免阻塞UI
- **兼容性风险**: 支持多版本IDEA和Git
- **隐私风险**: 严格的数据脱敏和用户同意机制
- **存储风险**: 分布式存储和备份策略
- **合规风险**: GDPR等法规的完整实现

### 6.3 成功指标
- **采纳率提升**: 目标提升15-25%
- **生成质量**: 编译成功率提升10%
- **用户满意度**: NPS评分提升20%
- **数据质量**: 整体质量评分>0.9
- **合规性**: 100%符合GDPR要求
```
