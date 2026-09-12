const translations = new Map([
  ["CONTENTFLOW AI · DESIGN FOUNDATIONS", "CONTENTFLOW AI · 设计基础"],
  ["Editorial clarity\nfor AI workflows.", "让 AI 工作流\n清晰可控"],
  ["A restrained system for focused writing, visible progress, and trustworthy AI output.", "一套面向专注写作、过程可见与结果可信的克制型设计系统。"],
  ["01 / Color", "01 / 色彩"],
  ["Canvas", "画布"],
  ["Surface", "界面层"],
  ["Ink", "主文字"],
  ["Muted", "次要文字"],
  ["Border", "边框"],
  ["Accent", "强调色"],
  ["Strong", "强调深色"],
  ["Soft", "强调浅色"],
  ["Warning", "警告"],
  ["Error", "异常"],
  ["02 / Typography", "02 / 排版"],
  ["Human direction. AI momentum.", "人来把握方向，AI 加速执行。"],
  ["From rough thought to ready-to-publish.", "从模糊想法到可发布内容。"],
  ["Your workflow, made visible.", "让每一步工作都清晰可见。"],
  ["Content brief", "内容简报"],
  ["Create structured, reviewable content without losing your voice.", "生成结构清晰、可审核，同时保持品牌语气的内容。"],
  ["Each step keeps the source, decisions, and output connected.", "每一步都将资料、决策与输出保持关联。"],
  ["READY FOR REVIEW", "可以审核"],
  ["Generated 2 minutes ago · Version 3", "生成于 2 分钟前 · 版本 3"],
  ["03 / Spacing & radius", "03 / 间距与圆角"],

  ["CONTENTFLOW AI · COMPONENTS", "CONTENTFLOW AI · 组件"],
  ["Small set. Clear states.", "精简组件，清晰状态。"],
  ["Only the controls required by the four-screen MVP prototype.", "只保留四个 MVP 页面真正需要的控件。"],
  ["01 / Buttons", "01 / 按钮"],
  ["02 / Navigation", "02 / 导航"],
  ["03 / Status badges", "03 / 状态标签"],
  ["04 / Prompt input", "04 / 任务输入"],
  ["05 / Content panel", "05 / 内容面板"],
  ["Start creating", "开始创作"],
  ["Save draft", "保存草稿"],
  ["View history", "查看历史"],
  ["New content", "新建内容"],
  ["History", "历史记录"],
  ["READY", "已就绪"],
  ["AI RUNNING", "AI 运行中"],
  ["NEEDS REVIEW", "待审核"],
  ["FAILED", "失败"],
  ["CONTENT BRIEF", "内容简报"],
  ["Describe what you want to create…", "描述你想创作的内容……"],
  ["Turn this research into a concise product launch article.", "将这些研究资料整理成简洁的产品发布文章。"],
  ["EDITORIAL OUTPUT", "内容输出"],
  ["A clear headline lives here", "这里是一条清晰的标题"],
  ["Structured content, source context, and review controls stay visible in one calm surface.", "在同一界面中查看结构化内容、资料上下文和审核操作。"],

  ["WORKSPACE", "工作空间"],
  ["FREE PLAN · 3 PROJECTS", "免费版 · 3 个项目"],
  ["NEW CONTENT  /  UNTITLED", "新建内容  /  未命名"],
  ["FROM SOURCE TO STORY", "从资料到成稿"],
  ["Turn research into\npublish-ready content.", "将研究资料转化为\n可发布的内容。"],
  ["Set the direction once. ContentFlow organizes the workflow, drafts the article, and keeps every decision reviewable.", "只需明确一次方向，ContentFlow 就能组织工作流、起草文章，并让每个决策都可追溯、可审核。"],
  ["Write a product launch article for a new AI research workspace. Keep the tone clear, credible, and useful for product teams.", "为新的 AI 研究工作空间撰写一篇产品发布文章。语气清晰、可信，并能为产品团队提供实际帮助。"],
  ["+ Add source", "+ 添加资料"],
  ["+ Brand voice", "+ 品牌语气"],
  ["+ Audience", "+ 目标受众"],
  ["Start workflow  →", "开始工作流  →"],
  ["WORKFLOW SETUP", "工作流设置"],
  ["4 focused steps", "4 个专注步骤"],
  ["01  Research", "01  资料研究"],
  ["02  Outline", "02  内容大纲"],
  ["03  Draft", "03  初稿生成"],
  ["04  Review", "04  审核优化"],
  ["EST. 3–5 MIN", "预计 3–5 分钟"],
  ["RECENT DRAFTS", "最近草稿"],
  ["AI workspace launch", "AI 工作空间发布"],
  ["Draft · 12 min ago", "草稿 · 12 分钟前"],
  ["Quarterly product story", "季度产品故事"],
  ["Ready · Yesterday", "已就绪 · 昨天"],
  ["Research trends brief", "研究趋势简报"],
  ["Review · Sep 3", "待审核 · 9 月 3 日"],

  ["←  AI WORKSPACE LAUNCH", "←  AI 工作空间发布"],
  ["Building the story,\nstep by step.", "一步一步，\n完成内容创作。"],
  ["Every stage shows its inputs, decisions, and output before the next one begins.", "每个阶段都会展示输入、处理决策和输出，确认后再进入下一步。"],
  ["Research", "资料研究"],
  ["Outline", "内容大纲"],
  ["Draft", "初稿"],
  ["Review", "审核"],
  ["02 / Shaping the outline", "02 / 整理内容大纲"],
  ["The AI is grouping source evidence into a clear narrative. You can approve, reorder, or rewrite each section before drafting.", "AI 正在将资料证据整理为清晰的叙事结构。生成初稿前，你可以确认、调整顺序或改写每个章节。"],
  ["Why content work breaks across tools", "为什么跨工具创作容易中断"],
  ["One workspace from evidence to draft", "从资料证据到初稿的一体化空间"],
  ["Review without losing context", "在不丢失上下文的情况下审核"],
  ["APPROVED", "已确认"],
  ["GENERATING", "生成中"],
  ["QUEUED", "等待中"],
  ["Pause", "暂停"],
  ["Review outline", "审核大纲"],
  ["INPUT CONTEXT", "输入上下文"],
  ["What the AI can use", "AI 可以使用的内容"],
  ["SOURCES", "资料来源"],
  ["BRAND VOICE", "品牌语气"],
  ["AUDIENCE", "目标受众"],
  ["Sources stay attached to every generated section.", "每个生成章节都会保留对应资料来源。"],

  ["←  WORKFLOW  /  FINAL DRAFT", "←  工作流  /  最终稿"],
  ["A finished draft,\nstill under your control.", "成稿已经完成，\n控制权仍在你手中。"],
  ["Copy", "复制"],
  ["Export  ↗", "导出  ↗"],
  ["H1   H2   B   I   Link   Quote", "H1   H2   B   I   链接   引用"],
  ["842 WORDS", "842 字"],
  ["PRODUCT STORY · 6 MIN READ", "产品故事 · 阅读约 6 分钟"],
  ["One workspace from\nevidence to publish", "一个工作空间，\n从资料到发布"],
  ["Content teams rarely struggle with ideas. They struggle with fractured context—sources in one tab, decisions in another, and drafts somewhere else.", "内容团队通常并不缺少想法，真正的问题是上下文碎片化：资料在一个标签页，决策在另一个地方，初稿又散落在其他工具中。"],
  ["The hidden cost of broken flow", "工作流断裂带来的隐性成本"],
  ["Every handoff creates a small loss of intent. Research becomes detached from the outline, feedback arrives without context, and the final copy becomes harder to verify.", "每次工具切换都会损失一部分创作意图。研究资料与大纲脱节，反馈缺少上下文，最终内容也更难验证。"],
  ["A connected workflow keeps evidence and editorial decisions beside the text they shape.", "连贯的工作流会让资料证据和编辑决策始终跟随它们所影响的内容。"],
  ["SOURCE 03  ·  PRODUCT RESEARCH INTERVIEW", "资料 03  ·  产品研究访谈"],
  ["ContentFlow turns that connection into a visible sequence: collect, structure, draft, review, and publish—without hiding the reasoning between steps.", "ContentFlow 将这种连接变成可见的流程：收集、整理、起草、审核和发布，同时保留步骤之间的判断依据。"],
  ["QUALITY CHECK", "质量检查"],
  ["READY TO PUBLISH", "可以发布"],
  ["Tone match", "语气匹配"],
  ["Source coverage", "资料覆盖"],
  ["Clarity", "表达清晰度"],
  ["One claim needs a stronger source before export.", "有一处陈述需要补充更有力的资料后再导出。"],
  ["Review claim", "审核陈述"],
  ["VERSIONS", "版本记录"],
  ["Current · now", "当前版本 · 刚刚"],
  ["Before review", "审核前"],
  ["First draft", "第一版初稿"],

  ["CONTENT LIBRARY", "内容库"],
  ["+ New content", "+ 新建内容"],
  ["Everything you made,\nstill connected.", "所有创作内容，\n始终保持关联。"],
  ["Return to any brief, source, workflow step, or version without rebuilding context.", "随时返回任意简报、资料、工作流步骤或历史版本，无需重新整理上下文。"],
  ["⌕  Search titles, sources, or topics", "⌕  搜索标题、资料或主题"],
  ["ALL", "全部"],
  ["DRAFTS", "草稿"],
  ["REVIEW", "待审核"],
  ["PROJECTS", "项目"],
  ["IN REVIEW", "审核中"],
  ["CONTENT", "内容"],
  ["STATUS", "状态"],
  ["UPDATED", "更新时间"],
  ["QUALITY", "质量"],
  ["Product story · 3 sources", "产品故事 · 3 份资料"],
  ["12 min ago", "12 分钟前"],
  ["Quarterly product narrative", "季度产品叙事"],
  ["Executive brief · 5 sources", "管理层简报 · 5 份资料"],
  ["Yesterday", "昨天"],
  ["Research trends report", "研究趋势报告"],
  ["Long-form article · 8 sources", "长篇文章 · 8 份资料"],
  ["Sep 3", "9 月 3 日"],
  ["Customer interview synthesis", "客户访谈总结"],
  ["Insights brief · 12 sources", "洞察简报 · 12 份资料"],
  ["Sep 1", "9 月 1 日"],
  ["Developer launch notes", "开发者发布说明"],
  ["Release article · 2 sources", "发布文章 · 2 份资料"],
  ["Aug 29", "8 月 29 日"],
  ["Running", "运行中"],
  ["Ready", "已就绪"]
]);

