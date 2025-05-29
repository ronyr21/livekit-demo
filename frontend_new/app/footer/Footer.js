export default function Footer() {
  return (
    <footer
      style={{
        width: "100%",
        position: "relative",
        left: 0,
        bottom: 0,
        padding: "16px 0",
        textAlign: "center",
        color: "#b6b9d2",
        fontSize: 12,
        background: "#F4F7FE",
        borderTop: "1px solid #f0f0f0",
        zIndex: 100,
      }}
    >
      &copy; {new Date().getFullYear()} CME. All rights reserved.
    </footer>
  );
}
