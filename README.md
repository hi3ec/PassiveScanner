# Passive Scanner
passive scanner and save to database




### Run mongodb with docker
```
docker run --rm -it --name mongodb -v ~/w/docker-db/datadir:/data/db -p 27017:27017 mongo
```




### Run postgresql with docker
```
docker run --rm -it --name postgres -p 5432:5432 -v ~/w/docker-db/datadir:/var/lib/postgresql/data -e POSTGRES_PASSWORD=postgres -d postgres
```

```
user:postgres
pass:postgres
```
