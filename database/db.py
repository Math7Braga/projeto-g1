"""Modelo relacional (SQLAlchemy + SQLite) da base de cobertura vacinal."""
from pathlib import Path

import pandas as pd
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

CAMINHO_DB = Path(__file__).parent / "vacinas.db"


class Base(DeclarativeBase):
    pass


class Regiao(Base):
    __tablename__ = "regioes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(20), unique=True)
    ufs: Mapped[list["UF"]] = relationship(back_populates="regiao")


class UF(Base):
    __tablename__ = "ufs"
    id: Mapped[int] = mapped_column(primary_key=True)
    sigla: Mapped[str] = mapped_column(String(2), unique=True)
    regiao_id: Mapped[int] = mapped_column(ForeignKey("regioes.id"))
    regiao: Mapped[Regiao] = relationship(back_populates="ufs")
    municipios: Mapped[list["Municipio"]] = relationship(back_populates="uf")


class Municipio(Base):
    __tablename__ = "municipios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    uf_id: Mapped[int] = mapped_column(ForeignKey("ufs.id"))
    uf: Mapped[UF] = relationship(back_populates="municipios")


class Vacina(Base):
    __tablename__ = "vacinas"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)


class Registro(Base):
    __tablename__ = "registros"
    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[object] = mapped_column(Date)
    ano: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    municipio_id: Mapped[int] = mapped_column(ForeignKey("municipios.id"))
    vacina_id: Mapped[int] = mapped_column(ForeignKey("vacinas.id"))
    publico_alvo: Mapped[str] = mapped_column(String(20))
    doses_aplicadas: Mapped[int] = mapped_column(Integer)
    populacao_alvo: Mapped[int] = mapped_column(Integer)
    cobertura_percentual: Mapped[float] = mapped_column(Float)
    meta_percentual: Mapped[int] = mapped_column(Integer)
    campanhas: Mapped[int] = mapped_column(Integer)
    nivel_alerta: Mapped[str] = mapped_column(String(10))
    atingiu_meta: Mapped[bool] = mapped_column(Boolean)


def obter_engine(caminho: Path = CAMINHO_DB):
    return create_engine(f"sqlite:///{caminho}")


def construir_banco(df: pd.DataFrame, caminho: Path = CAMINHO_DB):
    """Recria o banco a partir do DataFrame já tratado (utils.preparar)."""
    if caminho.exists():
        caminho.unlink()
    engine = obter_engine(caminho)
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        regioes = {n: Regiao(nome=n) for n in sorted(df["regiao"].unique())}
        s.add_all(regioes.values())
        ufs = {}
        for uf, reg in df[["uf", "regiao"]].drop_duplicates().itertuples(index=False):
            ufs[uf] = UF(sigla=uf, regiao=regioes[reg])
        s.add_all(ufs.values())
        muns = {}
        for mun, uf in df[["municipio", "uf"]].drop_duplicates().itertuples(index=False):
            muns[mun] = Municipio(nome=mun, uf=ufs[uf])
        s.add_all(muns.values())
        vacs = {n: Vacina(nome=n) for n in sorted(df["vacina"].unique())}
        s.add_all(vacs.values())
        s.flush()
        s.add_all(
            Registro(
                data=r.data.date(), ano=int(r.ano), mes=int(r.mes), municipio_id=muns[r.municipio].id,
                vacina_id=vacs[r.vacina].id, publico_alvo=r.publico_alvo, doses_aplicadas=int(r.doses_aplicadas),
                populacao_alvo=int(r.populacao_alvo), cobertura_percentual=float(r.cobertura_percentual),
                meta_percentual=int(r.meta_percentual), campanhas=int(r.campanhas),
                nivel_alerta=r.nivel_alerta, atingiu_meta=bool(r.atingiu_meta),
            )
            for r in df.itertuples(index=False)
        )
        s.commit()
    return engine


if __name__ == "__main__":
    # Uso: python -m database.db  (gera database/vacinas.db a partir do CSV)
    from pathlib import Path as _P
    csv = _P(__file__).parent.parent / "dados" / "simulacao_cobertura_vacinal_brasil.csv"
    bruto = pd.read_csv(csv, encoding="utf-8-sig")
    # preparar() depende do Streamlit apenas para cache; importamos aqui só a função pura
    from utils import preparar
    construir_banco(preparar(bruto))
    print("Banco criado em", CAMINHO_DB)
