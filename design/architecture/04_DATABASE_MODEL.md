# Modèle de données PostgreSQL - Aurelia

## Tables principales

### users
- id UUID PK
- username TEXT UNIQUE NOT NULL
- password_hash TEXT NOT NULL
- display_name TEXT
- created_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ
- last_login_at TIMESTAMPTZ

### books
- id UUID PK
- title TEXT NOT NULL
- subtitle TEXT
- description TEXT
- language TEXT
- isbn TEXT
- publisher TEXT
- published_date TEXT
- original_filename TEXT
- file_path TEXT NOT NULL
- file_size BIGINT
- file_hash TEXT UNIQUE
- cover_path TEXT
- metadata_source TEXT
- metadata_provider_id TEXT
- status TEXT NOT NULL DEFAULT 'unread'
- rating INTEGER CHECK rating BETWEEN 0 AND 5
- favorite BOOLEAN DEFAULT FALSE
- added_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ
- last_opened_at TIMESTAMPTZ
- deleted_at TIMESTAMPTZ NULL

Statuts possibles :
- unread
- in_progress
- finished
- abandoned

### authors
- id UUID PK
- name TEXT UNIQUE NOT NULL
- sort_name TEXT
- created_at TIMESTAMPTZ

### book_authors
- book_id UUID FK books
- author_id UUID FK authors
- position INTEGER DEFAULT 0

PK :
- book_id
- author_id

### series
- id UUID PK
- name TEXT UNIQUE NOT NULL
- description TEXT
- created_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ

### book_series
- book_id UUID FK books UNIQUE
- series_id UUID FK series
- series_index NUMERIC
- series_label TEXT

### tags
- id UUID PK
- name TEXT UNIQUE NOT NULL
- color TEXT
- created_at TIMESTAMPTZ

### book_tags
- book_id UUID FK books
- tag_id UUID FK tags

PK :
- book_id
- tag_id

### collections
- id UUID PK
- name TEXT UNIQUE NOT NULL
- description TEXT
- cover_book_id UUID NULL
- created_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ

### collection_books
- collection_id UUID FK collections
- book_id UUID FK books
- position INTEGER
- added_at TIMESTAMPTZ

PK :
- collection_id
- book_id

### reading_progress
- id UUID PK
- user_id UUID FK users
- book_id UUID FK books
- cfi TEXT
- progress_percent NUMERIC CHECK progress_percent >= 0 AND progress_percent <= 100
- chapter_label TEXT
- chapter_href TEXT
- location_json JSONB
- device_id TEXT
- updated_at TIMESTAMPTZ
- created_at TIMESTAMPTZ

Contrainte :
- UNIQUE user_id, book_id

### bookmarks
- id UUID PK
- user_id UUID FK users
- book_id UUID FK books
- cfi TEXT NOT NULL
- progress_percent NUMERIC
- chapter_label TEXT
- excerpt TEXT
- note TEXT
- created_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ
- deleted_at TIMESTAMPTZ NULL

### reading_settings
- id UUID PK
- user_id UUID FK users UNIQUE
- theme TEXT DEFAULT 'system'
- reader_theme TEXT DEFAULT 'black_gold'
- font_family TEXT
- font_size INTEGER DEFAULT 18
- line_height NUMERIC DEFAULT 1.6
- margin_size INTEGER DEFAULT 24
- reading_mode TEXT DEFAULT 'paged'
- updated_at TIMESTAMPTZ

reading_mode :
- paged
- scroll

### import_jobs
- id UUID PK
- source TEXT NOT NULL
- status TEXT NOT NULL
- filename TEXT
- file_path TEXT
- error_message TEXT
- result_book_id UUID NULL
- created_at TIMESTAMPTZ
- started_at TIMESTAMPTZ
- finished_at TIMESTAMPTZ

source :
- upload
- scan

status :
- pending
- running
- success
- warning
- failed

### metadata_provider_results
- id UUID PK
- book_id UUID FK books NULL
- provider TEXT NOT NULL
- provider_item_id TEXT
- query TEXT
- raw_json JSONB
- normalized_json JSONB
- score NUMERIC
- created_at TIMESTAMPTZ

### sync_events
Optionnel serveur pour audit sync.
- id UUID PK
- user_id UUID FK users
- device_id TEXT
- event_type TEXT
- payload JSONB
- client_created_at TIMESTAMPTZ
- received_at TIMESTAMPTZ
- processed_at TIMESTAMPTZ
- status TEXT

## Index recommandés

books :
- index title gin/trgm si possible
- index file_hash
- index status
- index added_at
- index last_opened_at
- index rating

reading_progress :
- unique user_id, book_id
- index updated_at

bookmarks :
- index user_id, book_id
- index deleted_at
