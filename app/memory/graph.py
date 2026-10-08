class Neo4jGraph:
    def __init__(self,uri,user,password):
        from neo4j import AsyncGraphDatabase
        self.driver=AsyncGraphDatabase.driver(uri,auth=(user,password))
    async def close(self): await self.driver.close()
    async def upsert(self,evidence,entities,claims):
        async with self.driver.session() as s:
            await s.run("MERGE (d:Evidence {id:$id}) SET d.text=$text,d.observed_at=$observed",id=evidence.source_id,text=evidence.text,observed=evidence.observed_at.isoformat())
            for e in entities:
                await s.run("MERGE (n:Entity {id:$id}) SET n.name=$name,n.type=$type",id=e.entity_id,name=e.name,type=e.entity_type)
                await s.run("MATCH (n:Entity {id:$eid}),(d:Evidence {id:$did}) MERGE (n)-[:SUPPORTED_BY]->(d)",eid=e.entity_id,did=evidence.source_id)
            for c in claims:
                await s.run("MERGE (c:Claim {id:$id}) SET c.predicate=$p,c.object_value=$o,c.confidence=$conf,c.valid_from=$vf,c.valid_until=$vu,c.status=$status",id=c.claim_id,p=c.predicate,o=c.object_value,conf=c.confidence,vf=c.valid_from.isoformat(),vu=c.valid_until.isoformat() if c.valid_until else None,status=c.status)
