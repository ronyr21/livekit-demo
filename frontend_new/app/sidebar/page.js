'use client';
import {
  LayoutDashboard,
  PhoneCall,
  History,
  Users,
  BarChart,
  LogOut,
} from 'lucide-react';
import Image from "next/image";
import styles from "./sidebar.module.css";

export default function Sidebar({ activeSection, setActiveSection }) {
  const sections = [
    { name: 'Overview', icon: LayoutDashboard },
    { name: 'Live Calls', icon: PhoneCall },
    { name: 'Call History', icon: History },
    { name: 'Manage Agents', icon: Users },
    { name: 'Dashboard', icon: BarChart },
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <Image
          src="/CME_Logo.png"
          alt="CME Logo"
          width={60}
          height={20}
          style={{ objectFit: "contain", cursor: "pointer" }}
        />
      </div>
      <nav className={styles.sectionsNav}>
        {sections.map((section, idx) => {
          const isActive = section.name === activeSection;
          const color = isActive ? '#9443d0' : '#b6b9d2';
          const Icon = section.icon;
          const borderStyle = isActive
            ? { borderRight: "3px solid #9443d0" }
            : { borderRight: "3px solid transparent" };

          return (
            <div
              key={idx}
              className={styles.sectionItem}
              style={{
                color,
                ...borderStyle,
              }}
              onClick={() => setActiveSection(section.name)}
              role="button"
              tabIndex={0}
            >
              <Icon size={18} color={color} />
              {section.name}
            </div>
          );
        })}
      </nav>
      <div className={styles.signOutWrapper}>
        <button
          className={styles.signOutButton}
        >
          <LogOut size={18} color="#b6b9d2" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
