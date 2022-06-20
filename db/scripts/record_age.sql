-- SQLite

-- I don't know why sql has a time difference from 1.5h to python datetime, maybe summer time diffs (?) -> hence the 0.0625 (1.5/24) offset
SELECT name, location, 0.0625 + julianday('now') - julianday(timestamp) AS AddedDaysAgo FROM RESTAURANT;
