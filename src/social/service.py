import bleach
from sqlalchemy import Row

from src.constants import GarageItemRelations
from src.database import engine as db
from src.social.queries import (
    build_add_comment_query,
    build_delete_comment_query,
    build_get_comments_query,
    build_user_garage_race_relation_query,
)

GARAGE_RELATION_SENTENCE_MAP = {
    GarageItemRelations.HAS_OWNED: "used to own the",
    GarageItemRelations.OWNS: "currently owns the",
    GarageItemRelations.HAS_RIDDEN: "has ridden the",
    GarageItemRelations.SAT_ON: "has sat on the",
}


def add_comment(text: str, race_unique_id: str, user_id: int) -> bool:
    text = bleach.clean(text)
    with db.connect() as conn:
        conn.execute(build_add_comment_query(text, race_unique_id, user_id))
        conn.commit()
        return True


def _get_user_garage_race_relation(user_id: int, race_unique_id: str) -> str:
    with db.connect() as conn:
        results = conn.execute(
            build_user_garage_race_relation_query(user_id, race_unique_id)
        ).all()
        merged_by_relation: dict[GarageItemRelations, list[str]] = {}
        for result in results:
            if result.relation not in merged_by_relation:
                merged_by_relation[result.relation] = []
            merged_by_relation[result.relation].append(result.name)
        sentence_parts = [
            f"{GARAGE_RELATION_SENTENCE_MAP[relation]} {' and the '.join(names)}"
            for relation, names in merged_by_relation.items()
        ]
    return " and ".join(sentence_parts)


def get_comments(race_unique_id: str) -> list[tuple[Row, str]]:
    results = []
    with db.connect() as conn:
        garage_relation_sentences = {}
        comments = conn.execute(build_get_comments_query(race_unique_id)).all()
        for comment in comments:
            if comment.user_id not in garage_relation_sentences:
                garage_relation_sentences[
                    comment.user_id
                ] = _get_user_garage_race_relation(comment.user_id, race_unique_id)
            results.append((comment, garage_relation_sentences[comment.user_id]))
    return results


def delete_comment(comment_id: int, user_id: int) -> bool:
    with db.connect() as conn:
        conn.execute(build_delete_comment_query(comment_id, user_id))
        conn.commit()
        return True
