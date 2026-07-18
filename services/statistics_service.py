"""
services/statistics_service.py
---------------------------------
Admin panelida ko'rsatiladigan statistik ma'lumotlarni tayyorlaydi:
TOP faol/sust foydalanuvchilar, faolsizlik davrlari bo'yicha ro'yxatlar
va umumiy bot statistikasi.
"""

from __future__ import annotations

from database.queries import message_repo, statistics_repo, user_repo


class StatisticsService:
    async def top_active(self, limit: int = 10):
        return await statistics_repo.top_active(limit)

    async def top_inactive(self, limit: int = 10):
        return await statistics_repo.top_inactive(limit)

    async def inactive_for_days(self, days: int):
        return await user_repo.inactive_since(days)

    async def overview(self) -> dict:
        total_users = await user_repo.count()
        today_reports = len(await message_repo.get_today())
        weekly_reports = len(await message_repo.get_weekly())
        monthly_reports = len(await message_repo.get_monthly())
        unread = len(await message_repo.get_unread())
        return {
            "total_users": total_users,
            "today_reports": today_reports,
            "weekly_reports": weekly_reports,
            "monthly_reports": monthly_reports,
            "unread": unread,
        }


statistics_service = StatisticsService()
