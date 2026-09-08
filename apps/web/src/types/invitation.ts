/** design.md §3.1 Invitation — schema.md `invitations` 매핑. */
import type { FamilyRole } from "./family-member";

export type InvitationStatus = "pending" | "accepted" | "expired";

export interface Invitation {
  id: string;
  userId: string;
  invitedBy?: string;
  contact: string;
  role: FamilyRole;
  token: string;
  status: InvitationStatus;
  expiresAt: string;
}
