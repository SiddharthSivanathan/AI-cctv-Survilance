/**
 * Shared type definitions for VisionOps AI.
 *
 * NOTE: Request/response DTOs for the REST API will be GENERATED from the
 * backend OpenAPI schema into this package (Phase 3+). The hand-written types
 * below are cross-cutting primitives that are stable across the platform.
 */

/** Roles map 1:1 to backend RBAC roles. Kept in sync with the API. */
export enum Role {
  Owner = 'owner',
  Admin = 'admin',
  Manager = 'manager',
  Analyst = 'analyst',
  Viewer = 'viewer',
}

/** Standard envelope returned by the API for successful responses. */
export interface ApiSuccess<T> {
  data: T;
  meta?: Record<string, unknown>;
}

/** Standard error envelope returned by the API. */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/** Cursor/offset pagination envelope. */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

/** A universally unique identifier (backend uses UUID v4/v7). */
export type UUID = string;

/** ISO-8601 timestamp string. */
export type ISODateTime = string;

export const ROLE_VALUES = Object.values(Role);
