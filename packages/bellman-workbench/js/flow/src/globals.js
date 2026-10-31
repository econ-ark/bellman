// The libraries the two scripts of this folder read from the page's window,
// set before either script runs: React, React DOM's client entry and React
// Flow.
import * as React from "react";
import { createPortal } from "react-dom";
import * as ReactDOMClient from "react-dom/client";
import * as ReactFlow from "@xyflow/react";

window.React = React;
window.ReactDOM = { ...ReactDOMClient, createPortal };
window.ReactFlow = ReactFlow;
