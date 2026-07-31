# =============================================================================
# 이 파일의 책임: documents 테이블에 대한 CRUD와 목록 검색/페이징 쿼리를 담당한다.
#   Service 레이어는 DB 세션(Session)을 직접 다루지 않고 반드시 이 Repository를
#   거쳐서만 documents에 접근한다 (§2-1 Router -> Service -> Repository 원칙).
# 다른 파일과의 관계: dependencies.py의 get_document_repository()가 Depends(get_db)로
#   받은 Session을 주입해 이 클래스를 생성한다. document_service.py(담당자 C)가
#   이 클래스를 호출한다. models/document.py의 Document/ExtractedText/Analysis를 사용.
# Spring 비교: Spring Data JPA의 DocumentRepository(JpaRepository<Document, Long>)와
#   같은 위치. 다만 Spring Data처럼 메서드 이름만으로 쿼리를 자동 생성해주지
#   않으므로, 검색·페이징 쿼리를 SQLAlchemy Query API로 직접 작성한다.
# =============================================================================

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.document import Analysis, Document, ExtractedText


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, document: Document) -> Document:
        self._db.add(document)
        self._db.flush()
        return document

    def get_by_id(self, document_id: int) -> Document | None:
        return self._db.get(Document, document_id)

    def delete(self, document: Document) -> None:
        self._db.delete(document)

    def search(
        self,
        *,
        q: str | None,
        document_type: str | None,
        category: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Document], int]:
        query = self._db.query(Document)

        if q:
            # 파일명 또는 본문(extracted_texts.content) 부분검색.
            # outerjoin 대신 서브쿼리로 매칭 id를 걸러서 join으로 인한 행 중복을 피한다.
            matching_ids = self._db.query(ExtractedText.document_id).filter(
                ExtractedText.content.ilike(f"%{q}%")
            )
            query = query.filter(
                or_(Document.filename.ilike(f"%{q}%"), Document.id.in_(matching_ids))
            )

        if document_type:
            query = query.filter(Document.document_type == document_type)

        if category:
            # analyses.analyzer_type == "category"인 결과의 JSONB에서 category 값을 비교.
            matching_ids = self._db.query(Analysis.document_id).filter(
                Analysis.analyzer_type == "category",
                Analysis.result_json["category"].astext == category,
            )
            query = query.filter(Document.id.in_(matching_ids))

        total = query.count()
        items = (
            query.order_by(Document.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        return items, total
