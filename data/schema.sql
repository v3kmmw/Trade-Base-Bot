CREATE TABLE IF NOT EXISTS prefix (
    prefix TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS claimcodes (
    code TEXT PRIMARY KEY,
    amount INTEGER,
    owner TEXT
);

CREATE TABLE IF NOT EXISTS invitecodes (
    code TEXT PRIMARY KEY,
    creator TEXT,
    uses INTEGER
);

CREATE TABLE IF NOT EXISTS embeds (
    name TEXT PRIMARY KEY, 
    id INTEGER,
    embed TEXT DEFAULT NULL,
    buttons TEXT DEFAULT '[]',
    author INTEGER DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS reportverification (
    code TEXT PRIMARY KEY, 
    status TEXT DEFAULT NULL,
    reporter INTEGER, 
    scammer TEXT DEFAULT '[]',
    public BOOLEAN DEFAULT FALSE,
    message_link TEXT DEFAULT NULL,
    proof TEXT DEFAULT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    code TEXT PRIMARY KEY, 
    status TEXT DEFAULT NULL,
    reporter INTEGER,
    scammer TEXT DEFAULT NULL,
    public BOOLEAN DEFAULT FALSE,
    message_link TEXT DEFAULT NULL,
    proof TEXT DEFAULT NULL,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unlockable_roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    requirement TEXT NOT NULL,
    requirement_type TEXT NOT NULL
);

    

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 500,
    username TEXT UNIQUE,
    profile_color TEXT DEFAULT '#DEFAULT_COLOR',
    embed_image TEXT,
    premium BOOLEAN DEFAULT FALSE,
    message_streak INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    linked_roblox_account TEXT,
    crew_id INTEGER REFERENCES crews(id),
    vouches INTEGER DEFAULT 0,
    scammer_reports INTEGER DEFAULT 0,
    reports TEXT DEFAULT '[]',
    tickets TEXT DEFAULT '[]',
    invited_by INTEGER REFERENCES users(id),
    invites INTEGER NOT NULL DEFAULT 0,
    fake_invites INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (invited_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL, 
    description TEXT 
);

CREATE TABLE IF NOT EXISTS challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    challenger_id INTEGER,
    challengee_id INTEGER,
    game_id INTEGER,
    amount INTEGER NOT NULL, 
    status TEXT NOT NULL DEFAULT 'pending', 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (challenger_id) REFERENCES users(id),
    FOREIGN KEY (challengee_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER NOT NULL,
    type TEXT NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL, 
    price INTEGER NOT NULL, 
    perks TEXT
);

CREATE TABLE IF NOT EXISTS automod (
    type TEXT NOT NULL DEFAULT 'AI',
    minimum_sexual REAL NOT NULL,
    enable_sexual INTEGER NOT NULL DEFAULT 1,
    minimum_hate REAL NOT NULL,
    enable_hate INTEGER NOT NULL DEFAULT 1,
    minimum_harassment REAL NOT NULL,
    enable_harassment INTEGER NOT NULL DEFAULT 1,
    minimum_self_harm REAL NOT NULL,
    enable_self_harm INTEGER NOT NULL DEFAULT 1,
    minimum_sexual_minors REAL NOT NULL,
    enable_sexual_minors INTEGER NOT NULL DEFAULT 1,
    minimum_hate_threatening REAL NOT NULL,
    enable_hate_threatening INTEGER NOT NULL DEFAULT 1,
    minimum_violence_graphic REAL NOT NULL,
    enable_violence_graphic INTEGER NOT NULL DEFAULT 1,
    minimum_self_harm_intent REAL NOT NULL,
    enable_self_harm_intent INTEGER NOT NULL DEFAULT 1,
    minimum_self_harm_instructions REAL NOT NULL,
    enable_self_harm_instructions INTEGER NOT NULL DEFAULT 1,
    minimum_harassment_threatening REAL NOT NULL,
    enable_harassment_threatening INTEGER NOT NULL DEFAULT 1,
    minimum_violence REAL NOT NULL,
    enable_violence INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS automod_logs (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    model TEXT,
    type TEXT NOT NULL, 
    content TEXT NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_drops (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    message_id INTEGER NOT NULL, 
    user_id INTEGER,
    amount INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
