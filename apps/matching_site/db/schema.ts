import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
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
