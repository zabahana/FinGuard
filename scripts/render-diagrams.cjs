/* Build-time only: render local Mermaid sources into offline SVG and PNG assets.
 * Usage: node scripts/render-diagrams.cjs /path/to/mermaid.min.js
 * Requires playwright-core (NODE_PATH may point to an existing installation).
 * Uses installed Chrome; set CHROME_PATH for another installation.
 */
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright-core');

(async () => {
  if (!process.argv[2]) throw new Error('Provide the local Mermaid 11.12.0 browser bundle');
  const root = path.resolve(__dirname, '..', 'docs');
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
    await page.route('http://**/*', route => route.abort());
    await page.route('https://**/*', route => route.abort());
    await page.setContent('<!doctype html><html><body style="margin:24px;background:white"><main></main></body></html>');
    await page.addScriptTag({ path: path.resolve(process.argv[2]) });
    await page.evaluate(() => mermaid.initialize({ startOnLoad: false, securityLevel: 'strict',
      theme: 'base', themeVariables: { fontFamily: 'Arial', fontSize: '16px',
        primaryColor: '#edf6f2', primaryTextColor: '#132f29', primaryBorderColor: '#487366',
        lineColor: '#526c64', secondaryColor: '#f5f7fa', tertiaryColor: '#ffffff',
        clusterBkg: '#f6f8f7', clusterBorder: '#aebeb7' },
      flowchart: { htmlLabels: false, useMaxWidth: false, curve: 'linear' },
      sequence: { useMaxWidth: false, wrap: true, width: 180 } }));
    await fs.mkdir(path.join(root, 'assets'), { recursive: true });
    for (const filename of (await fs.readdir(path.join(root, 'diagrams'))).filter(f => f.endsWith('.mmd')).sort()) {
      const name = path.basename(filename, '.mmd');
      const source = await fs.readFile(path.join(root, 'diagrams', filename), 'utf8');
      const svg = await page.evaluate(async ({name, source}) => {
        const result = await mermaid.render('diagram-' + name, source);
        document.querySelector('main').innerHTML = result.svg;
        return result.svg;
      }, { name, source });
      await fs.writeFile(path.join(root, 'assets', name + '.svg'), svg);
      await page.locator('main svg').screenshot({ path: path.join(root, 'assets', name + '.png') });
      console.log('Rendered and parsed ' + name);
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
