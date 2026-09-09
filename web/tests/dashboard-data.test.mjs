import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/dashboard/data.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
const { createSampleArticles, summarizeArticles, lengthIndex } = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);

test('sample totals, chart partitions and publication calendar reconcile', () => {
  const articles = createSampleArticles();
  const result = summarizeArticles(articles, 2026, '2026-09-08');
  assert.equal(result.items.length, 128);
  assert.equal(result.annual.length, 80);
  assert.equal(result.words, 326000);
  assert.equal(result.totalViews, 38592);
  assert.equal(result.totalLikes, 2316);
  assert.equal(result.seriesCount, 12);
  assert.equal(result.seriesArticleCount, 96);
  assert.equal(result.dates.length, 42);
  assert.deepEqual(result.months.map(item => item.value), [8,10,7,12,9,11,8,11,4]);
  assert.deepEqual(result.categories.map(item => item.value), [56,32,24,16]);
  assert.deepEqual(result.lengths.map(item => item.value), [24,58,30,16]);
  assert.deepEqual(result.tags.map(item => item.value), [35,28,24,21,18,15,12,10]);
  assert.equal(result.dates.reduce((sum,item) => sum+item.value,0), result.annual.length);
  assert.ok(articles.every(item => item.views >= 0 && item.likes >= 0 && /^\d{4}-\d{2}-\d{2}$/.test(item.published)));
});

test('historical years exclude later publications and keep cumulative metrics distinct', () => {
  const result = summarizeArticles(createSampleArticles(), 2025, '2026-09-08');
  assert.equal(result.cutoff, '2025-12-31');
  assert.equal(result.items.length, 48);
  assert.equal(result.annual.length, 24);
  assert.equal(result.months.length, 12);
  assert.ok(result.items.every(item => item.published <= result.cutoff));
});

test('word bins are disjoint at every boundary and empty input is usable', () => {
  assert.deepEqual([0,999,1000,2999,3000,4999,5000].map(lengthIndex), [0,0,1,1,2,2,3]);
  const empty = summarizeArticles([], 2026, '2026-09-08');
  assert.equal(empty.totalViews, 0);
  assert.equal(empty.averageViews, 0);
  assert.equal(empty.averageLikes, '0');
  assert.deepEqual(empty.categories, []);
});
