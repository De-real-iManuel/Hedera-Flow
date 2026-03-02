// Polyfill for buffer (required by HashConnect and crypto libraries)
import { Buffer } from 'buffer';
window.Buffer = Buffer;

import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
