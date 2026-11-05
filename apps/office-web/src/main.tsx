import React from "react";
import ReactDOM from "react-dom/client";
import { OfficeApp } from "./office-app";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <OfficeApp />
  </React.StrictMode>,
);
