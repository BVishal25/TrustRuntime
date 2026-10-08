from pydantic import BaseModel, Field

class ReadTicketArgs(BaseModel): ticket_id: str = Field(min_length=1,max_length=128)
class SearchTicketsArgs(BaseModel): query: str = Field(min_length=1,max_length=500)
class QueryReadonlyArgs(BaseModel): sql: str = Field(min_length=1,max_length=5000)
class UpdateTicketArgs(BaseModel):
    ticket_id: str
    status: str
class DeleteCustomerArgs(BaseModel): customer_id: str
