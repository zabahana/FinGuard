/* Render the canonical Markdown article as portable, offline publication HTML.
 * Requires the marked package. Usage: node scripts/render-medium-article.cjs
 * NODE_PATH can point to an existing installation of marked.
 */
const fs = require('node:fs');
const path = require('node:path');
const { marked } = require('marked');

const docs = path.resolve(__dirname, '../docs');
const source = fs.readFileSync(path.join(docs, 'MEDIUM_ARTICLE.md'), 'utf8');
const title = source.split('\n')[0].replace(/^# /, '');
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
let article = marked.parse(source, { gfm: true });
// Embed only the known local figure assets; no remote image dependencies.
const figures = ['safety-outcomes', 'components', 'end-to-end', 'investigation', 'deployment', 'workspace'];
for (const name of figures) {
  const image = fs.readFileSync(path.join(docs, 'assets', `${name}.png`));
  article = article.replaceAll(`src="assets/${name}.png"`, `src="data:image/png;base64,${image.toString('base64')}"`);
}
article = article.replace(/<p>(<img[^>]+>)<\/p>\s*<p><em>(Figure \d\.[\s\S]*?)<\/em><\/p>/g,
  '<figure>$1<figcaption>$2</figcaption></figure>');
const words = source.split(/\s+/).length;
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escape(title)}</title><meta name="description" content="A practical FinGuard demo combining local fraud detection, Qwen tool use, OpenShell runtime security, application safety controls, and native audit evidence.">
<style>
:root{color-scheme:light;--ink:#202c27;--muted:#647068;--green:#176649;--line:#dce4de}*{box-sizing:border-box}body{margin:0;background:#fcfdfb;color:var(--ink)}.publication-tools{font:13px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;border-bottom:1px solid var(--line);background:#f0f5ef;padding:20px max(24px,calc((100% - 960px)/2));}.publication-tools strong{font-weight:650}.publication-tools p{margin:8px 0;color:var(--muted);max-width:900px}.buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}button{border:1px solid #bccfc0;background:white;color:var(--green);padding:8px 14px;font:inherit;border-radius:4px;cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid var(--green);outline-offset:3px}.masthead{max-width:780px;margin:48px auto 30px;padding:0 30px;font:11px/1.5 monospace;letter-spacing:1.8px;color:var(--green);text-transform:uppercase}.masthead span{display:block;margin-top:8px;font:12px/1.7 sans-serif;letter-spacing:0;text-transform:none;color:var(--muted)}article{max-width:780px;margin:auto;padding:0 30px 70px;font:20px/1.8 Georgia,"Times New Roman",serif}h1,h2{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#162e23}h1{font-size:clamp(34px,4.2vw,49px);line-height:1.14;letter-spacing:-1.5px;font-weight:650;margin:0 0 24px}h2{font-size:28px;line-height:1.3;letter-spacing:-.5px;margin:48px 0 18px;font-weight:650}p{margin:22px 0}article>h1+p{font:21px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--muted);margin-bottom:36px}article>h1+p em{font-style:normal}a{color:var(--green);text-underline-offset:4px}figure{margin:36px -40px;padding:22px;background:white;border:1px solid var(--line)}figure img{display:block;width:100%;height:auto;max-height:1100px;object-fit:contain}figcaption{font:13px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--muted);margin-top:18px}pre{background:#f0f4ef;border:1px solid var(--line);padding:18px;overflow:auto;font:13px/1.7 monospace}code{font-family:monospace;font-size:.8em;overflow-wrap:anywhere}pre code{font-size:inherit}li{margin:10px 0}footer{max-width:780px;margin:auto;padding:24px 30px 50px;border-top:1px solid var(--line);font:12px/1.8 sans-serif;color:var(--muted)}#selection-status{font-size:12px;color:var(--green)}@media(max-width:850px){figure{margin:30px 0;padding:12px}}@media(max-width:500px){article{padding:0 22px 40px;font-size:18px}h1{font-size:35px;letter-spacing:-.9px}h2{font-size:25px}.masthead{padding:0 22px;margin-top:32px}.publication-tools{padding:16px 22px}article>h1+p{font-size:19px}figure{padding:9px}figcaption{font-size:12px}}@media print{.publication-tools{display:none}body{background:white}article{font-size:12pt;max-width:none}h1{font-size:28pt}h2{font-size:18pt;break-after:avoid}figure{break-inside:avoid;margin:20px 0}figure img{max-height:720px}.masthead{margin-top:10px}a{color:inherit}}
</style></head><body>
<aside class="publication-tools" aria-label="Publishing controls"><strong>Medium publication draft · portable HTML</strong><p>Select and copy the article below into the editor, then upload the six original PNG figures from <code>docs/assets/</code> and retain their captions. Images are embedded here for offline reading; image transfer through the clipboard depends on the destination editor. This file has not been published.</p><div class="buttons"><button id="select-article" type="button">Select article for copying</button><button id="print-article" type="button">Print / save PDF</button></div><p id="selection-status" role="status"></p></aside>
<div class="masthead">FinGuard / Applied agent security<span>Implementation walkthrough · approximately ${Math.ceil(words / 220)} min read · experiment verified October 3, 2026</span></div>
<article id="article">${article}</article>
<footer>Publication source: docs/MEDIUM_ARTICLE.md. Includes six embedded figures and original source links. OpenShell software integration only; banking actions are simulated.</footer>
<script>document.getElementById('select-article').addEventListener('click',()=>{const range=document.createRange();range.selectNodeContents(document.getElementById('article'));const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);document.getElementById('selection-status').textContent='Article selected. Press Command+C on Mac or Ctrl+C on Windows to copy.';});document.getElementById('print-article').addEventListener('click',()=>window.print());</script>
</body></html>`;
fs.writeFileSync(path.join(docs, 'MEDIUM_ARTICLE.html'), html);
console.log('Built docs/MEDIUM_ARTICLE.html with six embedded figures');
