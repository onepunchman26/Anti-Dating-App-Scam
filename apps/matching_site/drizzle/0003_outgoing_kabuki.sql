ALTER TABLE `planning_sessions` ADD `context_revision` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `preferences_approved_a` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `preferences_approved_b` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `plan_approved_by` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `plan_approved_at` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `option_a` text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `option_b` text DEFAULT '' NOT NULL;