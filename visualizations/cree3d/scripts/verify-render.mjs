import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const url = process.env.APP_URL || 'http://127.0.0.1:4173';
const outputDir = fileURLToPath(new URL('../artifacts', import.meta.url));

const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
];

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });

try {
  for (const viewport of viewports) {
    const page = await browser.newPage({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      isMobile: viewport.name === 'mobile',
    });

    await page.goto(url, { waitUntil: 'networkidle' });
    const canvas = await page.waitForSelector('canvas', { timeout: 10000 });
    await page.waitForTimeout(1200);

    const stats = await page.evaluate(() => {
      const source = document.querySelector('canvas');
      if (!source) throw new Error('Missing WebGL canvas');

      const probe = document.createElement('canvas');
      probe.width = 120;
      probe.height = 80;
      const ctx = probe.getContext('2d', { willReadFrequently: true });
      if (!ctx) throw new Error('Missing 2D probe context');

      ctx.drawImage(source, 0, 0, probe.width, probe.height);
      const pixels = ctx.getImageData(0, 0, probe.width, probe.height).data;
      let nonBackground = 0;
      const buckets = new Set();

      for (let idx = 0; idx < pixels.length; idx += 4) {
        const red = pixels[idx];
        const green = pixels[idx + 1];
        const blue = pixels[idx + 2];
        const distance = Math.abs(red - 248) + Math.abs(green - 250) + Math.abs(blue - 252);
        if (distance > 22) nonBackground += 1;
        buckets.add(`${red >> 4}-${green >> 4}-${blue >> 4}`);
      }

      return {
        width: source.clientWidth,
        height: source.clientHeight,
        nonBackgroundRatio: nonBackground / (pixels.length / 4),
        colorBuckets: buckets.size,
      };
    });

    const box = await canvas.boundingBox();
    if (!box || box.width < viewport.width * 0.95 || box.height < viewport.height * 0.95) {
      throw new Error(`${viewport.name}: canvas is not full-bleed enough: ${JSON.stringify(box)}`);
    }
    if (stats.nonBackgroundRatio < 0.002 || stats.colorBuckets < 10) {
      throw new Error(`${viewport.name}: canvas appears blank: ${JSON.stringify(stats)}`);
    }

    const screenshotPath = join(outputDir, `${viewport.name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`${viewport.name}: ${JSON.stringify({ ...stats, screenshotPath })}`);
    await page.close();
  }
} finally {
  await browser.close();
}
