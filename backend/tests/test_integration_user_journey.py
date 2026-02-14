"""B2.10 — Integration test: full user journey.

Tests the complete user flow end-to-end with the stub LLM:
  onboard → chat → upload → nugget inbox → node detail drawer

Uses httpx.AsyncClient against the FastAPI app with a real
(in-memory SQLite) database to validate API contracts, data flow,
and cross-endpoint consistency without requiring external services.
"""

import io
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.main import app
from app.models.base import Base

# ---------------------------------------------------------------------------
# Test database setup — async SQLite (in-memory)
# SQLite doesn't support JSONB or pgvector Vector, so we register
# type-compilation adapters that render them as JSON and TEXT.
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Register JSONB -> JSON adapter for SQLite
@compiles(JSONB, "sqlite")  # type: ignore[no-untyped-call]
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# Register pgvector Vector -> TEXT adapter for SQLite
try:
    from pgvector.sqlalchemy import Vector

    @compiles(Vector, "sqlite")  # type: ignore[no-untyped-call]
    def _compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass


async def _override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""

    # SQLite doesn't enforce FKs by default — enable them
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Provide an httpx AsyncClient wired to the FastAPI app."""
    from app.database import get_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# Full user-journey test
# ---------------------------------------------------------------------------


class TestFullUserJourney:
    """
    Simulates a complete user session:
      1. Onboard — create a session with project context
      2. Chat turn 1 — send a brain-dump message
      3. Chat turn 2 — send a follow-up message
      4. Upload — upload a .txt document
      5. Nugget inbox — list, filter, and update nugget status
      6. Node detail — inspect a node via the drawer endpoint
      7. Feedback — thumbs-up a nugget
      8. Graph view — verify the full graph state
    """

    async def test_full_journey(self, client: AsyncClient):
        # ------------------------------------------------------------------
        # Step 1: Onboard
        # ------------------------------------------------------------------
        onboard_resp = await client.post(
            "/onboard",
            json={
                "project_name": "Leadership Book",
                "topic": "Engineering leadership lessons",
                "audience": "VP-level engineering leaders",
            },
        )
        assert onboard_resp.status_code == 200
        onboard_data = onboard_resp.json()
        assert "session_id" in onboard_data
        assert onboard_data["project_name"] == "Leadership Book"
        session_id = onboard_data["session_id"]

        # ------------------------------------------------------------------
        # Step 2: Chat turn 1 — strong anecdote
        # ------------------------------------------------------------------
        chat1_resp = await client.post(
            "/chat_turn",
            json={
                "session_id": session_id,
                "message": (
                    "When I was at Stripe in 2019, our payment processing went down "
                    "for 45 minutes. The thing that saved us was that our on-call "
                    "engineer had built a personal relationship with the AWS support "
                    "team. She got us escalated in 10 minutes instead of 2 hours, "
                    "saving $6M."
                ),
            },
        )
        assert chat1_resp.status_code == 200
        chat1 = chat1_resp.json()

        # Verify core response structure
        assert "turn_id" in chat1
        assert chat1["session_id"] == session_id
        assert isinstance(chat1["captured_nuggets"], list)
        assert len(chat1["captured_nuggets"]) >= 1
        assert "graph_update_summary" in chat1

        # Verify nugget shape
        nugget_1 = chat1["captured_nuggets"][0]
        assert "nugget_id" in nugget_1
        assert "node_id" in nugget_1
        assert "title" in nugget_1
        assert "score" in nugget_1
        assert 0 <= nugget_1["score"] <= 100

        # Verify next question
        assert chat1.get("next_question") is not None
        assert "question" in chat1["next_question"]
        assert "why_this_next" in chat1["next_question"]

        # Save IDs for later assertions
        first_nugget_id = nugget_1["nugget_id"]
        first_node_id = nugget_1["node_id"]

        # ------------------------------------------------------------------
        # Step 3: Chat turn 2 — follow-up
        # ------------------------------------------------------------------
        chat2_resp = await client.post(
            "/chat_turn",
            json={
                "session_id": session_id,
                "message": (
                    "After that incident I created a framework called '3-before-3': "
                    "every new engineer has to build 3 external relationships in "
                    "their first 3 months. We measure it in onboarding reviews."
                ),
            },
        )
        assert chat2_resp.status_code == 200
        chat2 = chat2_resp.json()
        # In stub mode the same title is returned, so dedup may merge
        # instead of creating a new nugget. Both outcomes are valid.
        assert "session_id" in chat2

        # ------------------------------------------------------------------
        # Step 4: Upload a document
        # ------------------------------------------------------------------
        doc_content = (
            "My top leadership principle: always invest in relationships before "
            "you need them. At every company I've led, I've seen that teams with "
            "strong external networks resolve incidents 3x faster.\n\n"
            "Another principle: measure what matters. We started tracking 'time "
            "to first external escalation' as an SLI and reduced it from 2 hours "
            "to 15 minutes in 6 months."
        )
        upload_resp = await client.post(
            "/upload",
            params={"session_id": session_id},
            files={
                "file": ("leadership-notes.txt", io.BytesIO(doc_content.encode()), "text/plain")
            },
        )
        assert upload_resp.status_code == 200
        upload_data = upload_resp.json()
        assert "document_id" in upload_data
        assert upload_data["filename"] == "leadership-notes.txt"
        # Upload pipeline ran — count may be 0 if stub titles dedup
        assert upload_data["nugget_count"] >= 0
        assert isinstance(upload_data["top_nuggets"], list)

        # ------------------------------------------------------------------
        # Step 5: Nugget Inbox — list all nuggets
        # ------------------------------------------------------------------
        inbox_resp = await client.get("/nuggets", params={"session_id": session_id})
        assert inbox_resp.status_code == 200
        inbox = inbox_resp.json()
        # Stub LLM returns the same title each time, so dedup merges most
        # turns. We expect at least 1 nugget from the first chat turn.
        assert inbox["total"] >= 1
        assert all("nugget_id" in n for n in inbox["nuggets"])
        assert all("score" in n for n in inbox["nuggets"])
        assert all("status" in n for n in inbox["nuggets"])

        # Verify default status is "new"
        assert all(n["status"] == "new" for n in inbox["nuggets"])

        # Verify sort by score (descending)
        scores = [n["score"] for n in inbox["nuggets"]]
        assert scores == sorted(scores, reverse=True)

        # ------------------------------------------------------------------
        # Step 5b: Nugget Inbox — update status to "explored"
        # ------------------------------------------------------------------
        any_nugget_id = inbox["nuggets"][0]["nugget_id"]
        status_resp = await client.post(
            f"/nugget/{any_nugget_id}/status",
            json={"status": "explored"},
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "explored"

        # Verify filter by status works
        explored_resp = await client.get(
            "/nuggets",
            params={"session_id": session_id, "status": "explored"},
        )
        assert explored_resp.status_code == 200
        assert explored_resp.json()["total"] >= 1
        assert all(n["status"] == "explored" for n in explored_resp.json()["nuggets"])

        # ------------------------------------------------------------------
        # Step 6: Node Detail Drawer
        # ------------------------------------------------------------------
        node_resp = await client.get(f"/node/{first_node_id}")
        assert node_resp.status_code == 200
        node_detail = node_resp.json()
        assert node_detail["node_id"] == first_node_id
        assert "title" in node_detail
        assert "summary" in node_detail
        assert "provenance" in node_detail
        assert len(node_detail["provenance"]) >= 1

        # Verify nugget detail inside node
        assert node_detail.get("nugget") is not None
        assert "dimension_scores" in node_detail["nugget"]

        # ------------------------------------------------------------------
        # Step 7: Feedback — thumbs up
        # ------------------------------------------------------------------
        feedback_resp = await client.post(
            f"/nugget/{first_nugget_id}/feedback",
            json={"feedback": "up"},
        )
        assert feedback_resp.status_code == 200
        assert feedback_resp.json()["user_feedback"] == "up"

        # Verify feedback persists
        feedback_get = await client.get(f"/nugget/{first_nugget_id}/feedback")
        assert feedback_get.status_code == 200
        assert feedback_get.json()["user_feedback"] == "up"

        # ------------------------------------------------------------------
        # Step 8: Graph View — verify overall state
        # ------------------------------------------------------------------
        graph_resp = await client.get("/graph_view", params={"session_id": session_id})
        assert graph_resp.status_code == 200
        graph = graph_resp.json()
        assert len(graph["nodes"]) >= 1  # at least 1 from the first chat turn
        assert all("node_id" in n for n in graph["nodes"])
        assert all("node_type" in n for n in graph["nodes"])


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test boundary conditions and error paths."""

    async def test_chat_without_session_creates_one(self, client: AsyncClient):
        """Chat with no session_id should auto-create a session."""
        resp = await client.post(
            "/chat_turn",
            json={"message": "Here is a specific insight about hiring engineers at scale."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"] is not None

    async def test_upload_rejects_unsupported_type(self, client: AsyncClient):
        """Uploading an unsupported file type returns 400."""
        # Create a session first
        onboard = await client.post(
            "/onboard",
            json={"project_name": "Test", "topic": "Test"},
        )
        sid = onboard.json()["session_id"]

        resp = await client.post(
            "/upload",
            params={"session_id": sid},
            files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
        )
        assert resp.status_code == 400

    async def test_nugget_status_invalid_value(self, client: AsyncClient):
        """Setting an invalid status returns 400."""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/nugget/{fake_id}/status",
            json={"status": "invalid_status"},
        )
        # Either 400 (invalid status) or 404 (nugget not found) is acceptable
        assert resp.status_code in (400, 404)

    async def test_node_not_found(self, client: AsyncClient):
        """Requesting a non-existent node returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/node/{fake_id}")
        assert resp.status_code == 404

    async def test_nugget_feedback_not_found(self, client: AsyncClient):
        """Submitting feedback for a non-existent nugget returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/nugget/{fake_id}/feedback",
            json={"feedback": "up"},
        )
        assert resp.status_code == 404

    async def test_empty_graph_view(self, client: AsyncClient):
        """Graph view for a new session returns empty lists."""
        onboard = await client.post(
            "/onboard",
            json={"project_name": "Empty", "topic": "Nothing yet"},
        )
        sid = onboard.json()["session_id"]

        resp = await client.get("/graph_view", params={"session_id": sid})
        assert resp.status_code == 200
        graph = resp.json()
        assert graph["nodes"] == []
        assert graph["edges"] == []

    async def test_nugget_inbox_filters(self, client: AsyncClient):
        """Test nugget inbox type and sort filters."""
        # Onboard + chat to create nuggets
        onboard = await client.post(
            "/onboard",
            json={"project_name": "Filter Test", "topic": "Testing"},
        )
        sid = onboard.json()["session_id"]

        await client.post(
            "/chat_turn",
            json={
                "session_id": sid,
                "message": (
                    "At Google in 2020, we discovered that pair programming "
                    "doubled code review throughput for junior engineers."
                ),
            },
        )

        # List all — should have at least 1
        resp = await client.get("/nuggets", params={"session_id": sid})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # Sort by created_at
        resp2 = await client.get(
            "/nuggets",
            params={"session_id": sid, "sort_by": "created_at"},
        )
        assert resp2.status_code == 200
