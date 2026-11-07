import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "liga.db")
MAX_TEAMS = 8

lock = threading.Lock()


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with get_db() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS teams ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "father TEXT NOT NULL, "
            "son TEXT NOT NULL, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        cols = [r["name"] for r in con.execute("PRAGMA table_info(matches)")]
        if cols and "round" in cols:
            con.execute("DROP TABLE matches")
        con.execute(
            "CREATE TABLE IF NOT EXISTS matches ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "team1_id INTEGER NOT NULL, "
            "team2_id INTEGER NOT NULL, "
            "s1a INTEGER, s1b INTEGER, "
            "s2a INTEGER, s2b INTEGER, "
            "tb1 INTEGER, tb2 INTEGER, "
            "played TEXT, "
            "UNIQUE(team1_id, team2_id))"
        )
        con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")


def team_dict(con, team_id):
    row = con.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "father": row["father"], "son": row["son"]}


def match_winner(m):
    if m["s1a"] is None or m["s1b"] is None or m["s2a"] is None or m["s2b"] is None:
        return None
    t1_sets = (m["s1a"] > m["s1b"]) + (m["s2a"] > m["s2b"])
    t2_sets = (m["s1b"] > m["s1a"]) + (m["s2b"] > m["s2a"])
    if t1_sets != t2_sets:
        return m["team1_id"] if t1_sets > t2_sets else m["team2_id"]
    if m["tb1"] is None or m["tb2"] is None:
        return None
    return m["team1_id"] if m["tb1"] > m["tb2"] else m["team2_id"]


def compute_standings(con, teams, matches):
    stats = {
        t["id"]: {
            "team": t, "played": 0, "wins": 0, "losses": 0,
            "sets_won": 0, "sets_lost": 0, "games_won": 0, "games_lost": 0,
        }
        for t in teams
    }
    for m in matches:
        w = match_winner(m)
        if w is None:
            continue
        loser = m["team2_id"] if w == m["team1_id"] else m["team1_id"]
        a = stats[w]
        b = stats[loser]
        a["played"] += 1
        b["played"] += 1
        a["wins"] += 1
        b["losses"] += 1
        t1_sets = (m["s1a"] > m["s1b"]) + (m["s2a"] > m["s2b"])
        t2_sets = (m["s1b"] > m["s1a"]) + (m["s2b"] > m["s2a"])
        if w == m["team1_id"]:
            a["sets_won"] += t1_sets
            a["sets_lost"] += t2_sets
            b["sets_won"] += t2_sets
            b["sets_lost"] += t1_sets
        else:
            a["sets_won"] += t2_sets
            a["sets_lost"] += t1_sets
            b["sets_won"] += t1_sets
            b["sets_lost"] += t2_sets
        a["games_won"] += m["s1a"] + m["s2a"]
        a["games_lost"] += m["s1b"] + m["s2b"]
        b["games_won"] += m["s1b"] + m["s2b"]
        b["games_lost"] += m["s1a"] + m["s2a"]
    rows = []
    for s in stats.values():
        rows.append({
            "team": s["team"],
            "played": s["played"],
            "wins": s["wins"],
            "losses": s["losses"],
            "sets": f"{s['sets_won']}:{s['sets_lost']}",
            "sets_diff": s["sets_won"] - s["sets_lost"],
            "games": f"{s['games_won']}:{s['games_lost']}",
            "games_diff": s["games_won"] - s["games_lost"],
            "points": s["wins"] * 2,
        })
    rows.sort(key=lambda r: (-r["points"], -r["sets_diff"], -r["games_diff"], r["team"]["father"]))
    return rows


