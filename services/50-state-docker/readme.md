# scraper in docker
## setup env
* python3.13 -m venv .venv
* pip install -r requirements.txt

### build
docker build -t scraper-50-state .
### run locally
docker run -v ~/.aws:/root/.aws -p 80:80 scraper-50-state
* the -v option copies your aws credentials into the container.  in aws this is a role.

### aws stuff
* aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 471112980771.dkr.ecr.us-west-2.amazonaws.com
* docker tag scraper-50-state:latest 471112980771.dkr.ecr.us-west-2.amazonaws.com/scraper-50-state:latest
* create the ecr repo, if it hadn't already been created
* docker push 471112980771.dkr.ecr.us-west-2.amazonaws.com/scraper-50-state:latest
