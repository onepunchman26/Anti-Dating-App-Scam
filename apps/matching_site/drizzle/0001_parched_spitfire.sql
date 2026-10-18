ALTER TABLE `profiles` ADD `last_summary_version` integer DEFAULT 0 NOT NULL;
--> statement-breakpoint
UPDATE `profiles` SET `last_summary_version` = CAST(json_extract(`summary`, '$.version') AS INTEGER) WHERE `summary` != '{}';
