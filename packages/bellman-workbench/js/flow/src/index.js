// The entry of the graph's bundle (model interface specification 0.4, §7):
// the libraries set on window (globals.js), then flow-layout.js, which
// defines window.BellmanFlowLayout, then flow-canvas.js, which defines
// window.BellmanFlow. BellmanFlow.layout holds the layout's six functions
// with the page's measure, which the page tests call (G-D14; AAS, L-D20;
// design pass 13 §§1 and 2).
import "./globals.js";
import "./flow-layout.js";
import "./flow-canvas.js";

window.BellmanFlow.layout = {
  model: window.BellmanFlowLayout.model,
  build: window.BellmanFlowLayout.build,
  columnWidths: window.BellmanFlowLayout.columnWidths,
  arrange: window.BellmanFlowLayout.arrange,
  settle: window.BellmanFlowLayout.settle,
  read: window.BellmanFlowLayout.read,
  measure: window.BellmanFlow.measure,
};
