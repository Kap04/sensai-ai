import aiosqlite
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/all-results")
async def get_all_results():
    async with aiosqlite.connect("data.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM results") as cursor:
            rows = await cursor.fetchall()
            return JSONResponse(content=[dict(row) for row in rows])
