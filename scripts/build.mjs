import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('../', import.meta.url);
const web = new URL('web/', root);

const assets = {};
const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
};
async function collect(directory = '') {
  const entries = await readdir(new URL(`${directory}/`.replace(/^\//, ''), web), { withFileTypes: true });
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const path = directory ? join(directory, entry.name) : entry.name;
    if (entry.isDirectory()) {
      await collect(path);
      continue;
    }
    const extension = path.slice(path.lastIndexOf('.'));
    if (!entry.isFile() || !types[extension]) throw new Error(`지원하지 않는 웹 파일: ${path}`);
    const body = await readFile(new URL(path, web));
    assets['/' + path] = [types[extension], body.toString(extension === '.png' ? 'base64' : 'utf8')];
  }
}
await collect();
const modules = await Promise.all(['weather.js', 'index.js'].map((name) =>
  readFile(new URL('worker/' + name, root), 'utf8')));
const output = new URL('dist/server/', root);
await mkdir(output, { recursive: true });
await writeFile(new URL('index.js', output),
  `const assets = ${JSON.stringify(assets)};\n${modules.join('\n')}`);