def compute_state(con):
    teams = [
        {"id": r["id"], "father": r["father"], "son": r["son"]}
        for r in con.execute("SELECT * FROM teams ORDER BY id")
    ]
    sched = con.execute("SELECT value FROM meta WHERE key = 'schedule'").fetchone()
    scheduled = sched is not None
    matches = []
    for r in con.execute("SELECT * FROM matches ORDER BY id"):
        m = dict(r)
        m["team1"] = team_dict(con, m["team1_id"])
        m["team2"] = team_dict(con, m["team2_id"])
        m["winner_id"] = match_winner(m)
        matches.append(m)
    standings = compute_standings(con, teams, matches) if scheduled else []
    return {
        "teams": teams,
        "scheduled": scheduled,
        "maxTeams": MAX_TEAMS,
        "matches": matches,
        "standings": standings,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            with open(os.path.join(BASE, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/state":
            with lock, get_db() as con:
                self.send_json(compute_state(con))
        else:
            self.send_json({"error": "Nenalezeno"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            data = self.read_json()
        except Exception:
            self.send_json({"error": "Špatný požadavek"}, 400)
            return
        if path == "/api/teams":
            self.add_team(data)
        elif path == "/api/schedule":
            self.create_schedule()
        elif path.startswith("/api/match/") and path.endswith("/result"):
            try:
                match_id = int(path.split("/")[3])
            except ValueError:
                self.send_json({"error": "Špatné ID zápasu"}, 400)
                return
            self.set_result(match_id, data)
        elif path.startswith("/api/match/") and path.endswith("/clear"):
            try:
                match_id = int(path.split("/")[3])
            except ValueError:
                self.send_json({"error": "Špatné ID zápasu"}, 400)
                return
            self.clear_result(match_id)
        elif path == "/api/reset":
            self.reset()
        else:
            self.send_json({"error": "Nenalezeno"}, 404)

    def do_DELETE(self):
        path = self.path.split("?")[0]
        if path.startswith("/api/teams/"):
            try:
                team_id = int(path.split("/")[3])
            except ValueError:
                self.send_json({"error": "Špatné ID týmu"}, 400)
                return
            with lock, get_db() as con:
                if con.execute("SELECT value FROM meta WHERE key='schedule'").fetchone():
                    self.send_json({"error": "Zápasy už jsou vytvořené, registrace je uzavřená."}, 400)
                    return
                con.execute("DELETE FROM teams WHERE id = ?", (team_id,))
                self.send_json(compute_state(con))
        else:
            self.send_json({"error": "Nenalezeno"}, 404)

    def add_team(self, data):
        father = str(data.get("father", "")).strip()
        son = str(data.get("son", "")).strip()
        if not father or not son:
            self.send_json({"error": "Vyplňte jméno táty i syna."}, 400)
            return
        with lock, get_db() as con:
            if con.execute("SELECT value FROM meta WHERE key='schedule'").fetchone():
                self.send_json({"error": "Zápasy už jsou vytvořené, registrace je uzavřená."}, 400)
                return
            count = con.execute("SELECT COUNT(*) AS c FROM teams").fetchone()["c"]
            if count >= MAX_TEAMS:
                self.send_json({"error": f"Turnaj je plný ({MAX_TEAMS} týmů)."}, 400)
                return
            con.execute("INSERT INTO teams (father, son) VALUES (?, ?)", (father, son))
            self.send_json(compute_state(con))

    def create_schedule(self):
        with lock, get_db() as con:
            if con.execute("SELECT value FROM meta WHERE key='schedule'").fetchone():
                self.send_json({"error": "Zápasy už jsou vytvořené."}, 400)
                return
            ids = [r["id"] for r in con.execute("SELECT id FROM teams ORDER BY id")]
            if len(ids) < 2:
                self.send_json({"error": "Potřeba jsou alespoň 2 týmy."}, 400)
                return
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    con.execute(
                        "INSERT OR IGNORE INTO matches (team1_id, team2_id) VALUES (?, ?)",
                        (ids[i], ids[j]),
                    )
            con.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('schedule', '1')")
            self.send_json(compute_state(con))

    def set_result(self, match_id, data):
        def num(key):
            v = data.get(key)
            if v is None or v == "":
                return None
            return int(v)

        try:
            s1a, s1b, s2a, s2b = num("s1a"), num("s1b"), num("s2a"), num("s2b")
            tb1, tb2 = num("tb1"), num("tb2")
        except (TypeError, ValueError):
            self.send_json({"error": "Skóre musí být čísla."}, 400)
            return
        vals = [v for v in (s1a, s1b, s2a, s2b) if v is not None]
        if len(vals) != 4 or any(v < 0 for v in vals):
            self.send_json({"error": "Vyplňte oba sety (nezáporná čísla)."}, 400)
            return
        if s1a == s1b or s2a == s2b:
            self.send_json({"error": "V každém setu musí někdo vyhrát (bez remízy)."}, 400)
            return
        t1_sets = (s1a > s1b) + (s2a > s2b)
        t2_sets = (s1b > s1a) + (s2b > s2a)
        if t1_sets == t2_sets:
            if tb1 is None or tb2 is None or tb1 < 0 or tb2 < 0:
                self.send_json({"error": "Při 1:1 na sety je potřeba výsledek tie-breaku."}, 400)
                return
            if tb1 == tb2:
                self.send_json({"error": "V tie-breaku musí někdo vyhrát."}, 400)
                return
        else:
            tb1 = tb2 = None
        played = str(data.get("played", "")).strip() or None
        with lock, get_db() as con:
            row = con.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
            if not row:
                self.send_json({"error": "Zápas nenalezen."}, 404)
                return
            con.execute(
                "UPDATE matches SET s1a=?, s1b=?, s2a=?, s2b=?, tb1=?, tb2=?, played=? WHERE id = ?",
                (s1a, s1b, s2a, s2b, tb1, tb2, played, match_id),
            )
            self.send_json(compute_state(con))

    def clear_result(self, match_id):
        with lock, get_db() as con:
            row = con.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
            if not row:
                self.send_json({"error": "Zápas nenalezen."}, 404)
                return
            con.execute(
                "UPDATE matches SET s1a=NULL, s1b=NULL, s2a=NULL, s2b=NULL, tb1=NULL, tb2=NULL, played=NULL WHERE id = ?",
                (match_id,),
            )
            self.send_json(compute_state(con))

    def reset(self):
        with lock, get_db() as con:
            con.execute("DELETE FROM teams")
            con.execute("DELETE FROM matches")
            con.execute("DELETE FROM meta")
            self.send_json(compute_state(con))


def main():
    init_db()
    port = int(os.environ.get("PORT", "8899"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Běží na http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
