/** Export source ranges with the Workbench's type and note functions. */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

import { hiddenRanges } from '../../packages/bellman-workbench/js/codemirror/src/hidden_types.js';

const files = [
  'packages/bellman-workbench/js/codemirror/src/hidden_types.js',
  'packages/bellman-workbench/bellman_workbench/public/codemirror/bellman-workbench.js',
];
const native = files.map(path => readFileSync(new URL('../../' + path, import.meta.url)));
const native_sha256 = Object.fromEntries(files.map((path, index) => [
  path, createHash('sha256').update(native[index]).digest('hex'),
]));
const context = {};
vm.runInNewContext(native[1].toString('utf8'), context);

const texts = JSON.parse(readFileSync(0, 'utf8'));
const displays = Object.fromEntries(Object.entries(texts).map(([name, text]) => {
  if (typeof text !== 'string') throw new TypeError('Each source must be text.');
  return [name, {
    types: hiddenRanges(text.split(/\r\n?|\n/)).map(range => ({...range, line: range.line + 1})),
    notes: context.bellmanEditor.noteMarkersOf(text),
    native_sha256,
  }];
}));
process.stdout.write(JSON.stringify(displays));
