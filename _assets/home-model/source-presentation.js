// Display the ranges recorded by the Workbench without changing authored text.
export function sourceParts(text, line, display, {types = true, notes = false} = {}, inFull = false) {
  const whole = [{kind: 'text', text}];
  if (inFull) return whole;
  const hidden = types ? [] : (display?.types || []).filter(span => span.line === line);
  const collapsed = notes ? [] : (display?.notes || []).filter(span => span.line === line);
  const valid = span => Number.isInteger(span.from) && Number.isInteger(span.to)
    && span.from >= 0 && span.to > span.from && span.to <= text.length;
  if (hidden.some(span => !valid(span)) || collapsed.some(span => !valid(span) || text.slice(span.from, span.to) !== span.text)) return whole;
  const ranges = [
    ...hidden.map(span => ({...span, kind: 'hidden'})),
    ...collapsed.filter(note => !hidden.some(span => note.from < span.to && note.to > span.from))
      .map(span => ({...span, kind: 'note'}))
  ].sort((a, b) => a.from - b.from || a.to - b.to);
  const parts = [];
  let position = 0;
  for (const span of ranges) {
    if (span.from < position) return whole;
    if (span.from > position) parts.push({kind: 'text', text: text.slice(position, span.from)});
    if (span.kind === 'note') parts.push({kind: 'note', text: text.slice(span.from, span.to)});
    position = span.to;
  }
  if (position < text.length) parts.push({kind: 'text', text: text.slice(position)});
  return parts.length ? parts : [{kind: 'text', text: ''}];
}
