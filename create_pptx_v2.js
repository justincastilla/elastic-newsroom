const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

const { FaNewspaper, FaRobot, FaSearch, FaEdit, FaUpload, FaCode, FaGithub, FaDatabase, FaPlug, FaUserTie, FaCogs, FaQuestion, FaPencilAlt, FaBolt, FaGlobe, FaFileAlt, FaCheckCircle } = require("react-icons/fa");
const { MdOutlineArchive } = require("react-icons/md");

function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}
async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ── Custom Palette ──────────────────────────────────────────────────
const C = {
  yellow:     "E8CE2A",   // bright yellow (#2)
  darkYellow: "C4AD20",   // darker yellow variant
  charcoal:   "2D3748",   // dark slate for text
  blue:       "5AA5DE",   // medium blue (#5)
  darkTeal:   "3D7FA3",   // steel blue (#6)
  teal:       "6DC3BF",   // teal (#4)
  pink:       "D96BA0",   // rose pink (#1)
  green:      "93B73A",   // lime green (#3)
  // Derived
  nearBlack:  "1A202C",
  darkBg:     "1E2533",
  midGray:    "6B7280",
  lightGray:  "F3F4F6",
  paleBlue:   "E8F2FC",
  paleTeal:   "E6F5F4",
  paleYellow: "FBF8E4",
  palePink:   "FCE8F2",
  paleGreen:  "F0F5E4",
  white:      "FFFFFF",
  codeBg:     "1E1E2E",
  codeHeader: "2A2A3C",
};

