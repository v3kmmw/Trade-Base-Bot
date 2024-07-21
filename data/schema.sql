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

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, 
    balance INTEGER NOT NULL DEFAULT 500,
    reports TEXT DEFAULT '[]',
    invited_by INTEGER,
    invites INTEGER NOT NULL DEFAULT 0,
    fake_invites INTEGER NOT NULL DEFAULT 0,
    tickets TEXT DEFAULT '[]',
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

CREATE TABLE IF NOT EXISTS chat_drops (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    message_id INTEGER NOT NULL, 
    user_id INTEGER,
    amount INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
