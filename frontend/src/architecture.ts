import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: true,
  theme: "base",
  securityLevel: "strict",
  flowchart: { curve: "basis", htmlLabels: true },
  themeVariables: {
    background: "#ffffff",
    primaryTextColor: "#202429",
    lineColor: "#929995",
    fontFamily: "Inter, Arial, sans-serif",
    fontSize: "13px",
  },
});
