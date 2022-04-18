import aiosqlite

from typing import Any, Dict

class Purchase():

    def __init__(self, purchase_id):
        self.purchase_id = purchase_id

    async def fetch_purchase_from_db(self, db: aiosqlite.Connection, purchase_id: int) -> Dict[str, Any]:
        async with db.execute(
                "SELECT id, purchase_name, quantity, date_created, last_updated FROM purchases WHERE id = ?",
                [purchase_id]) as cursor:
            row = await cursor.fetchone()
            if row is None:
                raise RuntimeError(f"Purchase {purchase_id} doesn't exist")
            return {
                "id": purchase_id,
                "name": row["purchase_name"],
                "quantity": row["quantity"],
                "date_created": row["date_created"],
                "last_updated": row["last_updated"]
            }