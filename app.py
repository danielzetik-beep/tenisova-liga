import json
import math
import os
import random
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
        con.execute(
            "CREATE TABLE IF NOT EXISTS matches ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "round INTEGER NOT NULL, "
            "pos INTEGER NOT NULL, "
            "score1 INTEGER, "
            "score2 INTEGER, "
            "played TEXT, "
            "UNIQUE(round, pos))"
        )
        con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")


def next_pow2(n):
    p = 1
    while p < n:
        p *= 2
    return p


def team_dict(con, team_id):
    if team_id is None:
        return None
    row = con.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "father": row["father"], "son": row["son"]}


def compute_state(con):
    teams = [
        {"id": r["id"], "father": r["father"], "son": r["son"]}
        for r in con.execute("SELECT * FROM teams ORDER BY id")
    ]
    seed_row = con.execute("SELECT value FROM meta WHERE key = 'seeds'").fetchone()
    drawn = seed_row is not None
    matches = []
    champion = None
    if drawn:
        order = json.loads(seed_row["value"])
        n = next_pow2(max(len(order), 2))
        total_rounds = int(math.log2(n))
        slots = [None] * n
        for i, tid in enumerate(order):
            slots[i] = tid
        round_teams = {0: slots}
        result_rows = {
            (r["round"], r["pos"]): r
            for r in con.execute("SELECT * FROM matches")
        }
        for rnd in range(1, total_rounds + 1):
            prev = round_teams[rnd - 1]
            count = len(prev) // 2
            current = []
            for pos in range(count):
                t1 = prev[2 * pos]
                t2 = prev[2 * pos + 1]
                row = result_rows.get((rnd, pos))
                s1 = row["score1"] if row else None
                s2 = row["score2"] if row else None
                played = row["played"] if row else None
                mid = row["id"] if row else None
                winner = None
                if t1 is not None and t2 is not None:
                    if s1 is not None and s2 is not None and s1 != s2:
                        winner = t1 if s1 > s2 else t2
                elif t1 is not None:
                    winner = t1
                elif t2 is not None:
                    winner = t2
                current.append(winner)
                matches.append({
                    "id": mid,
                    "round": rnd,
                    "pos": pos,
                    "team1": team_dict(con, t1),
                    "team2": team_dict(con, t2),
                    "score1": s1,
                    "score2": s2,
                    "played": played,
                    "winner_id": winner,
                })
            round_teams[rnd] = current
        if total_rounds >= 1 and round_teams[total_rounds]:
            champion = team_dict(con, round_teams[total_rounds][0])
    return {
        "teams": teams,
        "drawn": drawn,
        "maxTeams": MAX_TEAMS,
        "matches": matches,
        "champion": champion,
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
        elif path == "/api/draw":
            self.draw()
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
                drawn = con.execute("SELECT value FROM meta WHERE key='seeds'").fetchone()
                if drawn:
                    self.send_json({"error": "Po rozlosování už nelze mazat týmy."}, 400)
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
            drawn = con.execute("SELECT value FROM meta WHERE key='seeds'").fetchone()
            if drawn:
                self.send_json({"error": "Turnaj už je rozlosovaný, registrace je uzavřená."}, 400)
                return
            count = con.execute("SELECT COUNT(*) AS c FROM teams").fetchone()["c"]
            if count >= MAX_TEAMS:
                self.send_json({"error": f"Turnaj je plný ({MAX_TEAMS} týmů)."}, 400)
                return
            con.execute("INSERT INTO teams (father, son) VALUES (?, ?)", (father, son))
            self.send_json(compute_state(con))

    def draw(self):
        with lock, get_db() as con:
            if con.execute("SELECT value FROM meta WHERE key='seeds'").fetchone():
                self.send_json({"error": "Turnaj už je rozlosovaný."}, 400)
                return
            ids = [r["id"] for r in con.execute("SELECT id FROM teams ORDER BY id")]
            if len(ids) < 2:
                self.send_json({"error": "Potřeba jsou alespoň 2 týmy."}, 400)
                return
            random.shuffle(ids)
            con.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('seeds', ?)",
                (json.dumps(ids),),
            )
            n = next_pow2(len(ids))
            total_rounds = int(math.log2(n))
            for rnd in range(1, total_rounds + 1):
                for pos in range(n >> rnd):
                    con.execute(
                        "INSERT OR IGNORE INTO matches (round, pos) VALUES (?, ?)",
                        (rnd, pos),
                    )
            self.send_json(compute_state(con))

    def set_result(self, match_id, data):
        try:
            s1 = int(data.get("score1"))
            s2 = int(data.get("score2"))
        except (TypeError, ValueError):
            self.send_json({"error": "Skóre musí být čísla."}, 400)
            return
        if s1 < 0 or s2 < 0:
            self.send_json({"error": "Skóre nesmí být záporné."}, 400)
            return
        if s1 == s2:
            self.send_json({"error": "Remíza není možná, jeden tým musí vyhrát."}, 400)
            return
        played = str(data.get("played", "")).strip() or None
        with lock, get_db() as con:
            row = con.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
            if not row:
                self.send_json({"error": "Zápas nenalezen."}, 404)
                return
            con.execute(
                "UPDATE matches SET score1 = ?, score2 = ?, played = ? WHERE id = ?",
                (s1, s2, played, match_id),
            )
            self.send_json(compute_state(con))

    def clear_result(self, match_id):
        with lock, get_db() as con:
            row = con.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
            if not row:
                self.send_json({"error": "Zápas nenalezen."}, 404)
                return
            con.execute(
                "UPDATE matches SET score1 = NULL, score2 = NULL, played = NULL WHERE id = ?",
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
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Běží na http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
