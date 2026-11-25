// Builds build/html/GT32U2086_SDK_User_Guide.pdf from the generated HTML pages.
// Usage: node tools/make_pdf.js   (run after `doxygen Doxyfile`)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const HTML = path.resolve(__dirname, '..', 'build', 'html');
const structure = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', 'pages', '_structure.json'), 'utf8'));
const VERSION = 'v1.0';  // số phiên bản tài liệu
const COPYRIGHT = 'Copyright © 2026 GTINX - FPT Telecom';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ colorScheme: 'light' });
  const page = await ctx.newPage();

  // collect the body of every chapter page, in reading order
  const sections = [];
  // titles are read from the built pages, so a title edited on the web also shows in the PDF
  const pageTitle = () => page.$eval('div.headertitle .title', e => e.textContent.trim()).catch(() => '');
  for (const part of structure.parts) {
    await page.goto('file://' + path.join(HTML, part.label + '.html'));
    sections.push({ part: (await pageTitle()) || part.title });
    for (const ch of part.chapters) {
      await page.goto('file://' + path.join(HTML, ch.label + '.html'));
      const body = await page.$eval('div.textblock', e => e.innerHTML);
      sections.push({ title: (await pageTitle()) || ch.title, body });
    }
  }

  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  let toc = '', content = '';
  for (const s of sections) {
    if (s.part) {
      toc += `<li class="toc-part">${esc(s.part)}</li>`;
      content += `<section class="part"><h1 class="part-title">${esc(s.part)}</h1></section>`;
    } else {
      toc += `<li>${esc(s.title)}</li>`;
      content += `<section class="chapter"><h1 class="chapter-title">${esc(s.title)}</h1>${s.body}</section>`;
    }
  }

  const doc = `<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="doxygen.css" rel="stylesheet"><link href="gt32u2086.css" rel="stylesheet">
<style>
  @page { size: A4; margin: 18mm 16mm 20mm; }
  body { background: #fff; color: #000; font-family: Inter, Arial, sans-serif; font-size: 10.5pt; }
  .cover { height: 245mm; display: flex; flex-direction: column; justify-content: center; page-break-after: always; }
  .cover img { width: 60mm; margin-bottom: 18mm; }
  .cover .t { font: 400 30pt/1.15 Inter; color: #00673A; margin: 0 0 6mm; }
  .cover .s { font: 600 14pt Inter; margin: 0 0 3mm; }
  .cover .g { font: 400 11pt Inter; color: #444; margin: 0 0 14mm; }
  .cover .v { font: 400 10pt Inter; color: #444; }
  .pdf-toc { page-break-after: always; }
  .pdf-toc h1 { font: 400 20pt Inter; color: #00673A; }
  .pdf-toc ul { list-style: none; padding: 0; }
  .pdf-toc li { font: 10.5pt/1.9 Inter; padding-left: 6mm; }
  .pdf-toc li.toc-part { font-weight: 600; padding-left: 0; margin-top: 3mm; }
  .part { page-break-before: always; height: 230mm; display: flex; align-items: center; }
  .part-title { font: 400 22pt Inter; color: #00673A; border: none; }
  .chapter { page-break-before: always; }
  .chapter-title { font: 400 18pt/1.25 Inter !important; color: #00673A !important; border: none !important; margin: 0 0 6mm !important; padding: 0 !important; }
  .chapter h1 { font: 700 12pt Inter; color: #00673A; border-bottom: 1px solid #DDE2E8; margin: 7mm 0 3mm; padding-bottom: 1.5mm; }
  .chapter h2 { font: 700 10.5pt Inter; margin: 5mm 0 2mm; }
  .chapter h3 { font: 700 10.5pt Inter; margin: 4mm 0 2mm; }
  .chapter h4 { font: 700 10pt Inter; }
  .chapter p, .chapter li, .chapter td, .chapter th { font-size: 10.5pt; line-height: 1.5; }
  table.markdownTable { width: 100%; page-break-inside: auto; }
  table.markdownTable tr { page-break-inside: avoid; }
  table.markdownTable td, table.markdownTable th { font-size: 9.5pt !important; padding: 4px 8px; }
  div.fragment { page-break-inside: avoid; position: static; }
  div.line { font-size: 8.5pt; }
  div.image { page-break-inside: avoid; }
  div.image object { max-width: 100%; }
  .gt32u2086-copy, a.anchor { display: none; }
  a { color: #000; text-decoration: none; }
</style></head><body>
<div class="cover">
  <img src="logo_gtinx.png">
  <p class="t">GT32U2086 SDK User Guide</p>
  <p class="s">${esc(structure.subtitle[0] || '')}</p>
  <p class="g">${esc(structure.tagline[0] || '')}</p>
  <p class="v">${VERSION}</p>
</div>
<div class="pdf-toc"><h1>Contents</h1><ul>${toc}</ul></div>
${content}
</body></html>`;

  const tmp = path.join(HTML, '_print.html');
  fs.writeFileSync(tmp, doc);
  await page.goto('file://' + tmp);
  await page.waitForTimeout(800);
  await page.pdf({
    path: path.join(HTML, 'GT32U2086_SDK_User_Guide.pdf'),
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `<div style="width:100%;font:8px Inter,Arial;color:#777;padding:0 16mm;display:flex;justify-content:space-between">
      <span>${COPYRIGHT}</span><span>GT32U2086 SDK User Guide${VERSION ? " " + VERSION : ""} · <span class="pageNumber"></span>/<span class="totalPages"></span></span></div>`,
    margin: { top: '18mm', bottom: '20mm', left: '16mm', right: '16mm' },
  });
  fs.unlinkSync(tmp);
  await browser.close();
  console.log('PDF written');
})();
