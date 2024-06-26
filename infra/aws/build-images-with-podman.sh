FUSEKI_IMAGE=docker.io/secoresearch/fuseki:4.5.0
METABASE_IMAGE=docker.io/metabase/metabase:v0.43.4
MONGO_EXPRESS_IMAGE=docker.io/mongo-express:0.54.0
SFTP_IMAGE=docker.io/atmoz/sftp:debian



IMAGES_TO_BE_BUILD=(airflow digest_api)
IMAGES_FROM_DOCKER_HUB=(fuseki metabase mongo-express sftp)
source .env
export $(cat .env | xargs)
cd ../../
cp requirements.txt ./infra/airflow/
cp requirements.txt ./infra/digest_api/digest_service/project_requirements.txt
cp -r ted_sws ./infra/digest_api/
make create-env-digest-api
cd infra/aws



build_image_from_source_code(){
  echo "Building image for $1"
  IMAGE_NAME=$1
  if [ "$IMAGE_NAME" = "metabase_postgres" ]; then
  IMAGE_NAME=metabase
  podman build -t $IMAGE_NAME-postgres ../$IMAGE_NAME/ --label=$IMAGE_NAME-postgres-image
  else
  podman build -t $IMAGE_NAME ../$IMAGE_NAME/ --label=$IMAGE_NAME-image
  fi

}

get_built_image_from_docker_hub(){
  echo "Getting image for $1"
  IMAGE_NAME=$1
  REPO_NAME=${IMAGE_NAME^^}
  IMAGE_TO_PULL=${REPO_NAME}_IMAGE
  podman pull ${!IMAGE_TO_PULL}
}

for IMAGE_NAME in "${IMAGES_FROM_DOCKER_HUB[@]}"
do
  get_built_image_from_docker_hub $IMAGE_NAME
done

for IMAGE_NAME in "${IMAGES_TO_BE_BUILD[@]}"
do
  build_image_from_source_code $IMAGE_NAME
done