const preferredFamilies = [
  "Noto Sans SC",
  "Source Han Sans SC",
  "思源黑体",
  "PingFang SC",
  "Microsoft YaHei",
  "微软雅黑"
];

function chooseStyle(styles, preferences) {
  for (const preferred of preferences) {
    if (styles.includes(preferred)) return preferred;
  }
  return styles[0];
}

function desiredWeight(node) {
  const font = node.fontName;
  const style = font !== figma.mixed && font && typeof font.style === "string"
    ? font.style.toLowerCase()
    : "";
  if (style.includes("bold") || style.includes("semibold")) return "bold";
  if (style.includes("medium")) return "medium";
  return "regular";
}

async function main() {
  await figma.loadAllPagesAsync();

  const availableFonts = await figma.listAvailableFontsAsync();
  const stylesByFamily = new Map();
  for (const item of availableFonts) {
    const family = item.fontName.family;
    if (!stylesByFamily.has(family)) stylesByFamily.set(family, []);
    stylesByFamily.get(family).push(item.fontName.style);
  }

  const family = preferredFamilies.find(name => stylesByFamily.has(name));
  if (!family) {
    figma.closePlugin("未找到中文字体。请先安装 Noto Sans SC 或思源黑体，然后重新运行插件。");
    return;
  }

  const familyStyles = stylesByFamily.get(family);
  const regular = chooseStyle(familyStyles, ["Regular", "Normal", "Book"]);
  const medium = chooseStyle(familyStyles, ["Medium", "SemiBold", "Regular", "Normal"]);
  const bold = chooseStyle(familyStyles, ["Bold", "SemiBold", "Medium", "Regular"]);
  const fonts = {
    regular: { family, style: regular },
    medium: { family, style: medium },
    bold: { family, style: bold }
  };

  await Promise.all(Object.values(fonts).map(font => figma.loadFontAsync(font)));

  const textStyles = await figma.getLocalTextStylesAsync();
  for (const style of textStyles) {
    const name = style.name.toLowerCase();
    if (name.includes("display") || name.includes("heading")) {
      style.fontName = fonts.bold;
    } else if (name.includes("title") || name.includes("label")) {
      style.fontName = fonts.medium;
    } else {
      style.fontName = fonts.regular;
    }
  }

  const pageNames = new Map([
    ["00 Foundations", "00 设计基础"],
    ["01 Components", "01 组件"],
    ["02 Screens", "02 产品页面"]
  ]);

  let translated = 0;
  let scanned = 0;
  const remainingEnglish = [];

  for (const page of figma.root.children) {
    if (pageNames.has(page.name)) page.name = pageNames.get(page.name);

    const nodes = page.findAll(node => node.type === "TEXT");
    for (const node of nodes) {
      scanned += 1;
      const next = translations.get(node.characters);
      if (next !== undefined) {
        const weight = desiredWeight(node);
        node.fontName = fonts[weight];
        node.characters = next;
        translated += 1;
      } else if (/[A-Za-z]{3,}/.test(node.characters) && !node.characters.includes("ContentFlow")) {
        remainingEnglish.push(node.characters);
      }
    }
  }

  const screensPage = figma.root.children.find(page => page.name === "02 产品页面");
  if (screensPage) {
    const frameNames = new Map([
      ["Screen / 01 Home", "页面 / 01 新建内容"],
      ["Screen / 02 Workflow", "页面 / 02 工作流"],
      ["Screen / 03 Result", "页面 / 03 内容结果"],
      ["Screen / 04 History", "页面 / 04 历史记录"]
    ]);
    for (const node of screensPage.children) {
      if (frameNames.has(node.name)) node.name = frameNames.get(node.name);
    }
  }

  const uniqueRemaining = [...new Set(remainingEnglish)].slice(0, 8);
  const suffix = uniqueRemaining.length
    ? `；仍有 ${uniqueRemaining.length} 类设计标识保留英文`
    : "";
  figma.closePlugin(`中文化完成：已替换 ${translated}/${scanned} 个文字节点，字体为 ${family}${suffix}`);
}

main().catch(error => {
  figma.closePlugin(`中文化失败：${error.message || error}`);
});
