/** design.md §3.1 Question — schema.md `questions` 매핑. */
export interface Question {
  id: string;
  userId: string;
  linkedChapterId?: string;
  text: string;
  type: "new_topic" | "follow_up";
  answered: boolean;
}
