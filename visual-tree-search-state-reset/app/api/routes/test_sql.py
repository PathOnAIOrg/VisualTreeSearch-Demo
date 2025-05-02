import sys
import os

from ...sql.ops import delete_data, restore_data, fetch_data


import logging
from fastapi import APIRouter, HTTPException

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter()


def runcmd(cmd):
    print('------------------------------------------------------------')
    print(cmd)
    res=os.popen(cmd).read()
    print(res)
    print('------------------------------------------------------------')
    return(res)



# curl -N http://localhost:8000/api/sql/restore
@router.get("/restore")
async def sql_restore():
    delres=delete_data()
    resres=restore_data()
    return {
        "delres":delres,
        "resres":resres
    }


# curl -N http://localhost:8000/api/sql/extract
@router.get("/extract")
async def sql_extract():
    res=fetch_data()
    return {
        "status":res
    }




# curl -N http://localhost:8000/api/sql/verify
@router.get("/verify")
async def sql_verify():
    res=runcmd("python sql/verify.py")
    return {
        "status":res
    }


