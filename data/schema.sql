CREATE TABLE IF NOT EXISTS prefix (
    prefix TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, 
    balance BIGINT NOT NULL DEFAULT 500, 
    tickets JSONB DEFAULT '[]' 
);

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY, 
    name VARCHAR(50) NOT NULL, 
    description TEXT 
);

CREATE TABLE IF NOT EXISTS challenges (
    id SERIAL PRIMARY KEY, 
    challenger_id BIGINT REFERENCES users(id), 
    challengee_id BIGINT REFERENCES users(id), 
    game_id INT REFERENCES games(id), 
    amount BIGINT NOT NULL, 
    status VARCHAR(20) NOT NULL DEFAULT 'pending', 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    amount BIGINT NOT NULL,
    type VARCHAR(20) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY, 
    name VARCHAR(50) NOT NULL, 
    price BIGINT NOT NULL, 
    perks JSONB 
);

CREATE TABLE IF NOT EXISTS chat_drops (
    id SERIAL PRIMARY KEY, 
    message_id BIGINT NOT NULL, 
    user_id BIGINT REFERENCES users(id), 
    amount BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
);
