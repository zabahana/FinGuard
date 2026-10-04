/* Build an allowlisted, import-ready public article; never copy the repository. */
const fs=require('node:fs'),path=require('node:path');
const {marked}=require('marked');
const root=path.resolve(__dirname,'..'),docs=path.join(root,'docs');
const base=process.env.FINGUARD_PAGES_URL||'https://zabahana.github.io/FinGuard/';
if(!/^https:\/\/zabahana\.github\.io\/[A-Za-z0-9_-]+\/$/.test(base))throw Error('Unexpected Pages URL');
const out=path.join(root,'artifacts/github-pages');
fs.mkdirSync(path.join(out,'assets'),{recursive:true});
const source=fs.readFileSync(path.join(docs,'MEDIUM_ARTICLE.md'),'utf8');
const title=source.split('\n')[0].replace(/^# /,'');
const escape=t=>t.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const figures=['model-behavior','safety-outcomes','attack-lab-results','attack-catalogue','model-evaluation','prompt-injection-story','workspace'];
let article=marked.parse(source,{gfm:true});
for(const name of figures){
 const filename=`${name}.png`;
 fs.copyFileSync(path.join(docs,'assets',filename),path.join(out,'assets',filename));
 article=article.replaceAll(`src="assets/${filename}"`,`src="${base}assets/${filename}"`);
}
if(/src="assets\/|src="data:/.test(article))throw Error('Unpublished or embedded image');
article=article.replace(/<p>(<img[^>]+>)<\/p>\s*<p><em>(Figure \d+\.[\s\S]*?)<\/em><\/p>/g,'<figure>$1<figcaption>$2</figcaption></figure>');
const offline=fs.readFileSync(path.join(docs,'MEDIUM_ARTICLE.html'),'utf8');
const css=offline.match(/<style>([\s\S]*?)<\/style>/)[1];
const html=`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(title)}</title><meta name="description" content="Testing application authorization, runtime isolation, prompt injection, and control ablation with NVIDIA OpenShell.">
<link rel="canonical" href="${base}"><meta property="og:type" content="article"><meta property="og:title" content="${escape(title)}"><meta property="og:url" content="${base}"><meta property="og:image" content="${base}assets/model-behavior.png">
<style>${css}</style></head><body>
<div class="masthead">FinGuard / Applied agent security<span>Security engineering field notes</span></div>
<article id="article">${article}</article>
<footer>Article and figures published for reading and import. Explore the <a href="https://github.com/zabahana/FinGuard">public source repository</a> or contact <a href="mailto:zga5029@psu.edu">zga5029@psu.edu</a> for a demo. Banking actions are simulated.</footer>
</body></html>`;
fs.writeFileSync(path.join(out,'index.html'),html);
fs.writeFileSync(path.join(out,'.nojekyll'),'');
console.log(`Built public article and ${figures.length} PNGs in artifacts/github-pages for ${base}`);
