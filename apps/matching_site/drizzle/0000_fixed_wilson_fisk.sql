CREATE TABLE `channel_checks` (
	`owner` text PRIMARY KEY NOT NULL,
	`marker` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `profiles` (
	`owner` text PRIMARY KEY NOT NULL,
	`public_id` text NOT NULL,
	`summary` text NOT NULL,
	`digest` text NOT NULL,
	`revision` integer NOT NULL,
	`active` integer NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `profiles_public_id_unique` ON `profiles` (`public_id`);--> statement-breakpoint
CREATE TABLE `query_limits` (
	`owner` text PRIMARY KEY NOT NULL,
	`window` integer NOT NULL,
	`count` integer NOT NULL
);
