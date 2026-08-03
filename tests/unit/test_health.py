"""Unit tests for the health check endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.sql.expression import TextClause


@pytest.mark.unit
class TestHealthCheck:
    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)
        return db

    async def test_postgres_probe_uses_text_object(self, mock_db):
        """Verify db.execute is called with text() for SQLAlchemy 2.x."""
        from api.routes.health import health_check

        with patch("redis.Redis") as mock_redis_class:
            mock_redis_class.return_value.ping = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db)

            assert exc_info.value.detail["dependencies"]["postgres"] == "healthy"

        mock_db.execute.assert_called_once()
        call_arg = mock_db.execute.call_args[0][0]
        assert isinstance(call_arg, TextClause)

    async def test_postgres_probe_catches_db_exception(self, mock_db):
        """Verify postgres marked unhealthy when db.execute fails."""
        from api.routes.health import health_check

        mock_db.execute = AsyncMock(side_effect=Exception("DB connection failed"))

        with patch("redis.Redis") as mock_redis_class:
            mock_redis_class.return_value.ping = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await health_check(db=mock_db)

            assert exc_info.value.detail["dependencies"]["postgres"] == "unhealthy"
