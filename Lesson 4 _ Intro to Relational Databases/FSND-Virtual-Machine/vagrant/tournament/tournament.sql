-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


CREATE DATABASE tournament;
\c tournament;

DROP tournament IF EXISTS;

CREATE TABLE IF NOT EXISTS players(id SERIAL PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS matches (id SERIAL PRIMARY KEY,
    player1 SERIAL references players(id),
    player2 SERIAL references players(id)
);
