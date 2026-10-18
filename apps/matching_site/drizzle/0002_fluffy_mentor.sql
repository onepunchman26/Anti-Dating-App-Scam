CREATE TABLE `participations` (
	`owner` text NOT NULL,
	`mode` text NOT NULL,
	`public_id` text NOT NULL,
	`summary` text NOT NULL,
	`digest` text NOT NULL,
	`revision` integer NOT NULL,
	`last_summary_version` integer DEFAULT 0 NOT NULL,
	`active` integer DEFAULT 0 NOT NULL,
	`updated_at` text NOT NULL,
	PRIMARY KEY(`owner`, `mode`)
);
--> statement-breakpoint
CREATE UNIQUE INDEX `participations_public_id_unique` ON `participations` (`public_id`);--> statement-breakpoint
CREATE INDEX `participations_mode_active` ON `participations` (`mode`,`active`);--> statement-breakpoint
CREATE TABLE `planning_sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`mode` text NOT NULL,
	`owner_a` text NOT NULL,
	`owner_b` text NOT NULL,
	`public_a` text NOT NULL,
	`public_b` text NOT NULL,
	`status` text DEFAULT 'pending' NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`expires_at` text NOT NULL,
	`preferences_a` text DEFAULT '{}' NOT NULL,
	`preferences_b` text DEFAULT '{}' NOT NULL,
	`preferences_digest_a` text DEFAULT '' NOT NULL,
	`preferences_digest_b` text DEFAULT '' NOT NULL,
	`preferences_version_a` integer DEFAULT 0 NOT NULL,
	`preferences_version_b` integer DEFAULT 0 NOT NULL,
	`preferences_expires_a` text DEFAULT '' NOT NULL,
	`preferences_expires_b` text DEFAULT '' NOT NULL,
	`plan` text DEFAULT '{}' NOT NULL,
	`plan_digest` text DEFAULT '' NOT NULL,
	`plan_version` integer DEFAULT 0 NOT NULL,
	`confirmation_a` integer DEFAULT 0 NOT NULL,
	`confirmation_b` integer DEFAULT 0 NOT NULL,
	`feedback_a` text DEFAULT '' NOT NULL,
	`feedback_b` text DEFAULT '' NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `planning_owner_a` ON `planning_sessions` (`owner_a`);--> statement-breakpoint
CREATE INDEX `planning_owner_b` ON `planning_sessions` (`owner_b`);