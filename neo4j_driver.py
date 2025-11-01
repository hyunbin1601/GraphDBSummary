from neo4j import GraphDatabase
import os

# Aura 접속 정보: 환경변수 우선, 미설정 시 제공된 기본값 사용
URI = os.getenv("NEO4J_URI", "neo4j+s://63dcd8cb.databases.neo4j.io")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "Nnmu9-N6GkJm7fWEXgv66lLRBuqNcfcHG3lDxarATPw")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
