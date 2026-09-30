"""Strategy Memory: workload -> best known strategy (SQLite)."""
import json
import sqlite3


class StrategyMemory:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS runs (workload TEXT, strategy TEXT, "
            "predicted REAL, measured REAL)")

    def record(self, workload, strategy, predicted, measured):
        self.db.execute("INSERT INTO runs VALUES (?,?,?,?)",
                        (json.dumps(workload, sort_keys=True), strategy, predicted, measured))
        self.db.commit()

    def best(self, workload):
        return self.db.execute(
            "SELECT strategy, measured FROM runs WHERE workload=? "
            "ORDER BY measured ASC LIMIT 1",
            (json.dumps(workload, sort_keys=True),)).fetchone()

    def twin_error(self):
        """Mean relative error of twin predictions vs measurements."""
        rows = self.db.execute(
            "SELECT predicted, measured FROM runs WHERE measured > 0").fetchall()
        if not rows:
            return None
        return sum(abs(p - m) / m for p, m in rows) / len(rows)
