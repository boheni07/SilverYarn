import { apiClient } from "@/lib/api/client";
import type { User } from "@/types";

export async function getUser(userId: string): Promise<User> {
  return apiClient.get<User>(`/users/${userId}`, { authToken: "dev" });
}
