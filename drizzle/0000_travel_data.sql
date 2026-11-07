CREATE TABLE `dataset_state` (
	`id` integer PRIMARY KEY NOT NULL,
	`revision` integer NOT NULL,
	CONSTRAINT "dataset_state_singleton" CHECK("dataset_state"."id" = 1),
	CONSTRAINT "dataset_state_revision_positive" CHECK("dataset_state"."revision" > 0)
);
--> statement-breakpoint
CREATE TABLE `trip_documents` (
	`slug` text NOT NULL,
	`kind` text NOT NULL,
	`body` text NOT NULL,
	PRIMARY KEY(`slug`, `kind`),
	FOREIGN KEY (`slug`) REFERENCES `trips`(`slug`) ON UPDATE no action ON DELETE cascade,
	CONSTRAINT "trip_documents_kind_valid" CHECK("trip_documents"."kind" IN ('plan', 'i18n', 'weather')),
	CONSTRAINT "trip_documents_body_valid" CHECK(json_valid("trip_documents"."body"))
);
--> statement-breakpoint
CREATE TABLE `trips` (
	`slug` text PRIMARY KEY NOT NULL,
	`name_json` text NOT NULL,
	`starts_on` text NOT NULL,
	`ends_on` text NOT NULL,
	`timezone` text NOT NULL,
	`weather_checked_at` integer DEFAULT 0 NOT NULL,
	CONSTRAINT "trips_name_valid" CHECK(json_valid("trips"."name_json")),
	CONSTRAINT "trips_date_range" CHECK("trips"."ends_on" >= "trips"."starts_on")
);
