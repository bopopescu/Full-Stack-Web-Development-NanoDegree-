-- Table definitions for the tournament project.

-- Drop tournament database if exists
DROP tournament IF EXISTS;

-- Create Database 'Tournament'
CREATE DATABASE tournament;

-- Connect to the tournament database
\c tournament;

-- Create Players Database
CREATE TABLE IF NOT EXISTS players(player_id SERIAL PRIMARY KEY, name TEXT);

-- Create Matches Database
CREATE TABLE IF NOT EXISTS matches (
  match_id serial PRIMARY KEY,
  winner INTEGER,
  loser INTEGER,
  FOREIGN KEY(winner) REFERENCES players(player_id),
  FOREIGN KEY(loser) REFERENCES players(player_id)
);

-- Create Standings View
CREATE VIEW standings AS
SELECT p.player_id as player_id, p.name,
(SELECT count(*) FROM matches WHERE matches.winner = p.player_id) as matches_won,
(SELECT count(*) FROM matches WHERE p.player_id in (winner, loser)) as matches_played
FROM players p
GROUP BY p.player_id
ORDER BY matches_won DESC;
