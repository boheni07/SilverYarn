"use server";

import { createOrganization } from "@/services/organizations";
import { setUserOrganization } from "@/services/users";
import { ApiError } from "@/services/errors";
import type { Organization, User } from "@/types";

export type ActionResult = { ok: true; organization: Organization } | { ok: false; error: string };

export async function createOrganizationAction(name: string): Promise<ActionResult> {
  try {
    const organization = await createOrganization(name);
    return { ok: true, organization };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "시설 등록 중 오류가 발생했습니다." };
  }
}

export type AssignResult = { ok: true; user: User } | { ok: false; error: string };

export async function assignUserOrganizationAction(
  userId: string,
  orgId: string | null,
): Promise<AssignResult> {
  try {
    const user = await setUserOrganization(userId, orgId);
    return { ok: true, user };
  } catch (e) {
    return { ok: false, error: e instanceof ApiError ? e.message : "시설 배정 중 오류가 발생했습니다." };
  }
}
