#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##  Requiriments
# certifi==2021.10.8
# charset-normalizer==2.0.12
# idna==3.3
# podman==4.0.0
# pyxdg==0.27
# requests==2.27.1
# toml==0.10.2
# typing-extensions==4.1.1
# urllib3==1.24.3

import logging
import os
from datetime import date
from podman import PodmanClient

# Nivel de log
log_level = logging.INFO

logging.basicConfig(
    level=log_level,
    datefmt='%d/%m/%Y %H:%M:%S',
    format='[%(asctime)s] <%(levelname)s> %(message)s'
)

# Socket de podman
# https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9-beta/html/building_running_and_managing_containers/assembly_using-the-container-tools-api_building-running-and-managing-containers
uri = "unix:///run/user/0/podman/podman.sock"

# Eliminar imaxes antiguas
delete_old = True

# Rutas
use_nfs = True
nfs_server = "192.168.0.101"
nfs_share = "/volume1/backup1/docker"
nfs_point_mount = "/mnt"
backup_path = "/mnt/backup"

def nfs(function):
    if function == "mount":
        try:
            os.system(f"mount -t nfs {nfs_server}:{nfs_share} {nfs_point_mount}")
            logging.info(f"Montouse o nfs")
        except Exception as e:
            logging.error(f"Produciuse un erro ao montar o nfs: {e}")
            return
    elif function == "umount":
        try:
            os.system(f"umount {nfs_point_mount}")
            logging.info(f"Desmontouse o nfs")
        except Exception as e:
            logging.error(f"Non se puido desmontar o nfs {e}")
            return

def  backup():
    imaxes_a_backup = []
    hoxe = date.today()

    with PodmanClient(base_url=uri) as client:
        for container in client.containers.list():
            imaxes_a_backup.append(f"localhost/{container.name}:latest")
            container.commit(repository=f"localhost/{container.name}", tag="latest")

        for image in client.images.list():
            image_repository = image.__dict__['attrs']['RepoTags']
            if image_repository is not None:
                image_repository_str = str(image_repository[0])
                image_name = image_repository_str.split('/')[1].split(':')[0]
                if image_repository[0] in imaxes_a_backup:
                    logging.info(f"Procedemos a crear o tarball da imaxe {image_repository[0]}")
                    try:
                        with open(f"{backup_path}{hoxe}_{image_name}.tar", 'wb') as ficheiro:
                            for bloque in image.save():
                                ficheiro.write(bloque)
                    except Exception as e:
                        logging.error(f"Erro ao crear o tar da imaxe {image_repository[0]}: {e}")
            else:
                if delete_old:
                    logging.info(f"eliminamos a imaxe con ID: {image.id} por ser antigua")
                    try:
                        image.remove()
                    except Exception as e:
                        logging.error(f"Erro ao elminar a imaxe {image.id}: {e}")
                else:
                    pass

if __name__ == '__main__':
    if use_nfs:
        nfs("mount")
        backup()
        nfs("umount")
    else:
        backup()