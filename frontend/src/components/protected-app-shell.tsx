"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { getAccessToken } from "@/src/shared/lib/auth";

type ProtectedAppShellProps = {
  children: React.ReactNode;
};

export default function ProtectedAppShell({
  children,
}: ProtectedAppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      const search = searchParams?.toString();
      const fullPath = `${pathname}${search ? `?${search}` : ""}`;
      const next =
        fullPath && fullPath !== "/" ? `?next=${encodeURIComponent(fullPath)}` : "";

      router.replace(`/login${next}`);
      return;
    }

    setIsCheckingAuth(false);
  }, [pathname, router, searchParams]);

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