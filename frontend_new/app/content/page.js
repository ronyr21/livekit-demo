"use client";

import { useState } from "react";
import LiveCalls from "./sections/LiveCalls";
import Overview from "./sections/Overview";
import CallHistory from "./sections/CallHistory";
import ManageAgents from "./sections/ManageAgents";
import Dashboard from "./sections/Dashboard";

const sectionComponents = {
  "Live Calls": LiveCalls,
  "Overview": Overview,
  "Call History": CallHistory,
  "Manage Agents": ManageAgents,
  "Dashboard": Dashboard,
};

export default function Content({ activeSection = "Live Calls" }) {
  const SectionComponent = sectionComponents[activeSection] || LiveCalls;
  return <SectionComponent />;
}
