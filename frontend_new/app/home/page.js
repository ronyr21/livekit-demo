"use client";

import { useState } from "react";
import Sidebar from "../sidebar/page";
import Content from "../content/page";
import Footer from "../footer/Footer";
import styles from "./home.module.css";

export default function HomePage() {
  const [activeSection, setActiveSection] = useState("Live Calls");

  return (
    <div className={styles.homeLayout}>
      <div className={styles.sidebarWrapper}>
        <Sidebar activeSection={activeSection} setActiveSection={setActiveSection} />
      </div>
      <div className={styles.contentWrapper}>
        <Content activeSection={activeSection} />
        <Footer />
      </div>
    </div>
  );
}
