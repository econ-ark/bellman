/** Read source line ranges recorded by the native model exporter. */
export function linesForNode(collection, selection, filename, lineCount) {
  const graph = collection?.graphs?.find(item => item.id === selection?.graphId);
  const node = graph?.nodes?.find(item => item.id === selection?.nodeId);
  const record = node?.attrs?.find(item => item.key === 'lines')?.value;
  if (typeof record !== 'string' || !Number.isInteger(lineCount) || lineCount < 1) return [];
  const entry = record.split('; ').find(item => item.startsWith(filename + ' '));
  const ranges = entry?.slice(filename.length + 1);
  if (!ranges || !/^\d+(?:–\d+)?(?:, \d+(?:–\d+)?)*$/u.test(ranges)) return [];
  const lines = new Set();
  for (const range of ranges.split(', ')) {
    const [first, last = first] = range.split('–').map(Number);
    if (!Number.isSafeInteger(first) || !Number.isSafeInteger(last) || first < 1 || last < first || last > lineCount) return [];
    for (let line = first; line <= last; line++) lines.add(line);
  }
  return [...lines].sort((a, b) => a - b);
}
