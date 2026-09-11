"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { acceptInvitationAction } from "./actions";

export function AcceptInvitationForm({ token }: { token: string }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!name.trim()) return;
    setPending(true);
    setError(null);
    const result = await acceptInvitationAction(token, name.trim());
    setPending(false);
    if (result.ok) {
      router.push("/");
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="rounded-xl border border-border-soft bg-surface p-6 shadow-sm">
      <label className="block text-caption text-ink-muted">
        본인 이름
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="가족 웹 콘솔에 표시될 이름"
          className="mt-1 block min-h-11 w-full rounded-lg border border-border bg-paper px-3 text-body-compact text-ink"
        />
      </label>

      {error && <p className="mt-3 text-caption text-ink">{error}</p>}

      <Button className="mt-4 w-full" onClick={handleSubmit} disabled={pending || !name.trim()}>
        {pending ? "수락하는 중…" : "초대 수락하기"}
      </Button>
    </div>
  );
}
