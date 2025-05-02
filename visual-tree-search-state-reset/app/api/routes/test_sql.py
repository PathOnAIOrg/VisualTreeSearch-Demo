import sys
import os

a_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, a_dir)

from sql.python_scripts.ops import *


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
    res=runcmd("python sql/python_scripts/verify.py")
    return {
        "status":res
    }


