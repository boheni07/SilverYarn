import Link from "next/link";
import { getInvitation } from "@/services/invitations";
import { AcceptInvitationForm } from "@/features/invitations/AcceptInvitationForm";
import { ApiError } from "@/services/errors";
import { FAMILY_ROLE_LABEL } from "@/types";

interface AcceptInvitationPageProps {
  params: Promise<{ token: string }>;
}

const STATUS_MESSAGE: Record<string, string> = {
  accepted: "이미 수락된 초대입니다.",
  expired: "만료된 초대입니다. 초대한 분께 새 링크를 요청해 주세요.",
};

/**
 * design.md §2.9 "가족 계정 웹 콘솔 초대" 수락 화면(신규) — admin이 만든 초대
 * 링크(`/invitations/{token}`)로 들어온 가족이 로그인 후 여기서 수락한다.
 * Next.js 16 `proxy.ts`가 미로그인 요청을 이미 `/login?callbackUrl=...`로
 * 돌려보내므로, 이 페이지는 로그인된 상태만 가정한다.
 */
export default async function AcceptInvitationPage({ params }: AcceptInvitationPageProps) {
  const { token } = await params;

  let invitation;
  try {
    invitation = await getInvitation(token);
  } catch (e) {
    const message = e instanceof ApiError ? e.message : "초대를 찾을 수 없습니다.";
    return (
      <main className="mx-auto max-w-md px-4 py-12">
        <p className="text-ink-muted">{message}</p>
      </main>
    );
  }

  if (invitation.status !== "pending") {
    return (
      <main className="mx-auto max-w-md px-4 py-12">
        <p className="text-ink-muted">{STATUS_MESSAGE[invitation.status] ?? "처리할 수 없는 초대입니다."}</p>
        <Link href="/" className="mt-4 inline-block text-teal-deep underline">
          처음으로
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md px-4 py-12">
      <h1 className="font-editorial text-h1 font-bold text-ink">초대 수락</h1>
      <p className="mt-2 text-ink-muted">
        {FAMILY_ROLE_LABEL[invitation.role]}(으)로 초대받았습니다. 아래에 이름을 입력하고
        수락하면 이 계정으로 로그인해 어르신의 자서전을 함께 만들 수 있습니다.
      </p>

      <div className="mt-6">
        <AcceptInvitationForm token={token} />
      </div>
    </main>
  );
}
