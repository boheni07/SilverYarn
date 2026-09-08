/**
 * 서버 wire format은 snake_case로 통일돼 있다(decisions.md #20). 웹(TS)은 자체
 * 컨벤션(camelCase)으로 변환해서 쓴다(glossary.md 규칙 7). 이 변환은 여기 한 곳에서만
 * 일어나야 한다 — services/ 아래 각 API 함수가 매번 손으로 필드명을 바꾸지 않도록.
 */

type JsonValue = string | number | boolean | null | undefined | JsonValue[] | { [key: string]: JsonValue };

function snakeToCamel(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

function camelToSnake(key: string): string {
  return key.replace(/([A-Z])/g, (letter) => `_${letter.toLowerCase()}`);
}

function isPlainObject(value: unknown): value is Record<string, JsonValue> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function keysToCamel<T = unknown>(value: JsonValue): T {
  if (Array.isArray(value)) {
    return value.map((item) => keysToCamel(item)) as T;
  }
  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      result[snakeToCamel(key)] = keysToCamel(val);
    }
    return result as T;
  }
  return value as T;
}

export function keysToSnake(value: unknown): JsonValue {
  if (Array.isArray(value)) {
    return value.map((item) => keysToSnake(item));
  }
  if (isPlainObject(value)) {
    const result: Record<string, JsonValue> = {};
    for (const [key, val] of Object.entries(value)) {
      result[camelToSnake(key)] = keysToSnake(val);
    }
    return result;
  }
  return value as JsonValue;
}
