from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Subjects(Base):
    __tablename__ = "subjects"
    id: Mapped[str] = mapped_column(primary_key=True)
    condition: Mapped[str] = mapped_column(String(30), nullable=True)
    age: Mapped[int] = mapped_column(nullable=True)
    sex: Mapped[str] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"Subject(id={self.id}, condition={self.condition}, age={self.age}, sex={self.sex})"


class Projects(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f"Project(id={self.id})"


class Samples(Base):
    __tablename__ = "samples"
    id: Mapped[str] = mapped_column(primary_key=True)
    project: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    subject: Mapped[str] = mapped_column(ForeignKey("subjects.id"))
    treatment: Mapped[str] = mapped_column(String(30), nullable=True)
    response: Mapped[str] = mapped_column(String(30), nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        return f"Sample(id={self.id}, project={self.project}, subject={self.subject}, treatment={self.treatment}, response={self.response}, type={self.type})"


class CellCounts(Base):
    __tablename__ = "cell_counts"
    sample: Mapped[str] = mapped_column(ForeignKey("samples.id"), primary_key=True)
    b_cells: Mapped[int] = mapped_column(nullable=True)
    cd8_t_cells: Mapped[int] = mapped_column(nullable=True)
    cd4_t_cells: Mapped[int] = mapped_column(nullable=True)
    nk_cells: Mapped[int] = mapped_column(nullable=True)
    monocytes: Mapped[int] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"Counts(sample={self.sample}, b_cell={self.b_cell}, cd8_t_cells={self.cd8_t_cells}, cd4_t_cells={self.cd4_t_cells}, nk_cells={self.nk_cells}, monocytes={self.monocytes})"
