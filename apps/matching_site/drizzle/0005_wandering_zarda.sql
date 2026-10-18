CREATE TABLE `test_enrollments` (
	`account_fingerprint` text PRIMARY KEY NOT NULL,
	`scope` text NOT NULL,
	`enrolled_at` text NOT NULL
);
--> statement-breakpoint
ALTER TABLE `participations` ADD `scope` text DEFAULT 'production' NOT NULL;--> statement-breakpoint
CREATE INDEX `participations_scope_mode_active` ON `participations` (`scope`,`mode`,`active`);--> statement-breakpoint
ALTER TABLE `planning_sessions` ADD `scope` text DEFAULT 'production' NOT NULL;