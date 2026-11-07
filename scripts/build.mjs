import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('../', import.meta.url);
const web = new URL('web/', root);
const seed = new URL('worker/seed/', root);
const parse = async (base, path) => JSON.parse(await readFile(new URL(path, base), 'utf8'));
const revision = Number(await readFile(new URL('revision.txt', seed), 'utf8'));
if (!Number.isSafeInteger(revision) || revision < 1) throw new Error('데이터 버전은 양의 정수여야 합니다.');

const trips = await parse(seed, 'trips.json');
const records = [];
const slugs = new Set();
for (const trip of trips) {
  const { slug } = trip;
  if (!/^\d{4}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slugs.has(slug)) {
    throw new Error(`잘못되었거나 중복된 여행 슬러그: ${slug}`);
  }
  slugs.add(slug);
  const plan = await parse(seed, `${slug}/plan.json`);
  const { timezone } = plan.trip;
  new Intl.DateTimeFormat('ko', { timeZone: timezone });
  const documents = { plan };
  for (const kind of ['i18n', 'weather']) {
    try {
      documents[kind] = await parse(seed, `${slug}/${kind}.json`);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  records.push({ ...trip, timezone, documents });
}

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
for (const slug of slugs) {
  if (!assets[`/travle-plan/${slug}/index.html`]) throw new Error(`여행 페이지가 없습니다: ${slug}`);
}
const modules = await Promise.all(['weather.js', 'index.js'].map((name) =>
  readFile(new URL('worker/' + name, root), 'utf8')));
const output = new URL('dist/server/', root);
await mkdir(output, { recursive: true });
await writeFile(new URL('index.js', output),
  `const assets = ${JSON.stringify(assets)};\nconst dataset = ${JSON.stringify({ revision, records })};\n${modules.join('\n')}`);
