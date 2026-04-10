"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getAccessToken } from "@/src/shared/lib/auth";

type ProtectedAppShellProps = {
  children: React.ReactNode;
};

export default function ProtectedAppShell({
  children,
}: ProtectedAppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      const next = pathname && pathname !== "/" ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
      return;
    }

    setIsCheckingAuth(false);
  }, [pathname, router]);

  if (isCheckingAuth) {
    return (
      <main>
        <section>
          <h2>Checking authorization...</h2>
          <p>Please wait while we verify your session.</p>
        </section>
      </main>
    );
  }

  return <>{children}</>;
}