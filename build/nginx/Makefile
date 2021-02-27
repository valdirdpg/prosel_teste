image: check-env
	docker build -t ifpb/nginx:${NGINX_VERSION} .
	docker tag ifpb/nginx:${NGINX_VERSION} docker.ifpb.edu.br:5000/ifpb/nginx:${NGINX_VERSION}
	docker push docker.ifpb.edu.br:5000/ifpb/nginx:${NGINX_VERSION}

check-env:
ifndef NGINX_VERSION
    	$(error NGINX_VERSION is undefined)
endif
