from schemas.imports import *
from pydantic import Field
import time
from security.hash import hash_password
from typing import List, Optional
from pydantic import BaseModel, EmailStr, model_validator

class AdminBase(BaseModel):

    full_name: str
    email: EmailStr
    password: str | bytes


class AdminLogin(BaseModel):
    # Add other fields here 
    email:EmailStr
    password:str | bytes
    pass
class AdminRefresh(BaseModel):
    # Add other fields here 
    refresh_token:str
    pass


class AdminCreate(AdminBase):
    # Add other fields here
    invited_by:str 
    date_created: int = Field(default_factory=lambda: int(time.time()))
    last_updated: int = Field(default_factory=lambda: int(time.time()))
    @model_validator(mode='after')
    def obscure_password(self):
        self.password=hash_password(self.password)
        return self
class AdminUpdate(BaseModel):
    # Add other fields here 
    password:Optional[str | bytes]=None
    last_updated: int = Field(default_factory=lambda: int(time.time()))
    @model_validator(mode='after')
    def obscure_password(self):
        if self.password:
            self.password=hash_password(self.password)
            return self
class AdminOut(AdminBase):
    # Add other fields here 
    id: Optional[str] =None

    date_created: Optional[int] = None
    last_updated: Optional[int] = None
    refresh_token: Optional[str] =None
    access_token:Optional[str]=None
    @model_validator(mode='before')
    def set_dynamic_values(cls,values):
        if isinstance(values,dict):
            values['id']= str(values.get('_id'))
            return values
      
            
    model_config = {
        "from_attributes": True,        # allows creating model from objects (like ORM)
        "populate_by_name": True,       # allow snake_case input
        "arbitrary_types_allowed": True,# allow non-pydantic types like ObjectId
        "json_encoders": {ObjectId: str} # encode ObjectId as string
    }