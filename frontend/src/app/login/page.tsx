"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { apiRequest } from "@/src/shared/api/client";

type TokenPair = {
    access_token: string;
    refresh_token: string;
    token_type: string;
};

export default function LoginPage() {
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const data = await apiRequest<TokenPair>("/auth/login", {
                method: "POST",
                body: { email, password },
            });

            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);

            router.push("/profile");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <main className="mx-auto max-w-md p-6">
            <h1 className="mb-6 text-2xl font-bold">Login</h1>

            <form onSubmit={handleSubmit} className="space-y-4">
                <input
                    className="w-full rounded border p-3"
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                />

                <input
                    className="w-full rounded border p-3"
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                />

                {error ? <p className="text-sm text-red-600">{error}</p> : null}

                <button
                    className="w-full rounded bg-black px-4 py-3 text-white disabled:opacity-50"
                    type="submit"
                    disabled={isLoading}
                >
                    {isLoading ? "Logging in..." : "Login"}
                </button>
            </form>
        </main>
    );
}