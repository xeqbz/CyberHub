import { useCurrentUserContext } from "@/src/components/current-user-provider";

export function useCurrentUser() {
  return useCurrentUserContext();
}