"""
SQLAlchemy model for summary statistics table.
Maps to summery_statistics_table created by the Master DB Creation Pipeline.
"""
from sqlalchemy import Column, String, Float
from app.database import Base


class SummaryStatistic(Base):
    """
    Model for pre-computed vehicle price summary statistics.
    Created by Airflow's Master_DB_Creation_Pipeline DAG.
    Groups by (make, model, yom, transmission, fuel_type) with average_price.
    """
    __tablename__ = "summery_statistics_table"

    make = Column(String(255), primary_key=True)
    model = Column(String(255), primary_key=True)
    yom = Column(String(255), primary_key=True)
    transmission = Column(String(255), primary_key=True)
    fuel_type = Column(String(255), primary_key=True)
    average_price = Column(Float)
    updated_date = Column(String(255))

    def __repr__(self):
        return f"<SummaryStatistic(make={self.make}, model={self.model}, yom={self.yom}, price={self.average_price})>"