async function createPresentation() {
  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Justin Castilla";
  pres.title = "Building an AI Newsroom with Multi-Agent Architecture";

  const icons = {
    newspaper:    await iconToBase64Png(FaNewspaper, "#" + C.yellow),
    newspaperDk:  await iconToBase64Png(FaNewspaper, "#" + C.charcoal),
    robot:        await iconToBase64Png(FaRobot, "#" + C.teal),
    robotDk:      await iconToBase64Png(FaRobot, "#" + C.charcoal),
    search:       await iconToBase64Png(FaSearch, "#" + C.blue),
    searchDk:     await iconToBase64Png(FaSearch, "#" + C.charcoal),
    edit:         await iconToBase64Png(FaEdit, "#" + C.darkTeal),
    editDk:       await iconToBase64Png(FaEdit, "#" + C.charcoal),
    upload:       await iconToBase64Png(FaUpload, "#" + C.darkTeal),
    uploadDk:     await iconToBase64Png(FaUpload, "#" + C.charcoal),
    code:         await iconToBase64Png(FaCode, "#" + C.yellow),
    codeDk:       await iconToBase64Png(FaCode, "#" + C.charcoal),
    github:       await iconToBase64Png(FaGithub, "#" + C.white),
    githubDk:     await iconToBase64Png(FaGithub, "#" + C.charcoal),
    database:     await iconToBase64Png(FaDatabase, "#" + C.teal),
    databaseDk:   await iconToBase64Png(FaDatabase, "#" + C.charcoal),
    databaseWh:   await iconToBase64Png(FaDatabase, "#" + C.white),
    plug:         await iconToBase64Png(FaPlug, "#" + C.charcoal),
    userTie:      await iconToBase64Png(FaUserTie, "#" + C.charcoal),
    cogs:         await iconToBase64Png(FaCogs, "#" + C.charcoal),
    cogsDk:       await iconToBase64Png(FaCogs, "#" + C.yellow),
    question:     await iconToBase64Png(FaQuestion, "#" + C.yellow),
    pencil:       await iconToBase64Png(FaPencilAlt, "#" + C.charcoal),
    bolt:         await iconToBase64Png(FaBolt, "#" + C.yellow),
    boltDk:       await iconToBase64Png(FaBolt, "#" + C.charcoal),
    globe:        await iconToBase64Png(FaGlobe, "#" + C.charcoal),
    file:         await iconToBase64Png(FaFileAlt, "#" + C.charcoal),
    check:        await iconToBase64Png(FaCheckCircle, "#" + C.teal),
    userTieWh:    await iconToBase64Png(FaUserTie, "#" + C.white),
    pencilWh:     await iconToBase64Png(FaPencilAlt, "#" + C.white),
    editWh:       await iconToBase64Png(FaEdit, "#" + C.white),
    searchWh:     await iconToBase64Png(FaSearch, "#" + C.white),
    uploadWh:     await iconToBase64Png(FaUpload, "#" + C.white),
    newspaperWh:  await iconToBase64Png(FaNewspaper, "#" + C.white),
    boltWh:       await iconToBase64Png(FaBolt, "#" + C.white),
  };

  // Font shortcuts
  const F = { body: "Inter", mono: "Roboto Mono" };

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 1 — Title (yellow left panel + dark right)
  // ════════════════════════════════════════════════════════════════════
  let s1 = pres.addSlide();
  s1.background = { color: C.charcoal };
  // Left pink panel
  s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 3.8, h: 5.625, fill: { color: C.pink } });
  // Icon in pink panel
  s1.addImage({ data: icons.newspaperWh, x: 1.4, y: 1.5, w: 1.0, h: 1.0 });
  s1.addText("elastic\nnewsroom", {
    x: 0.4, y: 2.7, w: 3.0, h: 1.2, fontSize: 28, fontFace: F.body,
    color: C.white, bold: true, align: "center", margin: 0
  });
  // Right side content
  s1.addText("Building an\nAI Newsroom", {
    x: 4.3, y: 0.8, w: 5.2, h: 1.4, fontSize: 42, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });
  s1.addText("Multi-Agent Architecture with\nA2A, MCP & Elasticsearch", {
    x: 4.3, y: 2.3, w: 5.2, h: 0.7, fontSize: 18, fontFace: F.body,
    color: C.pink, margin: 0
  });
  // Divider line
  s1.addShape(pres.shapes.LINE, { x: 4.3, y: 3.3, w: 4.0, h: 0, line: { color: C.pink, width: 2 } });
  // GitHub badge
  s1.addImage({ data: icons.github, x: 4.3, y: 3.6, w: 0.3, h: 0.3 });
  s1.addText("View on GitHub", {
    x: 4.7, y: 3.6, w: 3.0, h: 0.3, fontSize: 13, fontFace: F.body,
    color: C.teal, bold: true, valign: "middle", margin: 0
  });
  s1.addText("github.com/elastic/elastic-newsroom", {
    x: 4.3, y: 4.0, w: 4.5, h: 0.3, fontSize: 11, fontFace: F.mono,
    color: C.midGray, margin: 0
  });
  // Author
  s1.addText("Justin Castilla  ·  April 2026", {
    x: 4.3, y: 4.8, w: 5.0, h: 0.3, fontSize: 12, fontFace: F.body,
    color: C.midGray, margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 2 — Agenda (horizontal timeline style)
  // ════════════════════════════════════════════════════════════════════
  let s2 = pres.addSlide();
  s2.background = { color: C.white };
  s2.addText("Agenda", {
    x: 0.6, y: 0.4, w: 8.8, h: 0.6, fontSize: 36, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });
  // Bottom yellow accent
  s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.525, w: 10, h: 0.1, fill: { color: C.yellow } });

  const agenda = [
    { time: "3 min", title: "The Problem", sub: "Why multi-agent?", color: C.pink },
    { time: "4 min", title: "Architecture", sub: "A2A protocol & agents", color: C.yellow },
    { time: "3 min", title: "MCP", sub: "Shared tools", color: C.green },
    { time: "4 min", title: "Elasticsearch", sub: "Index, search, semantics", color: C.teal },
    { time: "3 min", title: "Live Workflow", sub: "Topic → article", color: C.blue },
    { time: "3 min", title: "Code & Lessons", sub: "Walkthrough", color: C.darkTeal },
    { time: "5 min", title: "Q & A", sub: "", color: C.midGray },
  ];

  // Agenda as simple numbered list
  agenda.forEach((item, i) => {
    const y = 1.3 + i * 0.55;
    s2.addText(`${item.title}`, {
      x: 0.6, y: y, w: 5.0, h: 0.3, fontSize: 14, fontFace: F.body,
      color: C.charcoal, bold: true, margin: 0, bullet: { type: "number" }
    });
    if (item.sub) {
      s2.addText(`${item.sub}  ·  ${item.time}`, {
        x: 1.1, y: y + 0.28, w: 5.0, h: 0.22, fontSize: 10, fontFace: F.body,
        color: C.midGray, margin: 0
      });
    } else {
      s2.addText(item.time, {
        x: 1.1, y: y + 0.28, w: 5.0, h: 0.22, fontSize: 10, fontFace: F.body,
        color: C.midGray, margin: 0
      });
    }
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 3 — The Problem (full-width split: top yellow, bottom white)
  // ════════════════════════════════════════════════════════════════════
  let s3 = pres.addSlide();
  s3.background = { color: C.white };
  // Top pink band
  s3.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 2.4, fill: { color: C.pink } });
  s3.addText("The Problem", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.6, fontSize: 36, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });
  s3.addText("Single-LLM chatbots hit quality ceilings. No specialization. Research, writing, and editing are conflated into one step. No traceability of sources or editorial decisions.", {
    x: 0.7, y: 1.0, w: 8.6, h: 1.0, fontSize: 14, fontFace: F.body,
    color: C.white, margin: 0
  });

  // Bottom: solution + stats
  s3.addText("The Solution", {
    x: 0.7, y: 2.7, w: 8.6, h: 0.5, fontSize: 22, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });
  s3.addText("Five specialized AI agents — each with a clear role — coordinated by a News Chief via the A2A protocol.", {
    x: 0.7, y: 3.2, w: 5.5, h: 0.7, fontSize: 13, fontFace: F.body,
    color: C.midGray, margin: 0
  });

  // Stat boxes on the right
  const stats = [
    { num: "5", label: "Agents", bg: C.blue },
    { num: "8", label: "MCP Tools", bg: C.teal },
    { num: "3", label: "Search Modes", bg: C.darkTeal },
  ];
  stats.forEach((s, i) => {
    const x = 6.6 + i * 1.15;
    s3.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.7, w: 1.0, h: 1.2, fill: { color: s.bg }
    });
    s3.addText(s.num, {
      x, y: 2.75, w: 1.0, h: 0.7, fontSize: 30, fontFace: F.body,
      color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    s3.addText(s.label, {
      x, y: 3.45, w: 1.0, h: 0.35, fontSize: 9, fontFace: F.body,
      color: C.white, align: "center", valign: "top", margin: 0
    });
  });

  // Bottom tech banner
  s3.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.4, w: 8.6, h: 0.5, fill: { color: C.charcoal } });
  s3.addText("A2A  ·  FastMCP  ·  Tavily  ·  Elasticsearch  ·  Claude  ·  React", {
    x: 0.9, y: 4.4, w: 8.2, h: 0.5, fontSize: 12, fontFace: F.body,
    color: C.white, align: "center", valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 4 — Tech Stack (icon grid — 3x2 with colored circle icons)
  // ════════════════════════════════════════════════════════════════════
  let s4 = pres.addSlide();
  s4.background = { color: C.lightGray };
  s4.addText("Tech Stack", {
    x: 0.7, y: 0.4, w: 8.6, h: 0.6, fontSize: 36, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });
  s4.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.525, w: 10, h: 0.1, fill: { color: C.yellow } });

  const techStack = [
    { name: "A2A Protocol", desc: "Google's Agent-to-Agent SDK\nJSON-RPC communication", icon: icons.plug, circle: C.palePink, tag: "OSS" },
    { name: "FastMCP", desc: "Model Context Protocol\nShared tool registry", icon: icons.cogs, circle: C.paleGreen, tag: "OSS" },
    { name: "Tavily", desc: "Real-time web search API\nfor research agents", icon: icons.globe, circle: C.paleYellow, tag: "API" },
    { name: "Elasticsearch", desc: "Full-text, semantic &\nhybrid vector search", icon: icons.databaseDk, circle: C.paleTeal, tag: "FREE" },
    { name: "Claude API", desc: "Anthropic's Claude for\ncontent generation", icon: icons.robotDk, circle: C.paleBlue, tag: "API" },
    { name: "React + Starlette", desc: "Frontend UI & async\nPython web framework", icon: icons.codeDk, circle: C.paleYellow, tag: "OSS" },
  ];

  techStack.forEach((t, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const x = 0.7 + col * 3.1;
    const y = 1.3 + row * 2.0;

    // White card
    s4.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.8, h: 1.7, fill: { color: C.white }
    });
    // Colored circle behind icon
    s4.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.3, w: 0.7, h: 0.7, fill: { color: t.circle }
    });
    s4.addImage({ data: t.icon, x: x + 0.32, y: y + 0.42, w: 0.45, h: 0.45 });
    s4.addText(t.name, {
      x: x + 1.05, y: y + 0.2, w: 1.6, h: 0.35, fontSize: 14, fontFace: F.body,
      color: C.charcoal, bold: true, margin: 0
    });
    s4.addText(t.desc, {
      x: x + 1.05, y: y + 0.55, w: 1.6, h: 0.6, fontSize: 10, fontFace: F.body,
      color: C.midGray, margin: 0
    });
    // Tag
    const tagColor = t.tag === "API" ? C.blue : t.tag === "FREE" ? C.darkTeal : C.green;
    s4.addShape(pres.shapes.RECTANGLE, {
      x: x + 1.05, y: y + 1.2, w: 0.5, h: 0.22, fill: { color: tagColor }
    });
    s4.addText(t.tag, {
      x: x + 1.05, y: y + 1.2, w: 0.5, h: 0.22, fontSize: 8, fontFace: F.body,
      color: C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 5 — Architecture (dark bg, agent boxes in a hub-spoke layout)
  // ════════════════════════════════════════════════════════════════════
  let s5 = pres.addSlide();
  s5.background = { color: C.nearBlack };

  s5.addText("Architecture Overview", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.5, fontSize: 32, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });

  // Agent boxes — hub and spoke
  const agentDefs = [
    { name: "News Chief",  port: "8080", icon: icons.userTieWh, x: 3.8, y: 1.1, bg: C.pink, textColor: C.white },
    { name: "Reporter",    port: "8081", icon: icons.pencilWh,  x: 0.7, y: 2.6, bg: C.blue, textColor: C.white },
    { name: "Editor",      port: "8082", icon: icons.editWh,    x: 3.8, y: 2.6, bg: C.green, textColor: C.charcoal },
    { name: "Researcher",  port: "8083", icon: icons.searchWh,  x: 6.9, y: 2.6, bg: C.teal, textColor: C.white },
    { name: "Publisher",   port: "8084", icon: icons.uploadWh,  x: 3.8, y: 4.0, bg: C.darkTeal, textColor: C.white },
  ];

  agentDefs.forEach(a => {
    s5.addShape(pres.shapes.RECTANGLE, {
      x: a.x, y: a.y, w: 2.4, h: 1.0, fill: { color: a.bg }
    });
    s5.addImage({ data: a.icon, x: a.x + 0.15, y: a.y + 0.25, w: 0.45, h: 0.45 });
    s5.addText(a.name, {
      x: a.x + 0.65, y: a.y + 0.12, w: 1.6, h: 0.45, fontSize: 14, fontFace: F.body,
      color: a.textColor, bold: true, valign: "middle", margin: 0
    });
    s5.addText(":" + a.port, {
      x: a.x + 0.65, y: a.y + 0.58, w: 1.0, h: 0.3, fontSize: 10, fontFace: F.mono,
      color: a.textColor === C.charcoal ? C.midGray : C.midGray, margin: 0
    });
  });

  // Connection lines
  // Chief down to Editor
  s5.addShape(pres.shapes.LINE, { x: 5.0, y: 2.1, w: 0, h: 0.5, line: { color: C.pink, width: 2 } });
  // Chief down-left to Reporter
  s5.addShape(pres.shapes.LINE, { x: 3.8, y: 1.8, w: -1.7, h: 0.8, line: { color: C.yellow, width: 1.5, dashType: "dash" } });
  // Chief down-right to Researcher
  s5.addShape(pres.shapes.LINE, { x: 6.2, y: 1.8, w: 1.7, h: 0.8, line: { color: C.yellow, width: 1.5, dashType: "dash" } });
  // Researcher to Reporter
  s5.addShape(pres.shapes.LINE, { x: 3.1, y: 3.1, w: 3.8, h: 0, line: { color: C.blue, width: 1.5, dashType: "dash" } });
  // Editor down to Publisher
  s5.addShape(pres.shapes.LINE, { x: 5.0, y: 3.6, w: 0, h: 0.4, line: { color: C.teal, width: 2 } });

  // Services bar
  s5.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 5.15, w: 8.6, h: 0.35, fill: { color: C.darkBg } });
  s5.addText("MCP Server :8095   ·   Event Hub (SSE) :8090   ·   Article API :8085   ·   React UI :3001", {
    x: 0.7, y: 5.15, w: 8.6, h: 0.35, fontSize: 10, fontFace: F.mono,
    color: C.midGray, align: "center", valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 6 — A2A Protocol (two-column: text blocks left, code right)
  // ════════════════════════════════════════════════════════════════════
  let s6 = pres.addSlide();
  s6.background = { color: C.white };
  s6.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.green } });

  s6.addText("A2A Protocol", {
    x: 0.7, y: 0.3, w: 4.0, h: 0.5, fontSize: 32, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });
  s6.addText("Agent-to-Agent Communication", {
    x: 0.7, y: 0.8, w: 4.0, h: 0.3, fontSize: 14, fontFace: F.body,
    color: C.midGray, margin: 0
  });

  // Feature rows
  const a2aFeatures = [
    { title: "Agent Cards", desc: "Self-describing JSON manifests with skills, capabilities, and transport preferences" },
    { title: "JSON-RPC", desc: "Standardized request/response between agents over HTTP" },
    { title: "Task Model", desc: "InMemoryTaskStore tracks state transitions across the workflow" },
    { title: "Discovery", desc: "Agents find each other by fetching /.well-known/agent.json" },
  ];

  a2aFeatures.forEach((f, i) => {
    const y = 1.35 + i * 0.78;
    s6.addText(f.title, {
      x: 0.7, y: y, w: 4.0, h: 0.28, fontSize: 13, fontFace: F.body,
      color: C.charcoal, bold: true, bullet: true, margin: 0
    });
    s6.addText(f.desc, {
      x: 1.1, y: y + 0.3, w: 3.6, h: 0.35, fontSize: 10, fontFace: F.body,
      color: C.midGray, margin: 0
    });
  });

  // Right: code block with terminal-style header
  s6.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 0.3, w: 4.4, h: 0.35, fill: { color: C.codeHeader } });
  s6.addShape(pres.shapes.OVAL, { x: 5.35, y: 0.42, w: 0.12, h: 0.12, fill: { color: "FF5F56" } });
  s6.addShape(pres.shapes.OVAL, { x: 5.55, y: 0.42, w: 0.12, h: 0.12, fill: { color: "FFBD2E" } });
  s6.addShape(pres.shapes.OVAL, { x: 5.75, y: 0.42, w: 0.12, h: 0.12, fill: { color: "27C93F" } });
  s6.addText("agent_card.py", {
    x: 6.0, y: 0.3, w: 3.4, h: 0.35, fontSize: 9, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });

  s6.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 0.65, w: 4.4, h: 3.9, fill: { color: C.codeBg } });

  const a2aCode = `AgentCard(
  name="Reporter",
  url="http://localhost:8081",
  version="1.0.0",
  capabilities=AgentCapabilities(
    streaming=False,
    state_transition_history=True,
    max_concurrent_tasks=20
  ),
  skills=[
    AgentSkill(
      id="write_article",
      name="Write Article",
      tags=["writing", "research"]
    )
  ]
)`;

  s6.addText(a2aCode, {
    x: 5.4, y: 0.8, w: 4.0, h: 3.6, fontSize: 10, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // Repo badge at bottom
  s6.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.85, w: 8.9, h: 0.45, fill: { color: C.charcoal } });
  s6.addImage({ data: icons.github, x: 0.9, y: 4.92, w: 0.28, h: 0.28 });
  s6.addText("A2A SDK — github.com/a2aproject/a2a-python", {
    x: 1.3, y: 4.85, w: 8.0, h: 0.45, fontSize: 11, fontFace: F.body,
    color: C.white, valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 7 — MCP Tools (horizontal cards with top color stripe)
  // ════════════════════════════════════════════════════════════════════
  let s7 = pres.addSlide();
  s7.background = { color: C.lightGray };
  s7.addText("MCP — Model Context Protocol", {
    x: 0.7, y: 0.4, w: 8.6, h: 0.5, fontSize: 30, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });
  s7.addText("A single FastMCP server exposes shared tools that any agent can call.", {
    x: 0.7, y: 0.95, w: 8.6, h: 0.3, fontSize: 13, fontFace: F.body,
    color: C.midGray, margin: 0
  });

  const mcpTools = [
    { name: "research_topic", desc: "Tavily search + Claude synthesis", stripe: C.pink },
    { name: "generate_outline", desc: "Structured story outline", stripe: C.yellow },
    { name: "write_article", desc: "Full article from research", stripe: C.green },
    { name: "review_article", desc: "Grammar & tone review", stripe: C.teal },
    { name: "generate_tags", desc: "AI-generated tags & categories", stripe: C.blue },
    { name: "extract_sources", desc: "Source URLs from research", stripe: C.darkTeal },
  ];

  mcpTools.forEach((tool, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const x = 0.7 + col * 3.1;
    const y = 1.5 + row * 1.5;

    s7.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.8, h: 1.2, fill: { color: C.white } });
    // Top stripe
    s7.addShape(pres.shapes.RECTANGLE, { x, y, w: 2.8, h: 0.06, fill: { color: tool.stripe } });
    s7.addText(tool.name, {
      x: x + 0.15, y: y + 0.2, w: 2.5, h: 0.35, fontSize: 11, fontFace: F.mono,
      color: C.charcoal, bold: true, margin: 0
    });
    s7.addText(tool.desc, {
      x: x + 0.15, y: y + 0.6, w: 2.5, h: 0.4, fontSize: 10, fontFace: F.body,
      color: C.midGray, margin: 0
    });
  });

  // Repo badge
  s7.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.85, w: 8.9, h: 0.45, fill: { color: C.charcoal } });
  s7.addImage({ data: icons.github, x: 0.9, y: 4.92, w: 0.28, h: 0.28 });
  s7.addText("FastMCP — github.com/jlowin/fastmcp", {
    x: 1.3, y: 4.85, w: 8.0, h: 0.45, fontSize: 11, fontFace: F.body,
    color: C.white, valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 8 — MCP Code Sample (full-slide terminal)
  // ════════════════════════════════════════════════════════════════════
  let s8 = pres.addSlide();
  s8.background = { color: C.nearBlack };

  // Terminal header
  s8.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.3, w: 9.0, h: 0.4, fill: { color: C.codeHeader } });
  s8.addShape(pres.shapes.OVAL, { x: 0.7, y: 0.43, w: 0.12, h: 0.12, fill: { color: "FF5F56" } });
  s8.addShape(pres.shapes.OVAL, { x: 0.9, y: 0.43, w: 0.12, h: 0.12, fill: { color: "FFBD2E" } });
  s8.addShape(pres.shapes.OVAL, { x: 1.1, y: 0.43, w: 0.12, h: 0.12, fill: { color: "27C93F" } });
  s8.addText("mcp_servers/newsroom_tools.py", {
    x: 1.4, y: 0.3, w: 7.8, h: 0.4, fontSize: 10, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });

  // Code body
  s8.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.7, w: 9.0, h: 4.5, fill: { color: C.codeBg } });

  const mcpCode = `from fastmcp import FastMCP

mcp = FastMCP("newsroom-tools")

@mcp.tool()
async def research_topic(
    topic: str, questions: list[str],
    max_results: int = 5
) -> dict:
    """Research a topic using Tavily web search
    and synthesize findings with Claude."""

    # Search with Tavily
    results = await tavily_client.search(
        query=topic, max_results=max_results,
        search_depth="advanced"
    )

    # Synthesize with Claude
    synthesis = await anthropic.messages.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user",
                   "content": format_research(results)}]
    )
    return {"sources": results, "synthesis": synthesis}`;

  s8.addText(mcpCode, {
    x: 0.75, y: 0.85, w: 8.5, h: 4.2, fontSize: 10.5, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 9 — Elasticsearch Indexing (left text, right code — teal header)
  // ════════════════════════════════════════════════════════════════════
  let s9 = pres.addSlide();
  s9.background = { color: C.white };
  // Teal header bar
  s9.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.blue } });
  s9.addImage({ data: icons.databaseWh, x: 0.7, y: 0.25, w: 0.45, h: 0.45 });
  s9.addText("Elasticsearch — Indexing & Storage", {
    x: 1.3, y: 0.25, w: 8.0, h: 0.5, fontSize: 26, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });

  // Left: numbered features
  const esFeatures = [
    { title: "31-Field Rich Mapping", desc: "Structured metadata with nested research_sources" },
    { title: "semantic_text Fields", desc: "Automatic embeddings via copy_to — no pipeline" },
    { title: "Bulk Indexing", desc: "elasticsearch.helpers.bulk with refresh='wait_for'" },
    { title: "ILM Policies", desc: "Hot → Warm → Cold lifecycle management" },
  ];

  esFeatures.forEach((f, i) => {
    const y = 1.3 + i * 0.95;
    s9.addText(f.title, {
      x: 0.7, y: y, w: 4.1, h: 0.28, fontSize: 13, fontFace: F.body,
      color: C.charcoal, bold: true, bullet: { type: "number" }, margin: 0
    });
    s9.addText(f.desc, {
      x: 1.1, y: y + 0.3, w: 3.7, h: 0.3, fontSize: 10, fontFace: F.body,
      color: C.midGray, margin: 0
    });
  });

  // Right: code
  s9.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.1, w: 4.3, h: 0.35, fill: { color: C.codeHeader } });
  s9.addShape(pres.shapes.OVAL, { x: 5.45, y: 1.22, w: 0.1, h: 0.1, fill: { color: "FF5F56" } });
  s9.addShape(pres.shapes.OVAL, { x: 5.62, y: 1.22, w: 0.1, h: 0.1, fill: { color: "FFBD2E" } });
  s9.addShape(pres.shapes.OVAL, { x: 5.79, y: 1.22, w: 0.1, h: 0.1, fill: { color: "27C93F" } });
  s9.addText("index-mapping.json", {
    x: 6.0, y: 1.1, w: 3.4, h: 0.35, fontSize: 9, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });
  s9.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.45, w: 4.3, h: 3.85, fill: { color: C.codeBg } });

  const esMapping = `{
  "mappings": {
    "properties": {
      "headline": {
        "type": "text",
        "copy_to": "headline_semantic"
      },
      "headline_semantic": {
        "type": "semantic_text"
      },
      "content": {
        "type": "text",
        "copy_to": "content_semantic"
      },
      "content_semantic": {
        "type": "semantic_text"
      },
      "research_sources": {
        "type": "nested",
        "properties": {
          "title": {"type": "text"},
          "url": {"type": "keyword"}
        }
      }
    }
  }
}`;

  s9.addText(esMapping, {
    x: 5.5, y: 1.55, w: 3.9, h: 3.6, fontSize: 8.5, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 10 — ES Search Modes (three columns + code below)
  // ════════════════════════════════════════════════════════════════════
  let s10 = pres.addSlide();
  s10.background = { color: C.white };
  s10.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.teal } });
  s10.addImage({ data: icons.databaseWh, x: 0.7, y: 0.25, w: 0.45, h: 0.45 });
  s10.addText("Elasticsearch — Three Search Modes", {
    x: 1.3, y: 0.25, w: 8.0, h: 0.5, fontSize: 24, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });

  const modes = [
    { title: "Keyword", desc: "multi_match with field boosting and fuzziness", color: C.pink },
    { title: "Semantic", desc: "Natural language via semantic_text with auto embeddings", color: C.green },
    { title: "Hybrid (RRF)", desc: "Combines both using Reciprocal Rank Fusion", color: C.blue },
  ];

  modes.forEach((m, i) => {
    const x = 0.7 + i * 3.1;
    // Colored top block
    s10.addShape(pres.shapes.RECTANGLE, { x, y: 1.2, w: 2.8, h: 0.5, fill: { color: m.color } });
    s10.addText(m.title, {
      x, y: 1.2, w: 2.8, h: 0.5, fontSize: 16, fontFace: F.body,
      color: m.color === C.green ? C.charcoal : C.white, bold: true, align: "center", valign: "middle", margin: 0
    });
    s10.addText(m.desc, {
      x: x + 0.1, y: 1.8, w: 2.6, h: 0.6, fontSize: 10, fontFace: F.body,
      color: C.midGray, align: "center", margin: 0
    });
  });

  // Code block
  s10.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.7, w: 8.6, h: 0.35, fill: { color: C.codeHeader } });
  s10.addShape(pres.shapes.OVAL, { x: 0.85, y: 2.82, w: 0.1, h: 0.1, fill: { color: "FF5F56" } });
  s10.addShape(pres.shapes.OVAL, { x: 1.02, y: 2.82, w: 0.1, h: 0.1, fill: { color: "FFBD2E" } });
  s10.addShape(pres.shapes.OVAL, { x: 1.19, y: 2.82, w: 0.1, h: 0.1, fill: { color: "27C93F" } });
  s10.addText("hybrid_search.py", {
    x: 1.4, y: 2.7, w: 7.6, h: 0.35, fontSize: 9, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });
  s10.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 3.05, w: 8.6, h: 2.2, fill: { color: C.codeBg } });

  const hybridCode = `response = es_client.search(
    index="news_archive",
    sub_searches=[
        {"query": {"multi_match": {
            "query": q, "fields": ["headline^3", "content", "topic^2"],
            "fuzziness": "AUTO"
        }}},
        {"query": {"semantic": {"field": "content_semantic", "query": q}}}
    ],
    rank={"rrf": {"window_size": 50, "rank_constant": 20}},
    size=limit
)`;

  s10.addText(hybridCode, {
    x: 0.9, y: 3.15, w: 8.2, h: 2.0, fontSize: 10, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 11 — Workflow (horizontal step flow)
  // ════════════════════════════════════════════════════════════════════
  let s11 = pres.addSlide();
  s11.background = { color: C.nearBlack };
  s11.addText("End-to-End Workflow", {
    x: 0.7, y: 0.3, w: 8.6, h: 0.5, fontSize: 32, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });

  const steps = [
    { label: "User submits\ntopic", bg: C.pink, text: C.white },
    { label: "News Chief\nassigns story", bg: C.yellow, text: C.charcoal },
    { label: "Reporter\noutlines", bg: C.green, text: C.charcoal },
    { label: "Researcher\n+ Archivist", bg: C.teal, text: C.white },
  ];
  const steps2 = [
    { label: "Reporter\nwrites article", bg: C.blue, text: C.white },
    { label: "Editor\nreviews draft", bg: C.darkTeal, text: C.white },
    { label: "Publisher\nindexes to ES", bg: C.yellow, text: C.charcoal },
  ];

  // Top row
  steps.forEach((step, i) => {
    const x = 0.5 + i * 2.35;
    s11.addShape(pres.shapes.RECTANGLE, { x, y: 1.2, w: 2.05, h: 1.2, fill: { color: step.bg } });
    s11.addText(step.label, {
      x, y: 1.2, w: 2.05, h: 1.2, fontSize: 12, fontFace: F.body,
      color: step.text, bold: true, align: "center", valign: "middle", margin: 0
    });
    if (i < 3) {
      s11.addText("→", {
        x: x + 2.05, y: 1.5, w: 0.3, h: 0.5, fontSize: 20, fontFace: F.body,
        color: C.pink, align: "center", valign: "middle", margin: 0
      });
    }
  });

  // Arrow down
  s11.addText("↓", {
    x: 8.3, y: 2.45, w: 0.5, h: 0.5, fontSize: 22, fontFace: F.body,
    color: C.pink, align: "center", margin: 0
  });

  // Bottom row (right to left)
  steps2.forEach((step, i) => {
    const x = 5.7 - i * 2.35;
    s11.addShape(pres.shapes.RECTANGLE, { x, y: 3.1, w: 2.05, h: 1.2, fill: { color: step.bg } });
    s11.addText(step.label, {
      x, y: 3.1, w: 2.05, h: 1.2, fontSize: 12, fontFace: F.body,
      color: step.text, bold: true, align: "center", valign: "middle", margin: 0
    });
    if (i < 2) {
      s11.addText("←", {
        x: x - 0.3, y: 3.4, w: 0.3, h: 0.5, fontSize: 20, fontFace: F.body,
        color: C.pink, align: "center", valign: "middle", margin: 0
      });
    }
  });

  // SSE note
  s11.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.6, w: 8.6, h: 0.6, fill: { color: C.darkBg } });
  s11.addText("Real-time SSE events stream to React UI at every step — users watch the article being built live", {
    x: 0.9, y: 4.6, w: 8.2, h: 0.6, fontSize: 12, fontFace: F.body,
    color: C.teal, align: "center", valign: "middle", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 12 — Agent Communication Code (terminal style)
  // ════════════════════════════════════════════════════════════════════
  let s12 = pres.addSlide();
  s12.background = { color: C.nearBlack };

  s12.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.3, w: 9.0, h: 0.4, fill: { color: C.codeHeader } });
  s12.addShape(pres.shapes.OVAL, { x: 0.7, y: 0.43, w: 0.12, h: 0.12, fill: { color: "FF5F56" } });
  s12.addShape(pres.shapes.OVAL, { x: 0.9, y: 0.43, w: 0.12, h: 0.12, fill: { color: "FFBD2E" } });
  s12.addShape(pres.shapes.OVAL, { x: 1.1, y: 0.43, w: 0.12, h: 0.12, fill: { color: "27C93F" } });
  s12.addText("agents/news_chief.py — Dispatching via A2A", {
    x: 1.4, y: 0.3, w: 7.8, h: 0.4, fontSize: 10, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });

  s12.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 0.7, w: 9.0, h: 4.5, fill: { color: C.codeBg } });

  const commCode = `class NewsChiefAgent(BaseAgent):

    async def _assign_story(self, request):
        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Step 1: Send to Reporter via A2A
        reporter_result = await self._send_to_agent(
            agent_url="http://localhost:8081",
            message=json.dumps({
                "action": "write_article",
                "assignment": {"story_id": story_id,
                               "topic": topic}
            })
        )

        # Step 2: Send draft to Editor for review
        editor_result = await self._send_to_agent(
            agent_url="http://localhost:8082",
            message=json.dumps({
                "action": "review_draft",
                "draft": reporter_result["article"]
            })
        )

        # Step 3: Publish via Publisher on :8084
        await self._send_to_agent(
            PUBLISHER_URL, json.dumps({"action": "publish", ...})
        )`;

  s12.addText(commCode, {
    x: 0.75, y: 0.85, w: 8.5, h: 4.2, fontSize: 10, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 13 — Archivist (split layout)
  // ════════════════════════════════════════════════════════════════════
  let s13 = pres.addSlide();
  s13.background = { color: C.white };
  s13.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.darkTeal } });
  s13.addText("Archivist — Elastic Cloud A2A Agent", {
    x: 0.7, y: 0.25, w: 8.6, h: 0.5, fontSize: 24, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });

  // Left: explanation
  s13.addText("Built with Elastic Agent Builder", {
    x: 0.7, y: 1.3, w: 4.3, h: 0.35, fontSize: 16, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });

  const archSteps = [
    "Reporter generates research questions",
    "Researcher + Archivist queried in parallel",
    "Archivist searches Elastic Cloud index",
    "Results merged into Reporter's context",
  ];

  archSteps.forEach((step, i) => {
    const y = 1.85 + i * 0.55;
    s13.addText(step, {
      x: 0.7, y: y, w: 4.2, h: 0.35, fontSize: 12, fontFace: F.body,
      color: C.charcoal, valign: "middle", bullet: { type: "number" }, margin: 0
    });
  });

  s13.addText("Deploy A2A-compatible agents directly from your Elastic Cloud cluster.", {
    x: 0.7, y: 4.2, w: 4.3, h: 0.4, fontSize: 10, fontFace: F.body,
    color: C.midGray, italic: true, margin: 0
  });

  // Right: code
  s13.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.1, w: 4.3, h: 0.35, fill: { color: C.codeHeader } });
  s13.addShape(pres.shapes.OVAL, { x: 5.45, y: 1.22, w: 0.1, h: 0.1, fill: { color: "FF5F56" } });
  s13.addShape(pres.shapes.OVAL, { x: 5.62, y: 1.22, w: 0.1, h: 0.1, fill: { color: "FFBD2E" } });
  s13.addShape(pres.shapes.OVAL, { x: 5.79, y: 1.22, w: 0.1, h: 0.1, fill: { color: "27C93F" } });
  s13.addText("parallel_research.py", {
    x: 6.0, y: 1.1, w: 3.4, h: 0.35, fontSize: 9, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });
  s13.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.45, w: 4.3, h: 3.55, fill: { color: C.codeBg } });

  const archCode = `# Reporter dispatches in parallel
research_task = asyncio.create_task(
    self._send_to_agent(
        RESEARCHER_URL,
        {"action": "research",
         "questions": questions}
    )
)

archive_task = asyncio.create_task(
    self._send_to_agent(
        ARCHIVIST_URL,
        {"action": "search",
         "queries": questions}
    )
)

research, archive = await asyncio.gather(
    research_task, archive_task
)`;

  s13.addText(archCode, {
    x: 5.5, y: 1.55, w: 3.9, h: 3.3, fontSize: 10, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 14 — SSE Events (numbered steps + code)
  // ════════════════════════════════════════════════════════════════════
  let s14 = pres.addSlide();
  s14.background = { color: C.lightGray };
  s14.addText("Real-Time UI with Server-Sent Events", {
    x: 0.7, y: 0.4, w: 8.6, h: 0.5, fontSize: 28, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });

  const eventSteps = [
    { title: "Agent publishes event", desc: "POSTs to Event Hub after key actions", color: C.pink },
    { title: "Event Hub broadcasts via SSE", desc: "Starlette streams to all clients", color: C.green },
    { title: "React UI renders live", desc: "Workflow updates in real-time", color: C.blue },
  ];

  eventSteps.forEach((step, i) => {
    const x = 0.7 + i * 3.0;
    s14.addText(step.title, {
      x: x, y: 1.1, w: 2.7, h: 0.25, fontSize: 11, fontFace: F.body,
      color: C.charcoal, bold: true, bullet: { type: "number" }, margin: 0
    });
    s14.addText(step.desc, {
      x: x + 0.35, y: 1.35, w: 2.35, h: 0.3, fontSize: 9, fontFace: F.body,
      color: C.midGray, margin: 0
    });
  });

  // Code
  s14.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.9, w: 8.6, h: 0.35, fill: { color: C.codeHeader } });
  s14.addShape(pres.shapes.OVAL, { x: 0.85, y: 2.02, w: 0.1, h: 0.1, fill: { color: "FF5F56" } });
  s14.addShape(pres.shapes.OVAL, { x: 1.02, y: 2.02, w: 0.1, h: 0.1, fill: { color: "FFBD2E" } });
  s14.addShape(pres.shapes.OVAL, { x: 1.19, y: 2.02, w: 0.1, h: 0.1, fill: { color: "27C93F" } });
  s14.addText("base_agent.py", {
    x: 1.4, y: 1.9, w: 7.6, h: 0.35, fontSize: 9, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });
  s14.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.25, w: 8.6, h: 3.05, fill: { color: C.codeBg } });

  const sseCode = `# BaseAgent._publish_event()
async def _publish_event(self, event_type, story_id, data):
    payload = {
        "event_type": event_type,
        "story_id": story_id,
        "agent": self.__class__.__name__,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    async with httpx.AsyncClient() as client:
        await client.post(
            EVENT_HUB_URL + "/events/publish", json=payload
        )

# Event types: story_assigned, outline_generated,
# research_completed, article_written,
# review_completed, article_published`;

  s14.addText(sseCode, {
    x: 0.9, y: 2.35, w: 8.2, h: 2.85, fontSize: 10, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 15 — Testing & Observability (horizontal two-block)
  // ════════════════════════════════════════════════════════════════════
  let s15 = pres.addSlide();
  s15.background = { color: C.white };
  s15.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.525, w: 10, h: 0.1, fill: { color: C.yellow } });

  s15.addText("Testing & Observability", {
    x: 0.7, y: 0.4, w: 8.6, h: 0.5, fontSize: 32, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });

  // Left: Testing block
  s15.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.15, w: 4.2, h: 0.45, fill: { color: C.pink } });
  s15.addText("Testing", {
    x: 0.7, y: 1.15, w: 4.2, h: 0.45, fontSize: 16, fontFace: F.body,
    color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });
  s15.addText([
    { text: "Full mock suite — no API keys needed", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "MockElasticsearch with ES 9.x keyword args", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "Mock Anthropic, Tavily, bulk helpers", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "Pytest with async support", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "make test runs everything", options: { bullet: true, fontSize: 12 } },
  ], {
    x: 0.9, y: 1.7, w: 3.8, h: 1.8, fontFace: F.body,
    color: C.charcoal, valign: "top", margin: 0
  });

  // Right: Observability block
  s15.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 1.15, w: 4.2, h: 0.45, fill: { color: C.darkTeal } });
  s15.addText("Structured Logging", {
    x: 5.1, y: 1.15, w: 4.2, h: 0.45, fontSize: 16, fontFace: F.body,
    color: C.white, bold: true, align: "center", valign: "middle", margin: 0
  });
  s15.addText([
    { text: "LOG_FORMAT=json for production", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "Per-agent colored console output", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "Agent name in every log line", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "ELK / Datadog / CloudWatch compatible", options: { bullet: true, breakLine: true, fontSize: 12 } },
    { text: "%-style formatting (no f-strings in logs)", options: { bullet: true, fontSize: 12 } },
  ], {
    x: 5.3, y: 1.7, w: 3.8, h: 1.8, fontFace: F.body,
    color: C.charcoal, valign: "top", margin: 0
  });

  // JSON sample
  s15.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 3.8, w: 8.6, h: 0.3, fill: { color: C.codeHeader } });
  s15.addShape(pres.shapes.OVAL, { x: 0.85, y: 3.88, w: 0.1, h: 0.1, fill: { color: "FF5F56" } });
  s15.addShape(pres.shapes.OVAL, { x: 1.02, y: 3.88, w: 0.1, h: 0.1, fill: { color: "FFBD2E" } });
  s15.addShape(pres.shapes.OVAL, { x: 1.19, y: 3.88, w: 0.1, h: 0.1, fill: { color: "27C93F" } });
  s15.addText("stdout (LOG_FORMAT=json)", {
    x: 1.4, y: 3.8, w: 7.6, h: 0.3, fontSize: 8, fontFace: F.mono,
    color: C.midGray, valign: "middle", margin: 0
  });
  s15.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 4.1, w: 8.6, h: 0.8, fill: { color: C.codeBg } });
  s15.addText('{"timestamp":"2026-04-21T10:30:45","level":"INFO",\n "agent":"REPORTER","message":"Article written: story=story_20260421 words=1023"}', {
    x: 0.9, y: 4.15, w: 8.2, h: 0.7, fontSize: 9, fontFace: F.mono,
    color: C.white, valign: "top", margin: 0
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 16 — Lessons Learned (yellow bg, clean numbered list)
  // ════════════════════════════════════════════════════════════════════
  let s16 = pres.addSlide();
  s16.background = { color: C.green };

  s16.addText("Lessons Learned", {
    x: 0.7, y: 0.4, w: 8.6, h: 0.6, fontSize: 36, fontFace: F.body,
    color: C.charcoal, bold: true, margin: 0
  });

  const lessons = [
    { title: "Specialization > Generalization", desc: "Five focused agents beat one do-everything LLM call" },
    { title: "A2A makes agents composable", desc: "Swap any agent without touching the rest" },
    { title: "MCP centralizes tool logic", desc: "One tool server — consistent behavior, no duplication" },
    { title: "semantic_text is magic", desc: "Elasticsearch handles embeddings automatically — zero pipeline" },
    { title: "SSE keeps users engaged", desc: "Watching the workflow live turns a wait into an experience" },
  ];

  lessons.forEach((l, i) => {
    const y = 1.2 + i * 0.82;
    s16.addText(l.title, {
      x: 0.7, y: y, w: 8.6, h: 0.3, fontSize: 15, fontFace: F.body,
      color: C.charcoal, bold: true, bullet: { type: "number" }, margin: 0
    });
    s16.addText(l.desc, {
      x: 1.1, y: y + 0.35, w: 8.2, h: 0.3, fontSize: 12, fontFace: F.body,
      color: C.charcoal, margin: 0
    });
  });

  // ════════════════════════════════════════════════════════════════════
  // SLIDE 17 — Q&A (split: yellow left, dark right)
  // ════════════════════════════════════════════════════════════════════
  let s17 = pres.addSlide();
  s17.background = { color: C.charcoal };

  // Pink left panel
  s17.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 4.0, h: 5.625, fill: { color: C.pink } });
  s17.addImage({ data: icons.boltWh, x: 1.5, y: 1.5, w: 1.0, h: 1.0 });
  s17.addText("Q & A", {
    x: 0.4, y: 2.7, w: 3.2, h: 0.8, fontSize: 44, fontFace: F.body,
    color: C.white, bold: true, align: "center", margin: 0
  });

  // Right side
  s17.addText("Justin Castilla", {
    x: 4.5, y: 1.5, w: 5.0, h: 0.4, fontSize: 20, fontFace: F.body,
    color: C.white, bold: true, margin: 0
  });
  s17.addText("justincastilla@gmail.com", {
    x: 4.5, y: 2.0, w: 5.0, h: 0.3, fontSize: 13, fontFace: F.body,
    color: C.midGray, margin: 0
  });

  s17.addShape(pres.shapes.LINE, { x: 4.5, y: 2.6, w: 4.0, h: 0, line: { color: C.pink, width: 2 } });

  s17.addImage({ data: icons.github, x: 4.5, y: 2.9, w: 0.3, h: 0.3 });
  s17.addText("github.com/elastic/elastic-newsroom", {
    x: 4.9, y: 2.9, w: 4.5, h: 0.3, fontSize: 12, fontFace: F.mono,
    color: C.pink, valign: "middle", margin: 0
  });

  // Tech tags
  const tags = [
    { name: "A2A", bg: C.pink },
    { name: "FastMCP", bg: C.yellow },
    { name: "Tavily", bg: C.green },
    { name: "Elasticsearch", bg: C.teal },
    { name: "Claude", bg: C.blue },
    { name: "React", bg: C.darkTeal },
  ];
  tags.forEach((tag, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const x = 4.5 + col * 1.5;
    const y = 3.5 + row * 0.5;
    s17.addShape(pres.shapes.RECTANGLE, { x, y, w: 1.3, h: 0.35, fill: { color: tag.bg } });
    s17.addText(tag.name, {
      x, y, w: 1.3, h: 0.35, fontSize: 10, fontFace: F.body,
      color: (tag.bg === C.yellow || tag.bg === C.green) ? C.charcoal : C.white,
      bold: true, align: "center", valign: "middle", margin: 0
    });
  });

  // ════════════════════════════════════════════════════════════════════
  // WRITE
  // ════════════════════════════════════════════════════════════════════
  const outputPath = "/sessions/friendly-optimistic-brahmagupta/mnt/elastic-newsroom/elastic-newsroom-talk.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log("Saved: " + outputPath);
}

createPresentation().catch(err => { console.error(err); process.exit(1); });
