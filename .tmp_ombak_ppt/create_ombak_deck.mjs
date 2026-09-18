import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const root = "/Users/Cahyo/Documents/OMBAK_NUSANTARA/Ombak_Nusantara";
const outDir = `${root}/documentation`;
const outFile = `${outDir}/Ombak_Nusantara_Overview.pptx`;
const previewDir = `${root}/.tmp_ombak_ppt/previews`;

const C = {
  ink: "#0F2922",
  deep: "#112D26",
  wave: "#00A6C8",
  pale: "#EAF5F7",
  mist: "#F4F8F8",
  rule: "#BDD0D2",
  muted: "#517068",
  coral: "#EE7D62",
  white: "#FFFFFF",
};

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function text(slide, name, value, position, style = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  box.text = value;
  box.text.style = {
    fontFace: "Helvetica Neue",
    fontSize: 24,
    color: C.ink,
    alignment: "left",
    verticalAlignment: "top",
    ...style,
  };
  return box;
}

function rule(slide, name, left, top, width, color = C.rule, height = 1) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left, top, width, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function dot(slide, name, left, top, color = C.wave, size = 12) {
  return slide.shapes.add({
    geometry: "ellipse",
    name,
    position: { left, top, width: size, height: size },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function footer(slide, n) {
  text(slide, `footer-${n}`, `Ombak Nusantara  /  ${String(n).padStart(2, "0")}`, { left: 42, top: 662, width: 360, height: 20 }, { fontSize: 13, color: C.muted });
}

function notes(slide, entries) {
  slide.speakerNotes.textFrame.setText(["[Sources]", ...entries]);
  slide.speakerNotes.setVisible(true);
}

function addCover(presentation, heroBytes) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  text(slide, "cover-kicker", "APLIKASI PENDAMPING SURFER INDONESIA", { left: 42, top: 42, width: 540, height: 24 }, { fontSize: 16, bold: true, color: C.wave });
  text(slide, "cover-title", "Ombak\nNusantara", { left: 42, top: 165, width: 550, height: 220 }, { fontSize: 70, bold: true, color: C.ink, verticalAlignment: "bottom" });
  rule(slide, "cover-rule", 42, 430, 108, C.wave, 5);
  text(slide, "cover-subtitle", "Temukan spot, pahami kondisi,\ndan rencanakan sesi dengan lebih percaya diri.", { left: 42, top: 465, width: 535, height: 110 }, { fontSize: 27, color: C.muted });
  slide.images.add({
    blob: heroBytes,
    contentType: "image/webp",
    alt: "Peselancar menunggangi ombak di pantai tropis",
    fit: "cover",
    position: { left: 658, top: 42, width: 582, height: 588 },
    geometry: "roundRect",
    borderRadius: 18,
  });
  footer(slide, 1);
  notes(slide, ["Local image asset: backend/uploads/268aadfce7f94387a3234f560e4e257c.webp (workspace-provided).", "Product statements based on workspace application source."]);
}

function addWhy(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  text(slide, "why-title", "Mengapa aplikasi ini dibuat", { left: 42, top: 42, width: 860, height: 60 }, { fontSize: 48, bold: true });
  text(slide, "why-lead", "Persiapan untuk berselancar sering dimulai dari\ninformasi yang terpisah-pisah.", { left: 42, top: 174, width: 575, height: 116 }, { fontSize: 34, color: C.ink });
  const items = [
    ["Kondisi berubah cepat", "Gelombang, angin, dan cuaca perlu dibaca bersama."],
    ["Spot harus sesuai level", "Setiap surfer membutuhkan konteks yang berbeda."],
    ["Risiko perlu dibagikan", "Peringatan lokal membantu komunitas lebih siap."],
  ];
  items.forEach(([title, body], i) => {
    const y = 174 + i * 145;
    dot(slide, `why-dot-${i}`, 698, y + 9, i === 2 ? C.coral : C.wave, 14);
    text(slide, `why-item-${i}`, title, { left: 730, top: y, width: 440, height: 34 }, { fontSize: 27, bold: true });
    text(slide, `why-body-${i}`, body, { left: 730, top: y + 48, width: 450, height: 48 }, { fontSize: 20, color: C.muted });
    if (i < items.length - 1) rule(slide, `why-rule-${i}`, 698, y + 116, 470, C.rule, 1);
  });
  footer(slide, 2);
  notes(slide, ["Product framing based on workspace application source: frontend/src/Dashboard.svelte, frontend/src/SurfMap.svelte, and frontend/src/Hazard.svelte."]);
}

function addWhat(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  text(slide, "what-title", "Apa itu Ombak Nusantara?", { left: 42, top: 42, width: 900, height: 60 }, { fontSize: 48, bold: true });
  text(slide, "what-intro", "Platform pendamping surfer untuk mengeksplorasi spot,\nmembaca kondisi, dan saling berbagi informasi.", { left: 42, top: 130, width: 820, height: 74 }, { fontSize: 24, color: C.muted });
  const cells = [
    [42, 248, "Surf Spots", "Peta lokasi dan pencarian spot."],
    [656, 248, "Forecast", "Gelombang, angin, dan tren kondisi."],
    [42, 462, "Surf Planner", "Rencana sesi sesuai level dan waktu."],
    [656, 462, "Hazard Alert", "Laporan risiko dari komunitas."],
  ];
  cells.forEach(([x, y, title, body], i) => {
    rule(slide, `what-accent-${i}`, x, y, 76, i === 3 ? C.coral : C.wave, 5);
    text(slide, `what-cell-title-${i}`, title, { left: x, top: y + 27, width: 470, height: 40 }, { fontSize: 29, bold: true });
    text(slide, `what-cell-body-${i}`, body, { left: x, top: y + 76, width: 500, height: 56 }, { fontSize: 21, color: C.muted });
  });
  footer(slide, 3);
  notes(slide, ["Feature inventory based on workspace application source: frontend/src/App.svelte, frontend/src/SurfMap.svelte, frontend/src/SurfPlanner.svelte, and frontend/src/Hazard.svelte."]);
}

function addFlow(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.mist;
  text(slide, "flow-title", "Dari pencarian spot sampai sesi yang lebih siap", { left: 42, top: 42, width: 1120, height: 60 }, { fontSize: 46, bold: true });
  text(slide, "flow-lead", "Alur yang sederhana untuk membantu keputusan sebelum masuk air.", { left: 42, top: 123, width: 900, height: 34 }, { fontSize: 23, color: C.muted });
  rule(slide, "flow-line", 83, 343, 1050, C.deep, 2);
  const stages = [
    ["01", "Pilih spot", "Cari pantai yang ingin dieksplorasi."],
    ["02", "Cek kondisi", "Lihat gelombang, angin, dan peringatan."],
    ["03", "Susun rencana", "Siapkan sesi sesuai kebutuhanmu."],
  ];
  stages.forEach(([num, title, body], i) => {
    const x = 84 + i * 390;
    dot(slide, `flow-dot-${i}`, x - 7, 336, i === 2 ? C.coral : C.wave, 16);
    text(slide, `flow-num-${i}`, num, { left: x, top: 273, width: 100, height: 30 }, { fontSize: 19, bold: true, color: C.wave });
    text(slide, `flow-stage-${i}`, title, { left: x, top: 394, width: 300, height: 42 }, { fontSize: 30, bold: true });
    text(slide, `flow-body-${i}`, body, { left: x, top: 449, width: 300, height: 64 }, { fontSize: 21, color: C.muted });
  });
  footer(slide, 4);
  notes(slide, ["Workflow based on workspace application source: frontend/src/Surfing.svelte, frontend/src/SurfMap.svelte, and frontend/src/SurfPlanner.svelte."]);
}

function addOutcome(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.deep;
  text(slide, "outcome-kicker", "TUJUAN AKHIR", { left: 42, top: 42, width: 240, height: 28 }, { fontSize: 16, bold: true, color: "#81D6E8" });
  text(slide, "outcome-title", "Sesi yang lebih\npercaya diri.", { left: 42, top: 138, width: 570, height: 190 }, { fontSize: 66, bold: true, color: C.white, verticalAlignment: "bottom" });
  text(slide, "outcome-copy", "Ombak Nusantara menghubungkan kondisi laut,\nrencana personal, dan informasi komunitas.", { left: 42, top: 386, width: 620, height: 72 }, { fontSize: 25, color: "#C5DAD5" });
  const outcomes = [["Lebih siap", "Kondisi terbaca"], ["Lebih aman", "Risiko terlihat"], ["Lebih terhubung", "Komunitas berbagi"]];
  outcomes.forEach(([title, body], i) => {
    const y = 182 + i * 138;
    rule(slide, `outcome-rule-${i}`, 748, y, 440, i === 1 ? C.coral : "#5A8177", 1);
    text(slide, `outcome-item-${i}`, title, { left: 748, top: y + 22, width: 300, height: 38 }, { fontSize: 29, bold: true, color: C.white });
    text(slide, `outcome-body-${i}`, body, { left: 748, top: y + 68, width: 340, height: 28 }, { fontSize: 20, color: "#B6CCC6" });
  });
  text(slide, "outcome-footer", "Ombak Nusantara", { left: 42, top: 662, width: 260, height: 20 }, { fontSize: 13, color: "#8AB2A9" });
  text(slide, "outcome-page", "05", { left: 1180, top: 662, width: 50, height: 20 }, { fontSize: 13, color: "#8AB2A9", alignment: "right" });
  notes(slide, ["Product outcome statement based on workspace application source and intended product positioning."]);
}

function addTechStack(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  text(slide, "tech-kicker", "TEKNOLOGI", { left: 42, top: 42, width: 220, height: 28 }, { fontSize: 16, bold: true, color: C.wave });
  text(slide, "tech-title", "Tech stack yang digunakan", { left: 42, top: 86, width: 940, height: 62 }, { fontSize: 48, bold: true });
  text(slide, "tech-lead", "Arsitektur end-to-end untuk pengalaman web, riset latar belakang, dan rekomendasi berbasis AI.", { left: 42, top: 162, width: 1120, height: 34 }, { fontSize: 22, color: C.muted });
  rule(slide, "tech-divider", 640, 236, 1, 342, C.rule, 1);
  const left = [
    ["Frontend", "Svelte · Vite · Tailwind CSS"],
    ["Backend & data", "FastAPI · SQLModel · Alembic · SQLite"],
    ["Background jobs", "Celery · Redis"],
  ];
  const right = [
    ["AI & research", "OpenAI GPT-4o · Agno · Tavily"],
    ["Knowledge layer", "ChromaDB · text-embedding-3-small · MCP"],
  ];
  left.forEach(([title, body], i) => {
    const y = 246 + i * 113;
    rule(slide, `tech-left-accent-${i}`, 42, y, 58, C.wave, 4);
    text(slide, `tech-left-title-${i}`, title, { left: 42, top: y + 22, width: 310, height: 33 }, { fontSize: 27, bold: true });
    text(slide, `tech-left-body-${i}`, body, { left: 42, top: y + 62, width: 520, height: 30 }, { fontSize: 20, color: C.muted });
  });
  right.forEach(([title, body], i) => {
    const y = 246 + i * 148;
    rule(slide, `tech-right-accent-${i}`, 696, y, 58, i === 1 ? C.coral : C.wave, 4);
    text(slide, `tech-right-title-${i}`, title, { left: 696, top: y + 22, width: 340, height: 33 }, { fontSize: 27, bold: true });
    text(slide, `tech-right-body-${i}`, body, { left: 696, top: y + 62, width: 500, height: 56 }, { fontSize: 20, color: C.muted });
  });
  footer(slide, 6);
  notes(slide, ["Technology stack based on workspace source: README.md, frontend/package.json, backend/app/modules/surf/agents.py, backend/app/modules/mcp/server.py, and backend/app/modules/knowledge/vectordb.py."]);
}

async function main() {
  await fs.mkdir(outDir, { recursive: true });
  await fs.mkdir(previewDir, { recursive: true });
  const heroBytes = await fs.readFile(`${root}/backend/uploads/268aadfce7f94387a3234f560e4e257c.webp`);
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  addCover(presentation, heroBytes);
  addWhy(presentation);
  addWhat(presentation);
  addFlow(presentation);
  addOutcome(presentation);
  addTechStack(presentation);
  for (let i = 0; i < presentation.slides.items.length; i += 1) {
    await writeBlob(`${previewDir}/slide-${i + 1}.png`, await presentation.export({ slide: presentation.slides.items[i], format: "png", scale: 2 }));
  }
  await writeBlob(`${previewDir}/montage.webp`, await presentation.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outFile);
  await fs.writeFile(`${root}/.tmp_ombak_ppt/source-notes.txt`, "[Sources]\n- Product content: workspace source files README.md, frontend/src/App.svelte, Dashboard.svelte, SurfMap.svelte, SurfPlanner.svelte, Community.svelte, Hazard.svelte.\n- Tech stack: README.md, frontend/package.json, backend/app/modules/surf/agents.py, backend/app/modules/mcp/server.py, backend/app/modules/knowledge/vectordb.py.\n- Visual: workspace-provided photo backend/uploads/268aadfce7f94387a3234f560e4e257c.webp.\n");
  console.log(outFile);
}

main();
