#!/bin/bash
cd /home/sami/quran-verse-bot || exit
git reset --hard
git pull origin master
docker compose pull
docker compose up -d --build