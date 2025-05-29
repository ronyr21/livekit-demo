"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Simulate login check. Replace with real auth logic when available.
    const isLoggedIn = true; // Set to true to simulate logged-in state

    if (isLoggedIn) {
      router.replace("/home");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div>
      {/* Optionally, show a loading spinner or message here */}
      Redirecting...
    </div>
  );
}
