CREATE TABLE social_accounts (
 scope text NOT NULL, owner text NOT NULL, public_id text NOT NULL,
 alias text NOT NULL, discoverable integer NOT NULL DEFAULT 0,
 revision integer NOT NULL DEFAULT 1, created_at text NOT NULL,
 PRIMARY KEY(scope,owner), UNIQUE(scope,public_id)
);--> statement-breakpoint
CREATE TABLE social_friends (
 scope text NOT NULL, pair_key text NOT NULL, sender text NOT NULL,
 recipient text NOT NULL, status text NOT NULL, blocked_by text NOT NULL DEFAULT '',
 revision integer NOT NULL DEFAULT 1, updated_at text NOT NULL,
 PRIMARY KEY(scope,pair_key)
);--> statement-breakpoint
CREATE INDEX social_friends_sender ON social_friends(scope,sender);--> statement-breakpoint
CREATE INDEX social_friends_recipient ON social_friends(scope,recipient);--> statement-breakpoint
CREATE TABLE social_groups (
 id text PRIMARY KEY NOT NULL, scope text NOT NULL, revision integer NOT NULL DEFAULT 1,
 data text NOT NULL, expires_at text NOT NULL, updated_at text NOT NULL
);--> statement-breakpoint
CREATE INDEX social_groups_scope ON social_groups(scope,updated_at);
