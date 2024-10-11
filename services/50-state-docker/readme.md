# scraper in docker
### build
docker build -t scraper-50-state .
### run locally
docker run -v ~/.aws:/root/.aws -p 80:80 scraper-50-state
* the -v option copies your aws credentials into the container.  in aws this is a role.