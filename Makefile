.PHONY: test

test:
	docker build -f Dockerfile.test -t pocketflow-test .
	docker run --rm pocketflow-test
