start-services:
	cd build/dev/; docker-compose up -d

stop-services:
	cd build/dev/; docker-compose stop

wait:
	sleep 5

start-worker:
	./build/rancher/worker.sh

start: start-services wait start-worker

stop-worker:
	ps uxww | grep 'celery -A portal'| grep -v grep | awk '{print $$2}' | xargs kill

stop: stop-worker stop-services
	
build-app:
	docker build -f build/tests/Dockerfile -t ifpb/portal:dev .
	docker tag ifpb/portal:dev docker.ifpb.edu.br:5000/ifpb/portal:dev

build-worker:
	docker build -f build/tests/Dockerfile.worker -t ifpb/portal_worker:dev .
	docker tag ifpb/portal_worker:dev docker.ifpb.edu.br:5000/ifpb/portal_worker:dev

push-app:
	docker push docker.ifpb.edu.br:5000/ifpb/portal:dev

push-worker:
	docker push docker.ifpb.edu.br:5000/ifpb/portal_worker:dev

build-push-app: build-app
	docker push docker.ifpb.edu.br:5000/ifpb/portal:dev

build-push-worker: build-worker
	docker push docker.ifpb.edu.br:5000/ifpb/portal_worker:dev
