import traceback
import logging
from typing import Dict, List, Any
import json
import docker,time,os,sys

from fastapi import APIRouter, HTTPException

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter()


def runsleep(dur, tik=5):
    cnt=int(dur)
    while(cnt>0):
        print('sleeping... ',cnt)
        time.sleep(int(tik))
        cnt-=int(tik)


# curl -N http://localhost:8000/api/container/reset/SERVERIP
@router.get("/reset/{myip}")
async def container_reset(myip: str):
    # Step 1: Connect to Docker
    client = docker.from_env()
    res=""

    # Step 2: Find the container ID using the image shopping_final_0712
    containers = client.containers.list(all=True)
    target_container_id = None
    for container in containers:
        if container.attrs['Config']['Image'] == 'shopping_final_0712':
            target_container_id = container.short_id
            break

    # Step 3: Stop and remove the container if found
    if target_container_id:
        container = client.containers.get(target_container_id)
        container.stop()
        container.remove()
        res=res+f"Container {target_container_id} stopped and removed."+"\n"
    else:
        return {
            "status": "No container found using the image shopping_final_0712."
        }

    # Step 4: Create a new container with specified parameters
    try:
        new_container = client.containers.run(
            'shopping_final_0712',
            detach=True,
            name='shopping',
            ports={'80/tcp': 7770, '3306/tcp': 33061}
        )
        res=res+f"New container created with ID: {new_container.short_id}"+"\n"
    
        runsleep(20)
        # Step 5: Execute commands inside the new container
        '''
        $ docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://SERVERIP:7770" # no trailing slash
        $ docker exec shopping mysql -u magentouser -pMyPassword magentodb -e 'UPDATE core_config_data SET value="http://SERVERIP:7770/" WHERE path = "web/secure/base_url";'
        $ docker exec shopping /var/www/magento2/bin/magento cache:flush
        '''
        new_container = client.containers.get('shopping')

        cmdlist=['/var/www/magento2/bin/magento setup:store-config:set --base-url="http://'+myip+':7770"' , 
                 f'mysql -u magentouser -pMyPassword magentodb -e \'UPDATE core_config_data SET value="http://'+myip+':7770/" WHERE path = "web/secure/base_url";\'' , 
                 '/var/www/magento2/bin/magento cache:flush']
        
        for cmd in cmdlist:
            res=res+"  cmd: "+cmd+"\n"
            exec_result = new_container.exec_run(cmd, stdout=True, stderr=True)
            res=res+"  result: "+exec_result.output.decode('utf-8')+"\n"
            res=res+"  --------------------- \n"

        return {
            "status": res
        }

    except docker.errors.APIError as e:
        return {
            "status": f"Failed to execute commands: {e}"
        }


