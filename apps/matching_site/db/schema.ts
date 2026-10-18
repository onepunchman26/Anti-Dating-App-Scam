import { sqliteTable, text, integer, primaryKey, index, uniqueIndex } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
export const profiles = sqliteTable("profiles", {
  owner: text("owner").primaryKey(),
  publicId: text("public_id").notNull().unique(),
  summary: text("summary").notNull(),
  digest: text("digest").notNull(),
  revision: integer("revision").notNull(),
  lastSummaryVersion: integer("last_summary_version").notNull().default(0),
  active: integer("active").notNull(),
  updatedAt: text("updated_at").notNull(),
});
export const channelChecks = sqliteTable("channel_checks", {
  owner: text("owner").primaryKey(), marker: text("marker").notNull(),
});
export const queryLimits = sqliteTable("query_limits", {
  owner: text("owner").primaryKey(), window: integer("window").notNull(), count: integer("count").notNull(),
});
// The legacy table stays intact. Existing rows enter dating only, paused, when
// their authenticated owner next accesses the service.
export const participations = sqliteTable("participations", {
  owner: text("owner").notNull(),
  mode: text("mode").notNull(),
  publicId: text("public_id").notNull().unique(),
  summary: text("summary").notNull(),
  digest: text("digest").notNull(),
  revision: integer("revision").notNull(),
  lastSummaryVersion: integer("last_summary_version").notNull().default(0),
  active: integer("active").notNull().default(0),
  updatedAt: text("updated_at").notNull(),
}, table => [primaryKey({columns:[table.owner,table.mode]}),index("participations_mode_active").on(table.mode,table.active)]);

// One row is the concurrency boundary. Consent changes invalidate the current
// proposal and both confirmations in the same conditional update.
export const planningSessions = sqliteTable("planning_sessions", {
  id: text("id").primaryKey(),
  pairKey: text("pair_key").notNull().default(""),
  mode: text("mode").notNull(),
  ownerA: text("owner_a").notNull(),
  ownerB: text("owner_b").notNull(),
  publicA: text("public_a").notNull(),
  publicB: text("public_b").notNull(),
  status: text("status").notNull().default("pending"),
  revision: integer("revision").notNull().default(1),
  contextRevision: integer("context_revision").notNull().default(0),
  expiresAt: text("expires_at").notNull(),
  preferencesA: text("preferences_a").notNull().default("{}"),
  preferencesB: text("preferences_b").notNull().default("{}"),
  preferencesDigestA: text("preferences_digest_a").notNull().default(""),
  preferencesDigestB: text("preferences_digest_b").notNull().default(""),
  preferencesVersionA: integer("preferences_version_a").notNull().default(0),
  preferencesVersionB: integer("preferences_version_b").notNull().default(0),
  preferencesExpiresA: text("preferences_expires_a").notNull().default(""),
  preferencesExpiresB: text("preferences_expires_b").notNull().default(""),
  preferencesApprovedA: text("preferences_approved_a").notNull().default(""),
  preferencesApprovedB: text("preferences_approved_b").notNull().default(""),
  plan: text("plan").notNull().default("{}"),
  planDigest: text("plan_digest").notNull().default(""),
  planVersion: integer("plan_version").notNull().default(0),
  planApprovedBy: text("plan_approved_by").notNull().default(""),
  planApprovedAt: text("plan_approved_at").notNull().default(""),
  confirmationA: integer("confirmation_a").notNull().default(0),
  confirmationB: integer("confirmation_b").notNull().default(0),
  optionA: text("option_a").notNull().default(""),
  optionB: text("option_b").notNull().default(""),
  feedbackA: text("feedback_a").notNull().default(""),
  feedbackB: text("feedback_b").notNull().default(""),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
}, table => [index("planning_owner_a").on(table.ownerA),index("planning_owner_b").on(table.ownerB),uniqueIndex("planning_open_pair").on(table.pairKey,table.mode).where(sql`status NOT IN ('withdrawn','expired')`)]);
