# Setup

### Format disk


```
sudo fdisk -l
sudo mkfs.ext4 /dev/xvdk -F
mkdir ~/data0
sudo mount -t ext4 /dev/xvdk /home/ubuntu/data0 -o defaults,nodelalloc,noatime
sudo chmod o+w /home/ubuntu/data0
sudo chown ubuntu /home/ubuntu/data0
cd /home/ubuntu/data0
```



### firewall (Optional)

```
echo y | sudo ufw enable
sudo systemctl start ufw
sudo systemctl enable ufw
sudo ufw allow from ****YOURIP****
sudo ufw status


sudo ufw allow 7770
sudo ufw allow 7780
sudo ufw allow 9999
sudo ufw allow 8023
sudo ufw allow 3000
sudo ufw allow 8888
sudo ufw allow 4399
sudo ufw allow 9980
sudo ufw allow 4040
sudo ufw status

```


### docker

```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo docker run hello-world


# docker without sudo
getent group docker    # Check if the docker group exists. If it doesn't exist, create it:  sudo groupadd docker
sudo usermod -aG docker pentium3
sudo systemctl restart docker
newgrp docker
docker run hello-world

sudo apt install htop iotop -y
```

### move Docker Data Directory

Move Docker Data Directory to another filesystem to save space on system disk

(eg, `/home/ubuntu/data0/docker`)


```
sudo systemctl stop docker
sudo systemctl status docker    # make sure docker service is stopped

mkdir /home/ubuntu/data0/docker

# Copy the Data to the New Location: Use rsync or cp to preserve file permissions and symbolic links
sudo rsync -aHAX /var/lib/docker/ /home/ubuntu/data0/docker/    
# Rename the Old Directory (as a backup)
sudo mv /var/lib/docker /var/lib/docker.bak

```

Then Edit the Docker configuration file (e.g., /etc/docker/daemon.json)
`sudo vi /etc/docker/daemon.json`

```
{
  "data-root": "/home/ubuntu/data0/docker/"
}
```

```
sudo systemctl restart docker

# Verify Docker is running:
sudo systemctl status docker

# Check if containers and images are accessible:
docker ps -a
docker images

# Start any necessary containers:
docker start <container_name>

# Once everything works as expected, you can delete the backup:
sudo rm -rf /var/lib/docker.bak
```

## Set up WebArena  website server

replace `****PUBLICIP****` with the public ip or URL of the server

```
wget http://metis.lti.cs.cmu.edu/webarena-images/shopping_final_0712.tar
```

### Shopping Website (OneStopShop)

```
docker load --input shopping_final_0712.tar
docker run --name shopping -p 7770:80 -d shopping_final_0712
# wait ~1 min to wait all services to start

docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://****PUBLICIP****:7770" # no trailing slash
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e  'UPDATE core_config_data SET value="http://****PUBLICIP****:7770/" WHERE path = "web/secure/base_url";'
docker exec shopping /var/www/magento2/bin/magento cache:flush
```

###  Allow remote connection to the DB inside docker container 


```
docker exec -it shopping mysql -u root -p
# Then enter the password (1234567890) when prompted

# Then run:
CREATE USER 'root'@'172.17.0.1' IDENTIFIED BY '1234567890';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'172.17.0.1' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```


### Default DB information

```
# Connection parameters
host = '127.0.0.1'
port = 33061
user = 'root'
password = '1234567890'
database = 'magentodb'
```


### Default user information


```
"username": "emma.lopez@gmail.com",
"password": "Password.123",
```
